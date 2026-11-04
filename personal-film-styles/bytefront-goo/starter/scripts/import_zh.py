"""Attach a native Volcengine male reading and its chapter request to a Chinese project."""
import argparse
import hashlib
import io
import wave
from pathlib import Path
from prepare import CONTENT, ROOT, read, write

parser = argparse.ArgumentParser()
parser.add_argument('chapter')
parser.add_argument('wav', type=Path)
parser.add_argument('--voice', required=True, help='Actual male voice ID from the provider receipt')
parser.add_argument('--speed', required=True, type=float, help='Actual speed used by provider')
parser.add_argument('--request-text', required=True, type=Path)
a = parser.parse_args()
assert read(CONTENT/'episode.json')['language'] == 'zh' and a.speed > 0
job = next(j for j in read(CONTENT/'chapters.json')['lines'] if j['id'] == a.chapter)
assert a.request_text.read_text().rstrip('\r\n') == job['text'], 'Provider text differs from chapter'
data = a.wav.read_bytes()
with wave.open(io.BytesIO(data)) as f:
    assert f.getnchannels() == 1 and f.getsampwidth() == 2 and f.getnframes() > 0
    rate = f.getframerate()
out = ROOT/'audio/chapters'
out.mkdir(parents=True, exist_ok=True)
path = out/(a.chapter+'.wav')
if path.exists() or path.with_suffix('.json').exists():
    raise SystemExit('Use a new take directory or archive the previous take before importing.')
path.write_bytes(data)
write(path.with_suffix('.json'), dict(provider='Volcengine', request=dict(text=job['text'], voice=a.voice,
      speed=a.speed, language='zh'), sample_rate=rate, audio_sha256=hashlib.sha256(data).hexdigest()))
