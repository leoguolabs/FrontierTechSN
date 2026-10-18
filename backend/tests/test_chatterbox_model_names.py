"""Recovery of false initialisms inside source-bound numeric CamelCase names."""

import hashlib
import json
from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from backend.pipeline import av_sync, chatterbox, chatterbox_phonemes, tts
from backend.pipeline.tts_model_names import model_name_spoken, repair_edits
from backend.tests.test_chatterbox import setup_client, advisory_report  # noqa: F401
from scripts.chatterbox_phoneme_evidence import reference_parts


SOURCE = 'The AI team reports on EgoWild2Dex.'
EDITS = [{'start': 4, 'end': 6, 'source': 'AI', 'spoken': 'eigh eye'},
         {'start': SOURCE.index('Dex'), 'end': SOURCE.index('Dex') + 1,
          'source': 'D', 'spoken': 'dee'}]


def test_model_name_repair_preserves_source_and_other_initialisms():
    before = deepcopy(EDITS)
    fixed = repair_edits(SOURCE, EDITS)
    assert EDITS == before
    assert fixed[0] == EDITS[0]
    assert fixed[1]['source'] == 'EgoWild2Dex'
    assert fixed[1]['spoken'] == 'Ego Wild two Dex'
    assert chatterbox._render_provider_span(SOURCE, 0, len(SOURCE), fixed) == (
        'The eigh eye team reports on Ego Wild two Dex.')
    assert reference_parts(SOURCE, fixed)
    changed = deepcopy(fixed)
    changed[1]['spoken'] = 'Ego Wild three Dex'
    with pytest.raises(ValueError, match='exact source'):
        reference_parts(SOURCE, changed)


@pytest.mark.parametrize('name', ['GPT4', 'OpenAI2', 'EgoWild2D', 'EgoWild2Qzx',
                                 'EgoWildDex', 'EgoWild2-Dex', 'EgoWild20000000Dex'])
def test_unknown_or_initialism_model_names_cannot_get_dictionary_repair(name):
    with pytest.raises(ValueError):
        model_name_spoken(name)


@pytest.mark.parametrize('observed', ['Ego Wild three Dex', 'Ego Wild Dex',
                                    'Ego Wild two D X', 'Ego Wild two Dex two'])
def test_model_name_guard_rejects_wrong_digits_letters_and_repetitions(observed):
    report = chatterbox._pronunciation_report(
        SOURCE, [{'text': SOURCE.replace('EgoWild2Dex', observed)}], repair_edits(SOURCE, EDITS))
    assert not report['passed'] or not chatterbox._trailing_speech_report(
        SOURCE, [{'text': SOURCE.replace('EgoWild2Dex', observed)}])['passed']


@pytest.mark.asyncio
@pytest.mark.parametrize('outcome', ['pass', 'phones_reject', 'unavailable', 'independent_reject'])
async def test_model_repair_preserves_jobs_and_requires_both_audits(setup_client, monkeypatch, outcome):
    server, script, directory, verifier, generate = setup_client
    script.write_text(SOURCE)
    server.pronunciation_ai.side_effect = lambda *a, **kw: json.dumps({'decisions': [
        {'id': i, 'source': edit['source'], 'action': 'spell', 'spoken': edit['spoken'],
         'reason': 'Original contextual decision.'} for i, edit in enumerate(EDITS)]})
    verifier.side_effect = tts.TtsIntegrityError('Chatterbox initialism pronunciation mismatch: wrong name')
    with pytest.raises(tts.TtsIntegrityError):
        await generate()
    original_requests = {p: p.read_bytes() for p in directory.glob('*.request-*.json')}
    assert len(original_requests) == 3
    original_plan = (directory / 'tts_pronunciation.json').read_bytes()
    verifier.side_effect = lambda *a, **kw: advisory_report()
    monkeypatch.setattr(av_sync, 'ensure_word_transcript', AsyncMock(return_value=(
        [{'text': SOURCE.replace('EgoWild2Dex', 'Ego Wild two Dex')}], {'passed': True})))

    async def confirm(path, text, edits, target):
        if outcome == 'unavailable':
            return {'supported': False, 'passed': False}
        return {'supported': True, 'passed': outcome != 'phones_reject',
                'method': 'complete_source_phone_sequence', 'conditioned_on_reference_text': False,
                'audio_sha256': tts._file_sha256(path),
                'source_sha256': hashlib.sha256(text.encode()).hexdigest()}

    monkeypatch.setattr(chatterbox_phonemes, 'confirm', confirm)
    if outcome == 'independent_reject':
        server.independent_audit.side_effect = tts.TtsIntegrityError('independent extra speech')
    if outcome == 'pass':
        await generate()
        await generate()
        assert len(server.jobs) == 4
        metadata = json.loads((directory / 'tts_input_part_001_generated.json').read_text())
        assert metadata['identity']['text'] == SOURCE
        assert metadata['synthesis_request']['text'] == 'The eigh eye team reports on Ego Wild two Dex.'
        assert metadata['integrity']['pronunciation']['required_model_phone_confirmation']['passed']
        assert metadata['integrity']['independent_audit']['passed']
        metadata['integrity']['pronunciation'].pop('required_model_phone_confirmation')
        (directory / 'tts_input_part_001_generated.json').write_text(json.dumps(metadata))
        assert chatterbox._cached_part(directory / 'tts_input_part_001_generated.wav',
                                       metadata['identity'], verify_text=True) is None
    elif outcome == 'unavailable':
        for _ in range(2):
            with pytest.raises(RuntimeError, match='acoustic verification unavailable'):
                await generate()
        assert len(server.jobs) == 4
    else:
        with pytest.raises(tts.TtsIntegrityError):
            await generate()
        with pytest.raises(tts.TtsIntegrityError, match='exhausted'):
            await generate()
        assert len(server.jobs) == 6
    assert script.read_text() == SOURCE
    assert (directory / 'tts_pronunciation.json').read_bytes() == original_plan
    for path, contents in original_requests.items():
        assert path.read_bytes() == contents


