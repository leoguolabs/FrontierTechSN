import json
import hashlib
import subprocess
import wave
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.pipeline import chatterbox_independent as independent, tts, tts_pronunciation


@pytest.fixture
def audit_case(tmp_path, monkeypatch):
    wav = tmp_path / 'original.wav'
    with wave.open(str(wav), 'wb') as writer:
        writer.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        writer.writeframes(b'\0\0' * 48000)
    observed = {'text': 'The report mentions DIY today.', 'start': 0.0, 'end': 1.0}
    calls = []

    def decode(command, **kwargs):
        calls.append((command, kwargs))
        with open(command[5], 'w') as stream:
            json.dump([observed], stream)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(independent.subprocess, 'run', decode)
    source = 'The report mentions DIY today.'
    _, edits = tts_pronunciation.validate_decisions(source, [{
        'id': 0, 'source': 'DIY', 'action': 'spell', 'spoken': 'dee eye Y',
        'reason': 'Source-bound fixture decision.',
    }])
    return wav, source, edits, tmp_path / 'audit', observed, calls


@pytest.mark.asyncio
async def test_independent_cache_binds_audio_source_decisions_and_transcript(audit_case):
    wav, source, edits, directory, observed, calls = audit_case
    first = await independent.audit_part(wav, source, edits, directory)
    assert first['passed'] and first['required']
    assert calls[0][0][7] == independent.MODEL
    assert calls[0][1]['env']['HF_HUB_OFFLINE'] == '1'
    await independent.audit_part(wav, source, edits, directory)
    assert len(calls) == 1
    transcript = next(directory.rglob('transcript.json'))
    transcript.write_text('[{"text":"forged transcript"}]')
    await independent.audit_part(wav, source, edits, directory)
    assert len(calls) == 2
    observed['text'] = source + ' Why today?'
    wav.write_bytes(wav.read_bytes() + b'different waveform identity')
    with pytest.raises(tts.TtsIntegrityError, match='unrequested speech'):
        await independent.audit_part(wav, source, edits, directory)
    assert len(calls) == 3


@pytest.mark.parametrize('observed', [
    'Table 30v2', 'Table30V2', 'Table 30 V 2', 'Table30 v2',
])
@pytest.mark.asyncio
async def test_versioned_name_spacing_requires_the_exact_complete_source(audit_case, observed):
    wav, _source, _edits, directory, observation, _calls = audit_case
    source = 'RoboChallenge Table30 V2 leads today.'
    edits = tts_pronunciation.candidates(source)
    observation['text'] = f'RoboChallenge {observed} leads today.'
    original = wav.read_bytes()
    report = await independent.audit_part(wav, source, edits, directory)
    assert report['passed'] and wav.read_bytes() == original
    if report.get('source_bound_version_spacing'):
        assert report['source_bound_version_spacing']['spans'][0]['numeric_groups'] == ['30', '2']
        assert report['asr_identifier_mismatches']
        assert report['raw_transcript'] == observation['text']


@pytest.mark.parametrize('observed', [
    'RoboChallenge Table 31v2 leads today.',
    'RoboChallenge Table 30v3 leads today.',
    'RoboChallenge Table 030v2 leads today.',
    'RoboChallenge Table 30v02 leads today.',
    'RoboChallenge Table 30v2.1 leads today.',
    'RoboChallenge Table 302 leads today.',
    'RoboChallenge Table 30vv2 leads today.',
    'RoboChallenge Table 30v2 V2 leads today.',
    'RoboChallenge Table 30v2 leads today. Thank you.',
    'Robot Challenge Table 30v2 leads today.',
    'RoboChallenge Table 30v2 leads.',
])
@pytest.mark.asyncio
async def test_version_spacing_never_repairs_changed_words_values_or_extra_speech(audit_case, observed):
    wav, _source, _edits, directory, observation, _calls = audit_case
    source = 'RoboChallenge Table30 V2 leads today.'
    observation['text'] = observed
    with pytest.raises(tts.TtsIntegrityError):
        await independent.audit_part(wav, source, tts_pronunciation.candidates(source), directory)


@pytest.mark.parametrize(('source', 'observed'), [
    ('ALDH3 B2 leads.', 'ALDH3B2 leads.'),
    ('DDR5 B2 leads.', 'DDR5B2 leads.'),
    ('Table3 0 V2 leads.', 'Table30V2 leads.'),
    ('Table30 and V2 leads.', 'Table30V2 leads.'),
    ('Table30 V2.1 leads.', 'Table30V21 leads.'),
    ('The Rapist30 V2 leads.', 'Therapist30V2 leads.'),
])
def test_version_spacing_does_not_merge_unrelated_source_identifiers(source, observed):
    proof = independent._versioned_name_spacing(source, observed)
    assert not proof or not proof['complete_source_match']


