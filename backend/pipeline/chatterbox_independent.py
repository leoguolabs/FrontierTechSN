"""Independent checks for extra speech in English pronunciation chunks."""

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from difflib import SequenceMatcher

from backend import config
from backend.pipeline.tts import TtsIntegrityError

MODEL = 'mlx-community/whisper-small-mlx'
AUDIT_VERSION = 2
logger = logging.getLogger(__name__)


async def _transcribe_independently(wav: Path, transcript: Path, env: dict) -> None:
    """Retry a slow local decoder without resubmitting the completed TTS job."""
    command = [
        sys.executable, '-m', 'backend.pipeline.av_sync', 'transcribe-mlx',
        str(wav), str(transcript), '--model', MODEL, '--language', 'en',
    ]
    for attempt, timeout in enumerate((180, 360), start=1):
        # A timed-out process may already have written output. Only accept
        # output from an invocation that also exits successfully.
        transcript.unlink(missing_ok=True)
        started = time.monotonic()
        try:
            done = await asyncio.to_thread(
                subprocess.run, command, cwd=config.PROJECT_ROOT, env=env,
                capture_output=True, timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError) as error:
            def output_text(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value

            diagnostic = {
                'attempt': attempt, 'timeout_seconds': timeout,
                'elapsed_seconds': time.monotonic() - started,
                'error': str(error),
                'stdout': output_text(getattr(error, 'stdout', None)),
                'stderr': output_text(getattr(error, 'stderr', None)),
            }
            transcript.with_name(f'decoder-failure-{time.time_ns()}.json').write_text(
                json.dumps(diagnostic, indent=2), encoding='utf-8')
            if isinstance(error, subprocess.TimeoutExpired) and attempt == 1:
                logger.warning('Independent recognizer timed out after %ss; retrying the same audio once', timeout)
                continue
            raise RuntimeError('Independent recognizer unavailable; preserving the completed job') from error
        if done.returncode or not transcript.exists():
            raise RuntimeError('Independent recognizer unavailable; preserving the completed job')
        return


class WaveformTailError(TtsIntegrityError):
    """Complete independent speech matched, but separated tail sound remains."""

    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report


def _versioned_name_spacing(text: str, observed: str) -> dict | None:
    """Resolve whitespace only in an exact source name-number plus V-version.

    Table30 V2 and Table 30v2 preserve both numeric runs and the V between
    them. Restrict this to title-case names with an explicit source V suffix;
    separate model identifiers, decimals and arbitrary word joins stay out.
    Require the complete utterance to match after this bounded rewrite.
    """
    from backend.pipeline import tts

    revised, evidence = observed, []
    for match in re.finditer(
            r'(?<![\w.])([A-Z][a-z]+)([0-9]+)[ \t]+V([0-9]+)(?![\w.])', text):
        name, number, version = match.groups()
        pattern = re.compile(
            r'(?<![\w.])' + re.escape(name) + r'[ \t]*' + re.escape(number)
            + r'[ \t]*v[ \t]*' + re.escape(version) + r'(?![\w.])', re.IGNORECASE)
        canonical = f'{name}{number} V{version}'
        matches = list(pattern.finditer(revised))
        if matches:
            evidence.append({'source': match[0], 'source_start': match.start(),
                             'numeric_groups': [number, version],
                             'observed': [row[0] for row in matches]})
            revised = pattern.sub(lambda _match: canonical, revised)
    if not evidence or revised == observed:
        return None
    return {'spans': evidence, 'normalized_transcript': revised,
            'complete_source_match': tts._lexical_tokens(revised) == tts._lexical_tokens(text)}


def _repeated_source_phrases(text: str, words: list[dict]) -> list[dict]:
    """Find extra source phrases, including ordinary words inside a chunk.

    Requiring two words and disjoint acoustic intervals avoids treating an
    overlapping duplicate decoder token as a second spoken utterance.
    """
    from backend.pipeline import tts

    expected = tts._lexical_tokens(text)
    observed, indexes = tts._transcript_tokens(words)
    repeats = []
    for tag, _a, _b, left, right in SequenceMatcher(
            a=expected, b=observed, autojunk=False).get_opcodes():
        phrase = observed[left:right]
        if tag != 'insert' or len(phrase) < 2 or not tts._subsequence_starts(expected, phrase):
            continue
        start = words[indexes[left]].get('start')
        end = words[indexes[right - 1]].get('end')
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            continue
        for other in tts._subsequence_starts(observed, phrase):
            if other == left:
                continue
            other_start = words[indexes[other]].get('start')
            other_end = words[indexes[other + len(phrase) - 1]].get('end')
            if (isinstance(other_start, (int, float)) and isinstance(other_end, (int, float))
                    and other_end > other_start and (end <= other_start or other_end <= start)):
                repeats.append({'words': phrase, 'start': start, 'end': end})
                break
    return repeats


async def audit_part(wav: Path, text: str, edits: list[dict], directory: Path) -> dict:
    from backend.pipeline import chatterbox, tts
    from backend.pipeline.tts_tail_guard import inspect_tail

    scope = 'all_parts_independent_speech_and_waveform_tail_check'
    identity = {
        'audio_sha256': tts._file_sha256(wav),
        'source_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'edits_sha256': chatterbox._digest(edits),
        'model': MODEL, 'version': AUDIT_VERSION,
    }
    target = directory / identity['source_sha256'] / identity['audio_sha256']
    target.mkdir(parents=True, exist_ok=True)
    transcript, marker = target / 'transcript.json', target / 'identity.json'
    binding = chatterbox._read_json(marker)
    if (not transcript.exists() or binding.get('identity') != identity
            or binding.get('transcript_sha256') != tts._file_sha256(transcript)):
        env = os.environ.copy()
        env['HF_HUB_OFFLINE'] = '1'
        await _transcribe_independently(wav, transcript, env)
        chatterbox._write_json(marker, {
            'identity': identity, 'transcript_sha256': tts._file_sha256(transcript),
        })
    try:
        words = json.loads(transcript.read_text())
        if (not isinstance(words, list) or not words
                or any(not isinstance(word, dict) for word in words)
                or not tts._raw_transcript(words).strip()):
            raise ValueError('Independent recognizer did not return word observations')
        spelling = chatterbox._pronunciation_report(text, words, edits)
    except (OSError, ValueError, TypeError) as error:
        chatterbox._write_json(marker, {'observation_unavailable': True, 'identity_before_failure': identity})
        raise RuntimeError('Independent observations unavailable; preserving the completed job') from error
    extra_initialisms, identifier_mismatches = [], []
    for difference in spelling['differences']:
        if (any(re.search(r'\d', token) for token in difference['source'])
                or (not difference['source'] and any(
                    re.search(r'\d', token) for token in tts._canonicalize_number_tokens(difference['asr'])))):
            identifier_mismatches.append(difference)
        for form in set(spelling['targets']):
            def count(tokens):
                total, cursor = 0, 0
                while cursor < len(tokens):
                    end = chatterbox._match_spoken_letters(tokens, cursor, len(tokens), form)
                    if end is None:
                        cursor += 1
                    else:
                        total += 1
                        cursor = end
                return total
            if count(difference['asr']) > count(difference['source']):
                extra_initialisms.append({'target': form, 'difference': difference})
    report = {
        'required': True, 'scope': scope, 'identity': identity,
        'transcript_sha256': tts._file_sha256(transcript),
        'raw_transcript': tts._raw_transcript(words),
        'tail': chatterbox._trailing_speech_report(text, words),
        'normalized_tail': chatterbox._trailing_speech_report(
            text, [{'text': spelling['normalized_transcript']}]),
        'extra_initialisms': extra_initialisms,
        'identifier_mismatches': identifier_mismatches,
        'waveform_tail': inspect_tail(wav, words),
        'repeated_source_phrases': _repeated_source_phrases(text, words),
    }
    if tts._file_sha256(wav) != identity['audio_sha256']:
        raise RuntimeError('Original waveform changed during independent verification')
    spacing = _versioned_name_spacing(text, report['raw_transcript'])
    if spacing and not spacing['complete_source_match']:
        # A second V2 can otherwise align with the intended occurrence and
        # hide the first inside the ordinary name prefix. Keep this failure.
        identifier_mismatches.append({
            'kind': 'version_spacing_source_mismatch', 'source': tts._lexical_tokens(text),
            'asr': tts._lexical_tokens(spacing['normalized_transcript']), 'source_start': 0})
    if (identifier_mismatches and spacing and spacing['complete_source_match']
            and report['tail']['passed'] and report['normalized_tail']['passed']
            and not extra_initialisms and not report['repeated_source_phrases']
            and report['waveform_tail']['passed']):
        # Keep the original transcript and differences. The exact full-source
        # comparison above changes whitespace only inside the named span;
        # it cannot correct a word, numeral, missing letter, echo or tail.
        report['asr_identifier_mismatches'] = identifier_mismatches
        report['source_bound_version_spacing'] = spacing
        report['verification_mode'] = 'complete_source_version_spacing'
        identifier_mismatches = []
        report['identifier_mismatches'] = []
    from difflib import SequenceMatcher
    model_names = {edit['source'].casefold() for edit in edits if edit.get('kind') == 'model_name'}
    expected_tokens = tts._lexical_tokens(text)
    observed_tokens = tts._lexical_tokens(spelling['normalized_transcript'])
    only_model_spelling = all(
        tag == 'equal' or (tag == 'replace' and end == start + 1
                           and expected_tokens[start] in model_names)
        for tag, start, end, _left, _right in SequenceMatcher(
            a=expected_tokens, b=observed_tokens, autojunk=False).get_opcodes())
    if (identifier_mismatches and model_names
            and only_model_spelling
            and all(row.get('kind') == 'replace' and len(row['source']) == 1
                    and row['source'][0] in model_names for row in identifier_mismatches)
            and report['tail']['passed'] and report['normalized_tail']['passed']
            and not extra_initialisms and not report['repeated_source_phrases']
            and report['waveform_tail']['passed']):
        from backend.pipeline import chatterbox_phonemes
        acoustic = await chatterbox_phonemes.confirm(wav, text, edits, target / 'model-name-phones')
        if acoustic is None or acoustic.get('supported') is not True:
            raise RuntimeError('Independent model-name acoustic observation unavailable; preserving the completed job')
        if (acoustic.get('audio_sha256') != identity['audio_sha256']
                or acoustic.get('source_sha256') != identity['source_sha256']
                or acoustic.get('conditioned_on_reference_text') is not False
                or acoustic.get('method') != 'complete_source_phone_sequence'):
            raise RuntimeError('Independent model-name acoustic evidence differs from the source waveform')
        report['model_name_phone_confirmation'] = acoustic
        if acoustic.get('passed') is True:
            # Keep the independent recognizer's original spelling. Only an
            # exact complete-source, unconditioned phone observation can
            # distinguish Dex/decks spelling drift from missing speech.
            report['asr_identifier_mismatches'] = identifier_mismatches
            identifier_mismatches = []
            report['identifier_mismatches'] = []
            report['verification_mode'] = 'complete_source_model_name_phone_sequence'
    report['passed'] = (report['tail']['passed'] and report['normalized_tail']['passed']
                        and not extra_initialisms and not identifier_mismatches
                        and not report['repeated_source_phrases']
                        and report['waveform_tail']['passed'])
    chatterbox._write_json(target / 'audit.json', report)
    if not report['passed']:
        if (tts._lexical_tokens(text) == tts._lexical_tokens(report['raw_transcript'])
                and report['tail']['passed'] and report['normalized_tail']['passed']
                and not extra_initialisms and not identifier_mismatches
                and not report['repeated_source_phrases'] and not report['waveform_tail']['passed']):
            raise WaveformTailError(
                'Independent Chatterbox check found unrequested speech: ' + json.dumps(report), report)
        raise tts.TtsIntegrityError('Independent Chatterbox check found unrequested speech: ' +
                                  json.dumps({'tail': report['tail']['extra_words'],
                                              'extra_initialisms': extra_initialisms,
                                              'identifier_mismatches': identifier_mismatches,
                                              'repeated_source_phrases': report['repeated_source_phrases'],
                                              'waveform_tail': report['waveform_tail']}))
    return report