@pytest.mark.parametrize('defect', ['pending', 'foreign_identity', 'changed_checkpoint',
                                 'accepted_audio', 'changed_marker'])
def test_repair_never_replaces_live_or_unowned_requests(tmp_path, defect):
    identity = {'text': SOURCE, 'synthesis_text': 'The eigh eye team reports on EgoWild2 deeex.',
                'language': 'en', 'voice': 'jane', 'seed': 42,
                'synthesis_parameters': dict(chatterbox.SYNTHESIS_PARAMETERS)}
    for attempt in range(3):
        payload = {'text': identity['synthesis_text'], 'language_id': 'en', 'voice': 'jane',
                   'seed': 42 + attempt, **identity['synthesis_parameters']}
        checkpoint = {'identity': chatterbox._digest({'identity': identity, 'payload': payload}),
                      'job_id': str(attempt), 'idempotency_key': str(attempt),
                      'rejected': 'Chatterbox initialism pronunciation mismatch: name'}
        if attempt == 0 and defect == 'pending':
            checkpoint.pop('rejected')
        if attempt == 0 and defect == 'foreign_identity':
            checkpoint['identity'] = 'foreign'
        (tmp_path / f'part.request-{attempt}.json').write_text(json.dumps(checkpoint))
    if defect in {'pending', 'foreign_identity'}:
        assert chatterbox._model_name_repair(tmp_path, 'part', identity, EDITS, audio_stem='part') == (
            identity, 'part', EDITS)
        assert not (tmp_path / 'part.model-name-repair.json').exists()
        return
    if defect == 'accepted_audio':
        (tmp_path / 'part_generated.wav').write_bytes(b'accepted')
    else:
        chatterbox._model_name_repair(tmp_path, 'part', identity, EDITS, audio_stem='part')
        target = tmp_path / ('part.request-0.json' if defect == 'changed_checkpoint'
                             else 'part.model-name-repair.json')
        target.write_text('{}')
    with pytest.raises(RuntimeError):
        chatterbox._model_name_repair(tmp_path, 'part', identity, EDITS, audio_stem='part')


@pytest.mark.parametrize('hint', [
    {'spoken': 'Eagle', 'phones': ['IY', 'G', 'AH', 'L']},
    {'spoken': 'E-go', 'phones': ['IY', 'G', 'AH', 'L']},
    {'spoken': 'E-go go', 'phones': ['IY', 'G', 'OW']},
])
def test_model_articulation_cannot_change_source_phones(hint):
    with pytest.raises(ValueError):
        model_name_spoken('EgoWild2Dex', {'Ego': hint})