@pytest.mark.asyncio
async def test_version_spacing_cannot_hide_waveform_tail(audit_case, monkeypatch):
    from backend.pipeline import tts_tail_guard
    wav, _source, _edits, directory, observed, _calls = audit_case
    source = 'RoboChallenge Table30 V2 leads today.'
    observed['text'] = 'RoboChallenge Table 30v2 leads today.'
    monkeypatch.setattr(tts_tail_guard, 'inspect_tail', lambda *_: {'passed': False})
    with pytest.raises(tts.TtsIntegrityError):
        await independent.audit_part(wav, source, tts_pronunciation.candidates(source), directory)


@pytest.mark.asyncio
@pytest.mark.parametrize('proof_kind', ['matched', 'different', 'unavailable', 'wrong_audio', 'conditioned'])
async def test_model_name_spelling_drift_requires_bound_complete_source_phones(audit_case, monkeypatch, proof_kind):
    from backend.pipeline import chatterbox_phonemes
    wav, _source, _edits, directory, observed, _calls = audit_case
    source = 'The report mentions EgoWild2Dex today.'
    start = source.index('EgoWild2Dex')
    edits = [{'start': start, 'end': start + 11, 'source': 'EgoWild2Dex',
              'spoken': 'Ego Wild two Dex', 'kind': 'model_name'}]
    observed['text'] = 'The report mentions Ego Wild two decks today.'
    proof = {'supported': proof_kind != 'unavailable', 'passed': proof_kind != 'different',
             'audio_sha256': tts._file_sha256(wav), 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
             'method': 'complete_source_phone_sequence', 'conditioned_on_reference_text': False}
    if proof_kind == 'wrong_audio':
        proof['audio_sha256'] = 'other-waveform'
    if proof_kind == 'conditioned':
        proof['conditioned_on_reference_text'] = True
    monkeypatch.setattr(chatterbox_phonemes, 'confirm', AsyncMock(return_value=proof))
    if proof_kind == 'matched':
        report = await independent.audit_part(wav, source, edits, directory)
        assert report['passed']
        assert report['asr_identifier_mismatches'][0]['asr'][-1] == 'decks'
        assert report['identifier_mismatches'] == []
        assert report['model_name_phone_confirmation'] == proof
    else:
        with pytest.raises(tts.TtsIntegrityError if proof_kind == 'different' else RuntimeError):
            await independent.audit_part(wav, source, edits, directory)


@pytest.mark.asyncio
async def test_model_name_confirmation_cannot_hide_extra_closing_speech(audit_case, monkeypatch):
    from backend.pipeline import chatterbox_phonemes
    wav, _source, _edits, directory, observed, _calls = audit_case
    source = 'The report mentions EgoWild2Dex today.'
    start = source.index('EgoWild2Dex')
    edits = [{'start': start, 'end': start + 11, 'source': 'EgoWild2Dex',
              'spoken': 'Ego Wild two Dex', 'kind': 'model_name'}]
    observed['text'] = 'The report mentions Ego Wild two decks today. Thank you.'
    confirm = AsyncMock(side_effect=AssertionError('Positive tail errors must stay rejected'))
    monkeypatch.setattr(chatterbox_phonemes, 'confirm', confirm)
    with pytest.raises(tts.TtsIntegrityError):
        await independent.audit_part(wav, source, edits, directory)
    confirm.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('observation', [
    'The report mentions DIY today. Why today?',
    'The report mentions D I Y today. Why today?',
])
async def test_independent_tail_rejects_the_primary_decoders_missed_diy_echo(audit_case, observation):
    wav, source, edits, directory, observed, _calls = audit_case
    original = wav.read_bytes()
    observed['text'] = observation
    with pytest.raises(tts.TtsIntegrityError, match='unrequested speech'):
        await independent.audit_part(wav, source, edits, directory)
    assert wav.read_bytes() == original
    report = json.loads(next(directory.rglob('audit.json')).read_text())
    assert not report['passed']
    assert not report['tail']['passed'] or not report['normalized_tail']['passed']


