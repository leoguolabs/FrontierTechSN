"""Collect a serial batch of Pocket TTS samples into an external project."""
import argparse
import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--voices', required=True, help='Comma-separated verified voice IDs')
    parser.add_argument('--text-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=float, default=240)
    args = parser.parse_args()
    text = args.text_file.read_text().strip()
    voices = args.voices.split(',')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'audio').mkdir(exist_ok=True)
    records = []
    for voice in voices:
        if not voice.replace('_', '').isalnum():
            raise ValueError('Invalid voice ID')
        record_path = args.output / (voice + '.json')
        destination = args.output / 'audio' / (voice + '.wav')
        if record_path.exists() and destination.exists():
            cached = json.loads(record_path.read_text())
            if (cached.get('sample_text') == text
                    and cached.get('audio_sha256') == hashlib.sha256(destination.read_bytes()).hexdigest()):
                records.append(cached)
                print('CACHED', voice, flush=True)
                continue
        request = urllib.request.Request(
            args.source.rstrip('/') + '/tts',
            data=urllib.parse.urlencode({'text': text, 'voice_url': voice}).encode(),
        )
        started = time.monotonic()
        print('REQUEST', voice, flush=True)
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as response:
            blob = response.read()
        generation_seconds = time.monotonic() - started
        # Pocket streams a placeholder RIFF/data size. Rewrite only the header,
        # preserving every PCM sample and its rate/channel/width parameters.
        with wave.open(io.BytesIO(blob), 'rb') as source:
            channels, width, rate = source.getnchannels(), source.getsampwidth(), source.getframerate()
            pcm = source.readframes(source.getnframes())
        if not pcm or len(pcm) % (width * channels):
            raise ValueError('Incomplete PCM stream: ' + voice)
        temporary = destination.with_suffix('.tmp')
        with wave.open(str(temporary), 'wb') as target:
            target.setnchannels(channels)
            target.setsampwidth(width)
            target.setframerate(rate)
            target.writeframes(pcm)
        temporary.replace(destination)
        record = {
            'id': voice, 'name': voice.replace('_', ' ').title(),
            'category': 'a-f' if voice[0] <= 'f' else 'g-m' if voice[0] <= 'm' else 'p-z',
            'language': 'en', 'accent': '英语', 'gender': '',
            'file': 'audio/' + destination.name,
            'duration_seconds': len(pcm) / (width * channels * rate),
            'generation_seconds': round(generation_seconds, 3),
            'sample_rate': rate, 'channels': channels, 'sample_width': width,
            'audio_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'sample_text': text,
        }
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        records.append(record)
        print('COMPLETE', voice, round(record['duration_seconds'], 2),
              round(generation_seconds, 2), flush=True)
        time.sleep(2)  # A single request at a time, with a gap between samples.
    manifest = {'engine': 'pocket', 'sample_text': text,
                'expected_voice_count': len(voices), 'voices': records}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print('ALL COMPLETE', len(records), flush=True)


if __name__ == '__main__':
    main()
