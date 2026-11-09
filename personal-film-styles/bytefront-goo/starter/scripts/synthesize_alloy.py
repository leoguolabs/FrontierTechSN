"""Generate and finish continuous OpenAI narration for an English Goo episode."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.request
import wave

import numpy as np

from prepare import CONTENT, ROOT, prepare, read, write
from realtime_speech import PROFILE_ID as REALTIME_PROFILE, fetch_realtime

sys.path.insert(0, str(ROOT / 'tools/frame_review'))
from ffmpeg_gate import run

PROFILE_ID = 'openai-alloy-goo'
OPENAI_PROFILES = (PROFILE_ID, REALTIME_PROFILE)
PROFILE_PATH = ROOT / 'voice-config.json'
SPEECH_URL = 'https://api.openai.com/v1/audio/speech'
OPENING = re.compile(r"\bI['’]m\s+(Goo)[,\s]+and\s+this\s+is\s+Ooh[,\s]+Lemme\s+(See)\b", re.I)
RATE = 24000
PCM = ['-f', 'f32le', '-ar', str(RATE), '-ac', '1']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def speech_request(profile, job, audio_format):
    text = job['spoken_text']
    instructions = [profile['instruction']]
    if OPENING.search(text):
        transition = profile['reference_transition']
        if transition.casefold() not in text.casefold():
            transition = 'the next sentence'
        instructions.append(profile['opening_instruction'].format(transition=transition))
    instructions.append(profile['reading_instruction'])
    return dict(model=profile['model'], voice=profile['voice'], input=text,
                instructions=' '.join(instructions), speed=profile['provider_speed'],
                response_format=audio_format)


def fetch_speech(payload):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise SystemExit('Set OPENAI_API_KEY for OpenAI Audio API synthesis, or import a verified OpenAI.fm take.')
    request = urllib.request.Request(
        SPEECH_URL, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    request.add_unredirected_header('Authorization', f'Bearer {key}')
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if not response.headers.get_content_type().startswith(('audio/', 'application/octet-stream')):
                raise ValueError('OpenAI Audio API did not return audio')
            return response.read(), response.headers.get('x-request-id')
    except urllib.error.HTTPError as error:
        raise SystemExit(f'OpenAI Audio API returned HTTP {error.code} '
                         f'(request ID {error.headers.get("x-request-id", "unavailable")})') from None


def commit_files(files):
    linked = []
    try:
        for src, dst in files:
            os.link(src, dst)
            linked.append(dst)
    except BaseException:
        for path in linked:
            path.unlink()
        raise


def freeze_source(profile, job, raw_dir, temp, imported, receipt_path):
    realtime = profile['profile_id'] == REALTIME_PROFILE
    source = 'OpenAI Realtime API' if realtime else 'OpenAI.fm'
    frozen_receipt = raw_dir / (job['id'] + '.provider.json')
    if frozen_receipt.exists():
        if imported:
            raise FileExistsError('An original take is already frozen for this chapter')
        receipt = read(frozen_receipt)
        raw = raw_dir / (job['id'] + '.' + receipt['request']['response_format'])
    else:
        raw = temp / ('source' + imported.suffix.lower()) if imported else temp / 'source.wav'
        expected = speech_request(profile, job, raw.suffix[1:])
        if expected['response_format'] not in (('wav',) if realtime else ('mp3', 'wav')):
            raise ValueError(f'Unsupported original audio format for {source}')
        if imported:
            receipt = read(receipt_path)
            if receipt.get('source') != source:
                raise ValueError(f'The imported take must identify its actual {source} source')
            raw.write_bytes(imported.read_bytes())
        elif realtime:
            content, metadata = fetch_realtime(expected, profile['keychain_service'])
            raw.write_bytes(content)
            receipt = dict(source=source, request=expected, sha256=digest(raw), **metadata)
        else:
            content, request_id = fetch_speech(expected)
            raw.write_bytes(content)
            receipt = dict(source='OpenAI Audio API', request=expected, sha256=digest(raw),
                           request_id=request_id)
    expected = speech_request(profile, job, raw.suffix[1:])
    if receipt.get('request') != expected or receipt.get('sha256') != digest(raw):
        raise ValueError(f'Original take or request mismatch for {job["id"]}')
    if realtime and (receipt.get('source') != source or not receipt.get('transcript')):
        raise ValueError(f'Missing Realtime source evidence for {job["id"]}')
    if not frozen_receipt.exists():
        raw_target = raw_dir / (job['id'] + raw.suffix)
        metadata = temp / 'provider.json'
        kept = ('source', 'request', 'sha256', 'request_id', 'response_id', 'transcript')
        write(metadata, {key: receipt[key] for key in kept if key in receipt})
        commit_files([(raw, raw_target), (metadata, frozen_receipt)])
        raw = raw_target
    return raw, frozen_receipt


def opening_gaps(text, signal, gaps):
    """Map the two scripted joins to nearby quiet intervals in the original take."""
    title = OPENING.search(text)
    if title is None:
        return None, None, None, False

    import mlx_whisper
    from scipy.signal import resample_poly
    from word_alignment import aligned

    result = mlx_whisper.transcribe(
        resample_poly(signal, 2, 3).astype(np.float32),
        path_or_hf_repo='mlx-community/whisper-large-v3-turbo-q4',
        language='en', temperature=0, condition_on_previous_text=False,
        word_timestamps=True, verbose=False,
    )
    words = [word for segment in result['segments'] for word in segment['words']]
    chars, _ = aligned(text, words)

    def find(group):
        anchors = [char for char in chars if title.start(group) <= char['index'] < title.end(group)]
        if not anchors or not all(char['matched'] for char in anchors):
            return None
        end = anchors[-1]['end']
        candidates = [gap for gap in gaps if end - 0.08 <= gap[0] <= end + 0.24]
        return min(candidates, key=lambda gap: abs(gap[0] - end), default=None)

    starts_with_title = not text[:title.start()].strip()
    entry = None
    if not starts_with_title:
        first = next((char for char in chars if char['index'] == title.start() and char['matched']), None)
        if first is not None:
            start = first['start']
            candidates = [gap for gap in gaps if gap[0] - 0.06 <= start <= gap[1] + 0.22]
            entry = min(candidates, key=lambda gap: abs(gap[1] - start), default=None)
    return entry, find(1), find(2), starts_with_title


def tempo(signal, factor):
    if not signal.size or factor == 1:
        return signal
    result = run(
        ['-nostdin', '-v', 'error', *PCM, '-i', 'pipe:0',
         '-af', f'atempo={factor:.8g}', *PCM, 'pipe:1'],
        input=signal.tobytes(), capture_output=True,
    )
    return np.frombuffer(result.stdout, dtype='<f4')


def finish_audio(raw, target, text, profile):
    decoded = run(
        ['-nostdin', '-hide_banner', '-i', str(raw), '-map', '0:a:0',
         '-af', f'silencedetect=noise={profile["quiet_threshold_db"]}dB:d=0.18',
         *PCM, 'pipe:1'], capture_output=True,
    )
    signal = np.frombuffer(decoded.stdout, dtype='<f4').copy()
    seconds = len(signal) / RATE
    if seconds <= 0 or not np.any(signal):
        raise ValueError('Empty or silent provider audio')
    log = decoded.stderr.decode()
    starts = map(float, re.findall(r'silence_start: (-?[\d.]+)', log))
    ends = map(float, re.findall(r'silence_end: (-?[\d.]+)', log))
    gaps = list(zip(starts, ends))
    head, tail = 0, len(signal)
    if gaps and gaps[0][0] <= 0:
        head = round(max(0, gaps.pop(0)[1] - 0.035) * RATE)
    if gaps and gaps[-1][1] >= seconds - 0.035:
        tail = min(tail, round((gaps.pop()[0] + 0.075) * RATE))

    entry, goo, title, starts_with_title = opening_gaps(text, signal, gaps)
    realtime = profile['profile_id'] == REALTIME_PROFILE
    first_join = goo or title
    separate_opening = (title is not None and (realtime or (goo is not None and goo < title))
                        and (starts_with_title or (entry is not None and entry < first_join)))
    opening_pause_limit = profile.get('opening_pause_limit_seconds', 0.095)
    pause_limit = profile.get('pause_limit_seconds', 0.245)
    rate = profile['narration_tempo']
    intro_rate = profile['opening_tempo']['self_introduction']
    section_rate = intro_rate if separate_opening and starts_with_title else rate
    pieces, section, trimmed = [], [], []
    cursor = head
    for gap in gaps:
        left, right = gap
        switch_rate = separate_opening and gap in (entry, goo, title)
        if gap == goo:
            keep = profile['opening_pause_seconds']['after_goo'] * section_rate * profile['final_tempo']
        elif gap == title:
            keep = profile['opening_pause_seconds']['after_title'] * section_rate * profile['final_tempo']
        elif title is not None and gap < title and (
            (goo is not None and goo < gap) or (realtime and (starts_with_title or (entry and entry < gap)))
        ):
            keep = opening_pause_limit
        else:
            keep = pause_limit
        shortening = right - left > keep
        if not shortening and not switch_rate:
            continue
        keep = min(keep, right - left)
        end = round((left + keep / 2) * RATE)
        resume = round((right - keep / 2) * RATE)
        fade = round(0.006 * RATE)
        signal[end-fade:end] *= np.linspace(1, 0, fade)
        signal[resume:resume+fade] *= np.linspace(0, 1, fade)
        section.append(signal[cursor:end])
        cursor = resume
        if shortening:
            trimmed.append({'start': left, 'end': right, 'kept_seconds': keep,
                            'anchor': 'Goo' if gap == goo else 'show title' if gap == title else 'pause'})
        if switch_rate:
            pieces.append(tempo(np.concatenate(section), section_rate))
            section = []
            if gap == entry:
                section_rate = intro_rate
            else:
                section_rate = profile['opening_tempo']['show_title'] if gap == goo else rate
    section.append(signal[cursor:tail])
    pieces.append(tempo(np.concatenate(section), section_rate))
    delivery = np.concatenate(pieces)
    final_tempo = profile['final_tempo']
    calibrated_tempo = 1.0
    if profile.get('delivery_wpm'):
        word_count = len(re.findall(r"\b\w+(?:['’]\w+)*\b", text))
        if word_count:
            target_seconds = word_count * 60 / profile['delivery_wpm']
            calibrated_tempo = max(1.0, min(profile['delivery_tempo_ceiling'],
                                             len(delivery) / RATE / final_tempo / target_seconds))
    delivery = tempo(delivery, final_tempo * calibrated_tempo)
    run(['-nostdin', '-v', 'error', *PCM, '-i', 'pipe:0', '-ar', '48000',
         '-c:a', 'pcm_s16le', str(target)], input=delivery.tobytes(), capture_output=True)
    with wave.open(str(target)) as wav:
        duration = wav.getnframes() / wav.getframerate()
    if duration <= 0:
        raise ValueError('Empty processed narration')
    return dict(source_seconds=seconds, duration_seconds=duration, pause_edits=trimmed,
                opening_retimed=separate_opening, calibrated_tempo=calibrated_tempo)


def validate_delivery(info, profile, job, source, audio):
    expected = dict(text=job['text'], spoken_text=job['spoken_text'],
                    voice=profile['voice'], speed=profile['provider_speed'], language=profile['language'])
    if (info['provider'] != 'OpenAI' or info['model'] != profile['model']
            or info['request'] != expected or info['profile_sha256'] != digest(PROFILE_PATH)
            or info['audio_sha256'] != digest(audio)
            or info['original_sha256'] != digest(source)
            or info['provider_receipt_sha256'] != digest(ROOT / info['provider_receipt_file'])
            or info['processing']['final_tempo'] != profile['final_tempo']):
        raise ValueError(f'Stale or mismatched OpenAI delivery for {job["id"]}; archive the take before replacing it')


def process_chapter(profile, job, imported, source_receipt):
    raw_dir = ROOT / 'audio/original'
    delivered = ROOT / 'audio/chapters'
    raw_dir.mkdir(parents=True, exist_ok=True)
    delivered.mkdir(parents=True, exist_ok=True)
    audio = delivered / (job['id'] + '.wav')
    meta = audio.with_suffix('.json')
    if audio.exists() or meta.exists():
        info = read(meta)
        validate_delivery(info, profile, job, ROOT / info['original_file'], audio)
        if imported:
            raise FileExistsError('A finished take already exists for this chapter')
        print(f'{job["id"]}: verified existing delivery')
        return
    with tempfile.TemporaryDirectory(dir=ROOT / 'audio') as temporary:
        temp = Path(temporary)
        raw, frozen_receipt = freeze_source(profile, job, raw_dir, temp, imported, source_receipt)
        wav = temp / 'delivery.wav'
        timings = finish_audio(raw, wav, job['spoken_text'], profile)
        info = dict(
            provider='OpenAI', model=profile['model'],
            request=dict(text=job['text'], spoken_text=job['spoken_text'],
                         voice=profile['voice'], speed=profile['provider_speed'], language=profile['language']),
            sample_rate=48000, audio_sha256=digest(wav), duration_seconds=timings['duration_seconds'],
            original_file=raw.relative_to(ROOT).as_posix(), original_sha256=digest(raw),
            provider_receipt_file=frozen_receipt.relative_to(ROOT).as_posix(),
            provider_receipt_sha256=digest(frozen_receipt), profile_sha256=digest(PROFILE_PATH),
            processing=dict(**timings, narration_tempo=profile['narration_tempo'],
                            final_tempo=profile['final_tempo']),
        )
        metadata = temp / 'delivery.json'
        write(metadata, info)
        commit_files([(wav, audio), (metadata, meta)])
        print(f'{job["id"]}: {timings["source_seconds"]:.2f}s -> {timings["duration_seconds"]:.2f}s')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chapter', help='Process one prepared request ID (default: all chapters)')
    parser.add_argument('--original', type=Path, help='Original provider audio matching the selected OpenAI profile')
    parser.add_argument('--receipt', type=Path, help='JSON with source, request and sha256')
    args = parser.parse_args()
    if bool(args.original) != bool(args.receipt) or (args.original and not args.chapter):
        parser.error('Import requires --chapter, --original and --receipt together')
    if read(CONTENT / 'episode.json')['language'] != 'en':
        parser.error('OpenAI narration is configured for English Goo episodes')
    profile = read(PROFILE_PATH)
    if profile['profile_id'] not in OPENAI_PROFILES:
        parser.error('Expected an OpenAI English narration profile')
    with (ROOT / '.alloy.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prepare()
        jobs = [job for job in read(CONTENT / 'chapters.json')['lines']
                if args.chapter is None or job['id'] == args.chapter]
        if not jobs:
            parser.error(f'Unknown chapter: {args.chapter}')
        for job in jobs:
            process_chapter(profile, job, args.original, args.receipt)


if __name__ == '__main__':
    main()