@pytest.mark.parametrize('text,overlap,rejected', [
    ('To deal news. Bloomberg reports.', False, True),
    ('To deal news. Bloomberg reports.', True, False),
    ('To deal news. To deal news. Bloomberg reports.', False, False),
])
def test_interior_ordinary_phrase_repeats_need_distinct_acoustic_spans(text, overlap, rejected):
    words = [{'text': word, 'start': i * .2, 'end': (i + 1) * .2}
             for i, word in enumerate('To deal news To deal news Bloomberg reports'.split())]
    if overlap:
        for i in range(3):
            words[i + 3].update(start=words[i]['start'], end=words[i]['end'])
    assert bool(independent._repeated_source_phrases(text, words)) is rejected


@pytest.mark.asyncio
@pytest.mark.parametrize(('source', 'observation', 'accepted'), [
    ('AI plans to ship.', 'AI AI plans to ship.', False),
    ('AI reports on AI.', 'AI reports on AI.', True),
    ('GPT-6 is available.', 'GPT6 is available.', True),
    ('GPT-6 is available.', 'GPT7 is available.', False),
    ('GPT-6 is available.', 'GPT seven is available.', False),
    ('GPT-6 is available.', 'GPT six is available.', True),
    ('GPT-4 is available.', 'GPT for is available.', True),
    ('GPT-4 is available.', 'GPT five is available.', False),
    ('GPT-4 is available.', 'GPT for for is available.', False),
    ('GPT-4 is available.', 'GPT for is available. GPT for.', False),
    ('The GPUs work.', 'The GP use work.', True),
])
async def test_independent_check_distinguishes_repetition_and_model_change_from_formatting(
        audit_case, source, observation, accepted):
    wav, _source, _edits, directory, observed, _calls = audit_case
    edits = tts_pronunciation.candidates(source)
    observed['text'] = observation
    if accepted:
        assert (await independent.audit_part(wav, source, edits, directory))['passed']
    else:
        with pytest.raises(tts.TtsIntegrityError):
            await independent.audit_part(wav, source, edits, directory)


@pytest.mark.asyncio
async def test_decoder_unavailability_preserves_the_original_wave_and_never_passes(audit_case, monkeypatch):
    wav, source, edits, directory, _observed, _calls = audit_case
    original = wav.read_bytes()
    attempts = []
    def timeout(*args, **kwargs):
        attempts.append(kwargs['timeout'])
        raise subprocess.TimeoutExpired('independent recognizer', kwargs['timeout'])
    monkeypatch.setattr(independent.subprocess, 'run', timeout)
    with pytest.raises(RuntimeError, match='preserving the completed job'):
        await independent.audit_part(wav, source, edits, directory)
    assert wav.read_bytes() == original and not list(directory.rglob('audit.json'))
    assert attempts == [180, 360]
    assert len(list(directory.rglob('decoder-failure-*.json'))) == 2


@pytest.mark.asyncio
async def test_decoder_timeout_retries_same_wave_and_rejects_stale_output(audit_case, monkeypatch):
    wav, source, edits, directory, _observed, calls = audit_case
    original = wav.read_bytes()
    decode = independent.subprocess.run
    attempts = []

    def slow_once(command, **kwargs):
        from pathlib import Path
        transcript = Path(command[5])
        attempts.append(kwargs['timeout'])
        if len(attempts) == 1:
            transcript.write_text('[{"text": "unfinished output"}]')
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], stderr=b'model loading')
        assert not transcript.exists()
        return decode(command, **kwargs)

    monkeypatch.setattr(independent.subprocess, 'run', slow_once)
    assert (await independent.audit_part(wav, source, edits, directory))['passed']
    assert attempts == [180, 360] and len(calls) == 1
    assert wav.read_bytes() == original
    diagnostic = json.loads(next(directory.rglob('decoder-failure-*.json')).read_text())
    assert diagnostic['stderr'] == 'model loading'


@pytest.mark.asyncio
async def test_decoder_nonzero_exit_does_not_retry_or_accept_output(audit_case, monkeypatch):
    wav, source, edits, directory, _observed, calls = audit_case
    decode = independent.subprocess.run

    def fail(command, **kwargs):
        decode(command, **kwargs)
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(independent.subprocess, 'run', fail)
    with pytest.raises(RuntimeError, match='preserving the completed job'):
        await independent.audit_part(wav, source, edits, directory)
    assert len(calls) == 1
    assert not list(directory.rglob('identity.json'))
    assert not list(directory.rglob('audit.json'))


@pytest.mark.asyncio
async def test_ordinary_sentences_require_independent_observations_too(audit_case):
    wav, _source, _edits, directory, observed, calls = audit_case
    observed['text'] = 'An ordinary sentence.'
    report = await independent.audit_part(wav, 'An ordinary sentence.', [], directory)
    assert report['passed'] and report['required'] and len(calls) == 1
    assert report['waveform_tail']['passed']


