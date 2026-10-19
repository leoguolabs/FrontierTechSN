"""Numeric recovery keeps source, accepted media, and exhausted job identities."""

import hashlib
import json
from unittest.mock import AsyncMock

import pytest

from backend.pipeline import av_sync, chatterbox as cb, tts, tts_pronunciation as pronunciation
from backend.pipeline.chatterbox_numeric_repair import repair_layout
from backend.tests.test_chatterbox import setup_client, advisory_report  # noqa: F401


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.mark.parametrize('observed', ['V4 .1', 'V 4 .1', 'V four point one'])
def test_explicit_decimal_observation_keeps_the_point(observed):
    source = 'The model V4.1 works.'
    words = [{'text': word} for word in f'The model {observed} works.'.split()]
    report = cb._pronunciation_report(source, words)
    assert report['passed']
    assert 'v4.1' in report['normalized_transcript']
    assert report['transcript'] == ' '.join(word['text'] for word in words)


@pytest.mark.parametrize('observed', ['V4 1', 'V4 .2', 'V41', 'V4 .01', 'V4 .1 .1',
                                     'V4 .1 V4 .1', 'V4 .1.2'])
def test_decimal_repair_rejects_changed_missing_or_repeated_digits(observed):
    assert not cb._pronunciation_report('The model V4.1 works.',
                                       [{'text': f'The model {observed} works.'}])['passed']


def test_numeric_edit_protects_the_entire_snapshot_suffix():
    source = 'Model V4.1-Flash-1017 works.'
    start = source.index('1017')
    edits = [*pronunciation.candidates(source),
             {'start': start, 'end': start + 4, 'source': '1017', 'kind': 'number',
              'spoken': 'one thousand seventeen'}]
    for observed in ['117', '717', 'one seventeen', 'one thousand seventy', '1017 1017']:
        assert not cb._pronunciation_report(source, [{'text': source.replace('1017', observed)}], edits)['passed']
    assert cb._pronunciation_report(source, [{'text': source.replace('1017', 'one thousand seventeen')}], edits)['passed']


@pytest.fixture
def failed_numeric_chunk(tmp_path):
    source = ('The technology outlet reports that DeepSeek has released a new model, '
              'DeepSeek-V4.1-Flash-1017 with a snapshot suffix matching the date.')
    edits = [{**edit, 'spoken': 'vee'} for edit in pronunciation.candidates(source)]
    synthesis = cb._render_provider_span(source, 0, len(source), edits)
    base = {'language': 'en', 'voice': 'jane', 'seed': 42,
            'synthesis_parameters': dict(cb.SYNTHESIS_PARAMETERS)}
    stem = 'tts_input_part_002'
    identity = {**base, 'text': source, 'synthesis_text': synthesis}
    paths = []
    for attempt in range(3):
        payload = {'text': synthesis, 'language_id': 'en', 'voice': 'jane', 'seed': 42 + attempt,
                   **base['synthesis_parameters']}
        path = tmp_path / f'{stem}.request-{attempt}.json'
        path.write_text(json.dumps({'identity': cb._digest({'identity': identity, 'payload': payload}),
                                   'idempotency_key': str(attempt), 'job_id': str(attempt),
                                   'rejected': 'Chatterbox initialism pronunciation mismatch: numeric'}))
        paths.append(path)
    numbers = [{'start': source.index(number), 'end': source.index(number) + len(number)}
               for number in ['4.1', '1017']]
    marker = tmp_path / f'{stem}.numeric-repair.json'
    marker.write_text(json.dumps({'version': 1, 'source_sha256': sha(source),
                                 'synthesis_sha256': sha(synthesis), 'reason': 'Observed wrong number',
                                 'numbers': numbers,
                                 'original_request_sha256': [tts._file_sha256(path) for path in paths]}))
    return source, edits, base, stem, marker, paths