@pytest.mark.asyncio
@pytest.mark.parametrize('outcome', ['pass', 'reject', 'unavailable'])
async def test_explicit_model_articulation_keeps_both_prior_budgets(setup_client, monkeypatch, outcome):
    server, script, directory, verifier, generate = setup_client
    script.write_text(SOURCE)
    server.pronunciation_ai.side_effect = lambda *a, **kw: json.dumps({'decisions': [
        {'id': i, 'source': edit['source'], 'action': 'spell', 'spoken': edit['spoken'],
         'reason': 'Original contextual decision.'} for i, edit in enumerate(EDITS)]})
    verifier.side_effect = tts.TtsIntegrityError('Chatterbox initialism pronunciation mismatch: name')
    with pytest.raises(tts.TtsIntegrityError):
        await generate()
    verifier.side_effect = tts.TtsIntegrityError('Model-identifier audio differs from its complete source phone sequence')
    with pytest.raises(tts.TtsIntegrityError):
        await generate()
    assert len(server.jobs) == 6
    originals = {p: p.read_bytes() for p in directory.glob('*.request-*.json')}
    stem = 'tts_input_part_001.model-name-repair'
    first = json.loads((directory / f'{stem}.json').read_text())
    marker = directory / f'{stem}.model-name-articulation-input.json'
    hints = {'EgoWild2Dex': {'Ego': {'spoken': 'E-go', 'phones': ['IY', 'G', 'OW']}}}
    marker.write_text(json.dumps({'version': 1, 'source_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
                                 'synthesis_sha256': hashlib.sha256(first['synthesis_text'].encode()).hexdigest(),
                                 'hints': hints}))
    monkeypatch.setattr(av_sync, 'ensure_word_transcript', AsyncMock(return_value=(
        [{'text': SOURCE.replace('EgoWild2Dex', 'Ego Wild two Dex')}], {'passed': True})))
    verifier.side_effect = lambda *a, **kw: advisory_report()

    async def confirm(path, text, edits, target):
        assert reference_parts(text, edits)
        return {'supported': outcome != 'unavailable', 'passed': outcome == 'pass',
                'method': 'complete_source_phone_sequence', 'conditioned_on_reference_text': False,
                'audio_sha256': tts._file_sha256(path),
                'source_sha256': hashlib.sha256(text.encode()).hexdigest()}

    monkeypatch.setattr(chatterbox_phonemes, 'confirm', confirm)
    if outcome == 'pass':
        await generate()
        await generate()
        assert len(server.jobs) == 7
        metadata = json.loads((directory / 'tts_input_part_001_generated.json').read_text())
        assert metadata['identity']['text'] == SOURCE
        assert metadata['synthesis_request']['text'] == 'The eigh eye team reports on E-go Wild two Dex.'
        assert metadata['integrity']['pronunciation']['required_model_phone_confirmation']['passed']
        assert metadata['integrity']['independent_audit']['passed']
        marker.write_text('{}')
        with pytest.raises(RuntimeError, match='unchanged first repair'):
            await generate()
    elif outcome == 'unavailable':
        for _ in range(2):
            with pytest.raises(RuntimeError, match='acoustic verification unavailable'):
                await generate()
        assert len(server.jobs) == 7
    else:
        for _ in range(2):
            with pytest.raises(tts.TtsIntegrityError):
                await generate()
        assert len(server.jobs) == 9
    for path, contents in originals.items():
        assert path.read_bytes() == contents


@pytest.mark.asyncio
async def test_acoustic_reference_fix_reaudits_same_completed_model_job(setup_client, monkeypatch):
    from scripts import chatterbox_phoneme_evidence as evidence
    server, script, directory, verifier, generate = setup_client
    script.write_text(SOURCE)
    server.pronunciation_ai.side_effect = lambda *a, **kw: json.dumps({'decisions': [
        {'id': i, 'source': edit['source'], 'action': 'spell', 'spoken': edit['spoken'],
         'reason': 'Original contextual decision.'} for i, edit in enumerate(EDITS)]})
    monkeypatch.setattr(evidence, 'EVIDENCE_VERSION', 31)
    verifier.side_effect = tts.TtsIntegrityError('Chatterbox initialism pronunciation mismatch: name')
    with pytest.raises(tts.TtsIntegrityError):
        await generate()
    original_requests = {p: p.read_bytes() for p in directory.glob('*.request-*.json')}
    verifier.side_effect = tts.TtsIntegrityError('Model-identifier audio differs from its complete source phone sequence')
    with pytest.raises(tts.TtsIntegrityError):
        await generate()
    assert len(server.jobs) == 6
    verifier.side_effect = lambda *a, **kw: advisory_report()
    monkeypatch.setattr(evidence, 'EVIDENCE_VERSION', 32)
    monkeypatch.setattr(av_sync, 'ensure_word_transcript', AsyncMock(return_value=(
        [{'text': SOURCE}], {'passed': True})))

    async def confirm(path, text, edits, target):
        return {'supported': True, 'passed': True, 'method': 'complete_source_phone_sequence',
                'conditioned_on_reference_text': False, 'audio_sha256': tts._file_sha256(path),
                'source_sha256': hashlib.sha256(text.encode()).hexdigest()}

    monkeypatch.setattr(chatterbox_phonemes, 'confirm', confirm)
    await generate()
    assert len(server.jobs) == 6
    for path, contents in original_requests.items():
        assert path.read_bytes() == contents