@pytest.mark.asyncio
async def test_empty_observation_can_recover_without_changing_the_wave(audit_case, monkeypatch):
    wav, source, edits, directory, _observed, calls = audit_case
    def decode(command, **kwargs):
        calls.append(command)
        with open(command[5], 'w') as stream:
            json.dump([] if len(calls) == 1 else [{'text': source, 'start': 0.0, 'end': 1.0}], stream)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(independent.subprocess, 'run', decode)
    original = wav.read_bytes()
    with pytest.raises(RuntimeError, match='preserving the completed job'):
        await independent.audit_part(wav, source, edits, directory)
    assert (await independent.audit_part(wav, source, edits, directory))['passed']
    assert len(calls) == 2 and wav.read_bytes() == original


@pytest.mark.asyncio
@pytest.mark.parametrize('source,transcript', [
    ('To deal news.', 'to DealNews.'),
    ('The release simply erased.', 'The release simply erased.'),
])
async def test_transcript_match_or_spelling_drift_cannot_hide_untranscribed_tail(
        audit_case, source, transcript):
    wav, _source, _edits, directory, observed, _calls = audit_case
    observed.update(text=transcript, end=.8)
    with wave.open(str(wav), 'wb') as writer:
        writer.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        writer.writeframes((3000).to_bytes(2, 'little') * 21600
                           + b'\0\0' * 16800
                           + (4000).to_bytes(2, 'little') * 9600)
    original = wav.read_bytes()
    with pytest.raises(tts.TtsIntegrityError, match='waveform_tail'):
        await independent.audit_part(wav, source, [], directory)
    report = json.loads(next(directory.rglob('audit.json')).read_text())
    assert report['tail']['passed'] and not report['waveform_tail']['passed']
    assert wav.read_bytes() == original


@pytest.mark.asyncio
@pytest.mark.parametrize('defect', [None, 'extra', 'omitted', 'weak_primary', 'disabled', 'derivative_extra'])
async def test_delivery_tail_requires_two_complete_transcripts_and_derivative_audit(audit_case, defect):
    import hashlib
    from backend.pipeline import chatterbox_tail

    wav, _source, _edits, directory, observed, calls = audit_case
    source = 'The release simply erased.'
    observed.update(text=source, end=.8)
    if defect == 'extra':
        observed['text'] += ' And.'
    if defect == 'omitted':
        observed['text'] = 'The release erased.'
    with wave.open(str(wav), 'wb') as writer:
        writer.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        writer.writeframes((3000).to_bytes(2, 'little') * 21600
                           + b'\0\0' * 16800 + (4000).to_bytes(2, 'little') * 9600)
    original = wav.read_bytes()
    integrity = {
        'accepted': True, 'expected_words': 4, 'transcript_words': 4,
        'matched_exact_words': 4, 'exact_asr_word_coverage': 1.,
        'transcript_word_ratio': 1., 'leading_anchor': True, 'trailing_anchor': True,
        'exact_leading_anchor': True, 'exact_trailing_anchor': True,
        'repeat_start_seconds': None, 'token_differences': [],
        'speech_end_seconds': .9, 'transcription': {'passed': True},
    }
    if defect == 'weak_primary':
        integrity['exact_asr_word_coverage'] = .7
    async def audit(path, text, edits):
        if path != wav and defect == 'derivative_extra':
            observed['text'] = source + ' And.'
        return await independent.audit_part(path, text, edits, directory)

    async def run():
        return await chatterbox_tail.audit_delivery_tail(
            wav, source, [], integrity, audit, directory, enabled=defect != 'disabled')

    if defect:
        with pytest.raises(tts.TtsIntegrityError):
            await run()
        assert 'independent_tail_recovery' not in integrity
    else:
        report = await run()
        assert report['passed'] and len(calls) == 2
        assert integrity['independent_tail_recovery']['speech_end_seconds'] == .9
        metadata = {'audio_sha256': hashlib.sha256(original).hexdigest(),
                    'integrity': integrity, 'identity': {'text': source}}
        output, rows = chatterbox_tail.prepare_delivery_parts([wav], [metadata])
        assert rows[0]['audio_sha256'] == report['identity']['audio_sha256']
        assert output[0] != wav and (await audit(output[0], source, []))['passed']
        integrity['independent_tail_recovery']['cleanup']['output_audio_sha256'] = 'changed'
        with pytest.raises(RuntimeError, match='independently audited tail'):
            chatterbox_tail.prepare_delivery_parts([wav], [metadata])
    assert wav.read_bytes() == original
    assert not list(directory.glob('independent-tail-verification.wav'))
