"""Build the static two-engine gallery from external, verified sample projects."""
import argparse
import array
import hashlib
import json
import math
import shutil
import sys
import wave
import zipfile
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent


def build_engine(engine, source, output, expected):
    data = json.loads((source / 'manifest.json').read_text())
    if len(data['voices']) != expected or data['expected_voice_count'] != expected:
        raise ValueError(engine + ': incomplete voice collection')
    destination = output / engine
    (destination / 'audio').mkdir(parents=True, exist_ok=True)
    voices, verification, seen = [], [], set()
    for voice in data['voices']:
        identity = voice['id']
        if not identity.replace('_', '').isalnum() or identity in seen:
            raise ValueError('Invalid or duplicate voice ID')
        seen.add(identity)
        relative = Path('audio') / (identity + '.wav')
        path = source / relative
        if voice['file'] != relative.as_posix():
            raise ValueError('Unexpected audio path')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != voice['audio_sha256']:
            raise ValueError('Audio hash mismatch: ' + identity)
        with wave.open(str(path), 'rb') as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 24000):
                raise ValueError('Unexpected audio format: ' + identity)
            pcm = wav.readframes(wav.getnframes())
            if len(pcm) != wav.getnframes() * 2:
                raise ValueError('Truncated WAV: ' + identity)
        values = array.array('h', pcm)
        if sys.byteorder != 'little':
            values.byteswap()
        duration = len(values) / 24000
        peak = max(map(abs, values), default=0)
        if not 1 < duration < 60 or peak < 100 or abs(duration - voice['duration_seconds']) > .001:
            raise ValueError('Invalid audio duration/signal: ' + identity)
        bars = []
        for i in range(40):
            block = values[i * len(values) // 40:(i + 1) * len(values) // 40]
            bars.append(math.sqrt(sum(x*x for x in block) / len(block)))
        record = {key: voice[key] for key in
                  ('id', 'name', 'language', 'accent', 'gender', 'file',
                   'duration_seconds', 'generation_seconds', 'audio_sha256')}
        if 'category' in voice:
            record['category'] = voice['category']
        record['waveform'] = [round(x / max(bars), 4) for x in bars]
        voices.append(record)
        verification.append({'id': identity, 'sha256': digest, 'duration_seconds': duration,
                             'sample_rate': 24000, 'channels': 1, 'sample_width': 2,
                             'peak_dbfs': round(20 * math.log10(peak / 32768), 2),
                             'clipped_samples': sum(abs(x) >= 32767 for x in values)})
        shutil.copyfile(path, destination / relative)
    public = {'engine': engine, 'sample_text': data['sample_text'],
              'expected_voice_count': expected, 'voices': voices}
    encoded = json.dumps(public, ensure_ascii=False).replace('<', '\\u003c')
    html = (TEMPLATES / (engine + '.html')).read_text().replace('__DATA__', encoded)
    (destination / 'index.html').write_text(html)
    (destination / 'manifest.json').write_text(json.dumps(public, ensure_ascii=False, indent=2))
    (destination / 'verification.json').write_text(json.dumps(verification, indent=2))
    (destination / 'SAMPLE-TEXT.txt').write_text(data['sample_text'] + '\n')
    with zipfile.ZipFile(destination / 'samples.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in ('manifest.json', 'verification.json', 'SAMPLE-TEXT.txt'):
            archive.write(destination / name, name)
        for voice in voices:
            archive.write(destination / voice['file'], voice['file'])
    print(engine, expected, 'voices;', round(sum(v['duration_seconds'] for v in voices), 2),
          'audio seconds;', sum(v['clipped_samples'] for v in verification), 'clipped samples')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kokoro', required=True, type=Path)
    parser.add_argument('--pocket', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    sources = [args.kokoro.resolve(), args.pocket.resolve()]
    destination = args.output.resolve()
    if any(destination == p or destination in p.parents or p in destination.parents for p in sources):
        raise ValueError('Use a separate output directory')
    texts = [json.loads((p / 'manifest.json').read_text())['sample_text'] for p in sources]
    if texts[0] != texts[1]:
        raise ValueError('Both engines must use the same sample text')
    (destination / 'assets').mkdir(parents=True, exist_ok=True)
    for name in ('catalog.css', 'catalog.js', 'hub.css'):
        shutil.copyfile(TEMPLATES / name, destination / 'assets' / name)
    shutil.copyfile(TEMPLATES / 'hub.html', destination / 'index.html')
    for engine, source, expected in zip(('kokoro', 'pocket'), sources, (28, 21)):
        build_engine(engine, source, destination, expected)


if __name__ == '__main__':
    main()
