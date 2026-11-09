"""Reproduce the approved Cedar Putonghua audition's pause, tempo and loudness recipe."""
import json
from pathlib import Path
import re
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/frame_review'))
from ffmpeg_gate import run

RATE = 24000
PCM = ['-f', 'f32le', '-ar', str(RATE), '-ac', '1']


def loudness_stats(result):
    log = result.stderr.decode()
    return json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]


def finish_mandarin(raw, target, text, profile):
    decoded = run([
        '-nostdin', '-hide_banner', '-i', str(raw), '-af',
        f'silencedetect=noise={profile["quiet_threshold_db"]}dB:d={profile["silence_min_seconds"]}',
        *PCM, 'pipe:1',
    ], capture_output=True)
    signal = np.frombuffer(decoded.stdout, dtype='<f4').copy()
    if not signal.size or not np.any(signal):
        raise ValueError('Empty or silent Mandarin provider audio')
    source_seconds = len(signal) / RATE
    log = decoded.stderr.decode()
    gaps = list(zip(map(float, re.findall(r'silence_start: (-?[\d.]+)', log)),
                    map(float, re.findall(r'silence_end: (-?[\d.]+)', log))))
    head, tail = 0, len(signal)
    if gaps and gaps[0][0] <= 0:
        head = round(max(0, gaps.pop(0)[1] - profile['head_pad_seconds']) * RATE)
    if gaps and gaps[-1][1] >= source_seconds - .035:
        tail = min(tail, round((gaps.pop()[0] + profile['tail_pad_seconds']) * RATE))
    pause_cap = profile['pause_limit_seconds']
    parts, edits, cursor = [], [], head
    for left, right in gaps:
        if right - left <= pause_cap:
            continue
        end = round((left + pause_cap / 2) * RATE)
        resume = round((right - pause_cap / 2) * RATE)
        fade = round(profile['cut_fade_seconds'] * RATE)
        signal[end-fade:end] *= np.linspace(1, 0, fade)
        signal[resume:resume+fade] *= np.linspace(0, 1, fade)
        parts.append(signal[cursor:end])
        cursor = resume
        edits.append(dict(start=left, end=right, kept_seconds=pause_cap))
    parts.append(signal[cursor:tail])
    joined = np.concatenate(parts)
    hanzi = len(re.findall(r'[\u4e00-\u9fff]', text))
    factor = max(1., min(profile['delivery_tempo_ceiling'],
                        len(joined) / RATE / (hanzi / profile['delivery_hanzi_per_second']))) if hanzi else 1.
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        paced = Path(temporary) / 'paced.wav'
        run(['-nostdin', '-v', 'error', *PCM, '-i', 'pipe:0', '-af', f'atempo={factor:.9f}',
             '-ar', '48000', '-c:a', 'pcm_s16le', str(paced)],
            input=joined.tobytes(), capture_output=True)
        settings = f'I={profile["delivery_lufs"]}:TP={profile["true_peak_dbtp"]}:LRA={profile["loudness_range"]}'
        loud = loudness_stats(run([
            '-nostdin', '-hide_banner', '-i', str(paced),
            '-af', f'loudnorm={settings}:print_format=json', '-f', 'null', '-',
        ], capture_output=True))
        normalization = (f'loudnorm={settings}:measured_I={loud["input_i"]}'
                         f':measured_TP={loud["input_tp"]}:measured_LRA={loud["input_lra"]}'
                         f':measured_thresh={loud["input_thresh"]}:offset={loud["target_offset"]}:linear=true')
        run(['-nostdin', '-v', 'error', '-i', str(paced), '-af', normalization,
             '-ar', '48000', '-c:a', 'pcm_s16le', str(target)], capture_output=True)
    with wave.open(str(target)) as wav:
        duration = wav.getnframes() / wav.getframerate()
    if duration <= 0:
        raise ValueError('Empty processed Mandarin narration')
    return dict(source_seconds=source_seconds, duration_seconds=duration, pause_edits=edits,
                opening_retimed=False, calibrated_tempo=factor, hanzi_count=hanzi,
                loudness_normalization=dict(target_lufs=profile['delivery_lufs'], **loud))
