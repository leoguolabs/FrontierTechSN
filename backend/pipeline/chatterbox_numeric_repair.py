"""Bounded, explicit numeric articulation after exhausted Chatterbox jobs."""

import hashlib
import re
from pathlib import Path


def repair_layout(directory: Path, normalized: str, chunks: list[str], stems: list[str],
                  edits: list[dict], identity_base: dict, *, max_words: int,
                  max_chars: int) -> tuple[list[str], list[str], list[dict], dict[str, str]]:
    """Keep source and accepted stems; split only a bound, failed numeric chunk.

    A marker binds all exhausted requests and selects exact source numerals.
    Their deterministic spoken forms get new stems and the usual finite retry
    budget. The original plan, requests, and failed waveforms stay immutable.
    """
    from backend.pipeline import chatterbox as cb, tts, tts_pronunciation as pronunciation

    result, names, revised, bindings = [], [], list(edits), {}
    offset = 0
    for source, stem in zip(chunks, stems, strict=True):
        start = normalized.index(source, offset)
        offset = start + len(source)
        marker = directory / f'{stem}.numeric-repair.json'
        if not marker.exists():
            result.append(source)
            names.append(stem)
            continue
        repair = cb._read_json(marker)
        synthesis = cb._render_provider_span(normalized, start, offset, edits)
        if (repair.get('version') != 1
                or repair.get('source_sha256') != hashlib.sha256(source.encode()).hexdigest()
                or repair.get('synthesis_sha256') != hashlib.sha256(synthesis.encode()).hexdigest()
                or not isinstance(repair.get('reason'), str) or not repair['reason'].strip()
                or (directory / f'{stem}_generated.wav').exists()):
            raise RuntimeError('Numeric repair requires an unchanged unaccepted source chunk')
        local = [{**edit, 'start': edit['start'] - start, 'end': edit['end'] - start}
                 for edit in edits if start <= edit['start'] and edit['end'] <= offset]
        identity = {**identity_base, 'text': source, 'synthesis_text': synthesis}
        refs = [pronunciation.word_hint_reference(edit) for edit in local if edit.get('kind') == 'word']
        if refs:
            identity['word_hint_references'] = refs
        requests = [directory / f'{stem}.request-{attempt}.json'
                    for attempt in range(cb.MAX_INTEGRITY_ATTEMPTS)]
        other_requests = [path for path in directory.glob(f'{stem}.*request-*.json')
                          if not path.name.startswith(f'{stem}.numeric-v1-')]
        if (not all(path.is_file() for path in requests)
                or repair.get('original_request_sha256') != [tts._file_sha256(path) for path in requests]
                or sorted(other_requests) != requests):
            raise RuntimeError('Numeric repair requires unchanged original requests only')
        for attempt, path in enumerate(requests):
            request = cb._read_request_checkpoint(path)
            payload = {'text': synthesis, 'language_id': identity['language'], 'voice': identity['voice'],
                       'seed': (identity['seed'] + attempt) % (2 ** 32), **identity['synthesis_parameters']}
            if (request.get('identity') != cb._digest({'identity': identity, 'payload': payload})
                    or not request.get('job_id') or not str(request.get('rejected', '')).startswith(
                        ('Chatterbox initialism pronunciation mismatch:',
                         'Word-hint audio differs from its complete source phone sequence',
                         'Required complete-source phone sequence differs from the source'))):
                raise RuntimeError('Numeric repair requires all exhausted pronunciation jobs')
        spans = repair.get('numbers')
        if not isinstance(spans, list) or not spans:
            raise RuntimeError('Numeric repair requires exact source number spans')
        added, previous_end = [], -1
        protected = list(pronunciation.PROTECTED_TEXT_RE.finditer(source))
        for span in spans:
            if not isinstance(span, dict):
                raise RuntimeError('Numeric repair requires exact source number spans')
            left, right = span.get('start'), span.get('end')
            if (type(left) is not int or type(right) is not int
                    or not 0 <= left < right <= len(source) or left < previous_end
                    or any(edit['start'] < right and edit['end'] > left for edit in local)
                    or any(match.start() < right and match.end() > left for match in protected)
                    or (left and source[left - 1] in '0123456789.')
                    or (right < len(source) and source[right] in '0123456789.')):
                raise RuntimeError('Numeric repair cannot overlap or truncate source tokens')
            literal = source[left:right]
            if not re.fullmatch(pronunciation.NUMERIC_LITERAL_RE, literal):
                raise RuntimeError('Numeric repair must select complete source numerals')
            added.append({'start': left, 'end': right, 'source': literal, 'kind': 'number',
                          'spoken': pronunciation.numeric_cue(literal), 'numeric_cue_version': 1})
            previous_end = right
        repaired_edits = sorted([*local, *added], key=lambda edit: edit['start'])
        children = cb._split_text(source, max_words=max_words, max_chars=max_chars,
                                  pronunciation_edits=repaired_edits)
        child_stems = [f'{stem}.numeric-v1-{index:02d}' for index in range(1, len(children) + 1)]
        binding = {'repair_sha256': cb._digest(repair), 'chunks': children, 'stems': child_stems}
        applied = directory / f'{stem}.numeric-repair-applied.json'
        if applied.exists():
            if cb._read_json(applied) != binding:
                raise RuntimeError('Numeric repair changed after activation; preserving its jobs')
        else:
            cb._write_json(applied, binding)
        revised.extend({**edit, 'start': start + edit['start'], 'end': start + edit['end']} for edit in added)
        result.extend(children)
        names.extend(child_stems)
        bindings.update({name: binding['repair_sha256'] for name in child_stems})
    if ' '.join(result) != ' '.join(chunks):
        raise RuntimeError('Numeric repair changed source text')
    return result, names, sorted(revised, key=lambda edit: edit['start']), bindings