def test_numeric_layout_splits_only_failed_chunk_and_preserves_frozen_assets(tmp_path, failed_numeric_chunk):
    source, edits, base, stem, marker, paths = failed_numeric_chunk
    before = {path: path.read_bytes() for path in [marker, *paths]}
    prefix, suffix = 'An accepted sentence.', 'The next untouched sentence.'
    normalized = f'{prefix} {source} {suffix}'
    offset = len(prefix) + 1
    edits = [{**edit, 'start': edit['start'] + offset, 'end': edit['end'] + offset} for edit in edits]
    accepted = tmp_path / 'tts_input_part_001_generated.wav'
    accepted.write_bytes(b'immutable')
    args = (tmp_path, normalized, [prefix, source, suffix],
            ['tts_input_part_001', stem, 'tts_input_part_003'], edits, base)
    result = repair_layout(*args, max_words=20, max_chars=250)
    chunks, names, revised, bindings = result
    assert ' '.join(chunks) == normalized
    assert names[0] == 'tts_input_part_001' and names[-1] == 'tts_input_part_003'
    assert len(bindings) >= 2
    cursor = 0
    for chunk in chunks:
        start = normalized.index(chunk, cursor)
        cursor = start + len(chunk)
        rendered = cb._render_provider_span(normalized, start, cursor, revised)
        assert cb._synthesis_word_count(rendered) <= 20 and len(rendered) <= 250
    assert 'one thousand seventeen' in cb._render_provider_span(normalized, 0, len(normalized), revised)
    (tmp_path / f'{names[1]}.request-0.json').write_text('{}')
    assert repair_layout(*args, max_words=20, max_chars=250) == result
    assert accepted.read_bytes() == b'immutable'
    assert all(path.read_bytes() == contents for path, contents in before.items())


@pytest.mark.parametrize('rejection', [
    'Word-hint audio differs from its complete source phone sequence',
    'Required complete-source phone sequence differs from the source',
])
def test_numeric_recovery_accepts_exhausted_complete_source_rejections(
        tmp_path, failed_numeric_chunk, rejection):
    source, edits, base, stem, marker, paths = failed_numeric_chunk
    for path in paths:
        request = json.loads(path.read_text())
        request['rejected'] = rejection
        path.write_text(json.dumps(request))
    repair = json.loads(marker.read_text())
    repair['original_request_sha256'] = [tts._file_sha256(path) for path in paths]
    marker.write_text(json.dumps(repair))
    original = {path: path.read_bytes() for path in paths}
    chunks, names, revised, bindings = repair_layout(
        tmp_path, source, [source], [stem], edits, base, max_words=20, max_chars=250)
    assert ' '.join(chunks) == source
    assert len(bindings) >= 2
    assert all(name.startswith(f'{stem}.numeric-v1-') for name in names)
    assert 'one thousand seventeen' in cb._render_provider_span(source, 0, len(source), revised)
    assert all(path.read_bytes() == contents for path, contents in original.items())


@pytest.mark.parametrize('defect', ['pending', 'identity', 'changed_request', 'accepted',
                                   'truncated_number', 'overlap', 'wrong_source', 'changed_marker',
                                   'unavailable', 'unrelated_failure'])
def test_numeric_recovery_rejects_unowned_or_changed_inputs(tmp_path, failed_numeric_chunk, defect):
    source, edits, base, stem, marker, paths = failed_numeric_chunk
    repair = json.loads(marker.read_text())
    if defect in {'pending', 'identity', 'changed_request', 'unavailable', 'unrelated_failure'}:
        record = json.loads(paths[0].read_text())
        if defect == 'pending':
            record.pop('rejected')
        elif defect == 'unavailable':
            record['rejected'] = 'Required word-hint acoustic verification unavailable'
        elif defect == 'unrelated_failure':
            record['rejected'] = 'Pocket TTS produced an internal silence'
        else:
            record['identity'] = 'foreign'
        paths[0].write_text(json.dumps(record))
        if defect != 'changed_request':
            repair['original_request_sha256'] = [tts._file_sha256(path) for path in paths]
    elif defect == 'accepted':
        (tmp_path / f'{stem}_generated.wav').write_bytes(b'accepted')
    elif defect == 'truncated_number':
        repair['numbers'][1]['start'] += 1
    elif defect == 'overlap':
        repair['numbers'].append(repair['numbers'][0])
    elif defect == 'wrong_source':
        repair['source_sha256'] = 'foreign'
    else:
        repair_layout(tmp_path, source, [source], [stem], edits, base, max_words=30, max_chars=250)
        repair['reason'] = 'changed after activation'
    marker.write_text(json.dumps(repair))
    with pytest.raises(RuntimeError):
        repair_layout(tmp_path, source, [source], [stem], edits, base, max_words=30, max_chars=250)


@pytest.mark.asyncio
@pytest.mark.parametrize('outcome', ['pass', 'reject', 'unavailable'])
@pytest.mark.parametrize('rejection', [
    'Chatterbox initialism pronunciation mismatch: numeric',
    'Word-hint audio differs from its complete source phone sequence',
    'Required complete-source phone sequence differs from the source',
])
async def test_numeric_recovery_keeps_old_jobs_and_requires_fresh_audits(
        setup_client, monkeypatch, outcome, rejection):
    server, script, directory, verifier, generate = setup_client
    source = 'The model V4.1-Flash-1017 works today.'
    script.write_text(source)
    server.pronunciation_ai.side_effect = lambda *args, **kwargs: json.dumps({'decisions': [
        {'id': 0, 'source': 'V', 'action': 'spell', 'spoken': 'vee', 'reason': 'Model letter'}]})
    verifier.side_effect = tts.TtsIntegrityError(rejection)
    with pytest.raises(tts.TtsIntegrityError):
        await generate()
    plan = (directory / 'tts_pronunciation.json').read_bytes()
    paths = sorted(directory.glob('tts_input_part_001.request-*.json'))
    original = {path: path.read_bytes() for path in paths}
    synthesis = json.loads(plan)['synthesis_text']
    marker = directory / 'tts_input_part_001.numeric-repair.json'
    marker.write_text(json.dumps({'version': 1, 'source_sha256': sha(source),
        'synthesis_sha256': sha(synthesis), 'reason': 'Wrong snapshot number',
        'numbers': [{'start': source.index(n), 'end': source.index(n) + len(n)} for n in ['4.1', '1017']],
        'original_request_sha256': [tts._file_sha256(path) for path in paths]}))
    verifier.side_effect = lambda *args, **kwargs: advisory_report()
    observed = source.replace('V4.1', 'V four point one').replace('1017', 'one thousand seventeen')
    monkeypatch.setattr(av_sync, 'ensure_word_transcript', AsyncMock(return_value=([{'text': observed}], {})))
    if outcome != 'pass':
        error = (tts.TtsIntegrityError('Independent Chatterbox check found unrequested speech: wrong number')
                 if outcome == 'reject' else RuntimeError('Independent decoder unavailable'))
        server.independent_audit.side_effect = error
        for _ in range(2):
            with pytest.raises(type(error)):
                await generate()
        assert len(server.jobs) == (6 if outcome == 'reject' else 4)
        assert all(path.read_bytes() == contents for path, contents in original.items())
        assert (directory / 'tts_pronunciation.json').read_bytes() == plan
        return
    await generate()
    await generate()
    assert len(server.jobs) == 4
    assert server.independent_audit.await_count >= 2
    metadata = json.loads((directory / 'tts_input_part_001.numeric-v1-01_generated.json').read_text())
    assert metadata['identity']['text'] == source
    assert 'four point one' in metadata['synthesis_request']['text']
    assert metadata['integrity']['pronunciation']['passed']
    assert metadata['integrity']['independent_audit']['passed']
    assert (directory / 'tts_pronunciation.json').read_bytes() == plan
    assert all(path.read_bytes() == contents for path, contents in original.items())
