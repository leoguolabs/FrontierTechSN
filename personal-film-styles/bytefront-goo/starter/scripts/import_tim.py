"""Import verified native Tim audio; preserve provider-native 1.3x timing without tempo processing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import wave
import av
from prepare import CONTENT, ROOT, read, write


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('chapter')
    parser.add_argument('audio', type=Path, help='Unmodified provider MP3 or WAV')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    profile = read(ROOT/'voice-config.json')
    job = next(j for j in read(CONTENT/'chapters.json')['lines'] if j['id'] == args.chapter)
    receipt = read(args.receipt)
    if (read(CONTENT/'episode.json')['language'] != 'en'
            or profile['profile_id'] != 'volcengine-tim-native130'
            or profile['provider_speed'] != 1.3 or profile['delivery_speed'] != 1.3
            or profile['speech_rate'] != 30 or profile['post_synthesis_tempo_processing'] is not False):
        raise ValueError('Expected provider-native Tim 1.3x English profile')
    expected = {'voice': 'Tim', 'model': profile['model'], 'controls': profile['controls'],
                'instruction': profile['instruction'], 'text': job['text'],
                'spoken_text': job['spoken_text'], 'sha256': digest(args.audio),
                'provider_speed': 1.3, 'speech_rate': 30, 'post_synthesis_tempo_processing': False}
    if not str(receipt.get('provider', '')).startswith('Volcengine'):
        raise ValueError('Missing Volcengine source provenance')
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError('Source receipt mismatch: '+key)
    if receipt.get('processing') or not receipt.get('rate_evidence'):
        raise ValueError('Import native provider audio, never a previously sped-up derivative')
    if args.audio.suffix.lower() not in ('.mp3', '.wav'):
        raise ValueError('Use the original provider MP3 or WAV')
    original = ROOT/'audio/original'/args.chapter
    output = ROOT/'audio/chapters'/args.chapter
    native_file = original.with_suffix(args.audio.suffix.lower())
    native_pcm = original.with_suffix('.native.wav')
    source_receipt = original.with_suffix('.provider.json')
    wav = output.with_suffix('.wav')
    meta = output.with_suffix('.json')
    destinations = [native_file, native_pcm, source_receipt, wav, meta]
    if any(p.exists() for p in destinations):
        raise FileExistsError('Chapter already imported: archive its take before a deliberate replacement')
    for p in destinations:
        p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/'audio') as temporary:
        temp = Path(temporary)
        decoded = temp/'native.wav'
        with av.open(str(args.audio)) as source, wave.open(str(decoded), 'wb') as writer:
            converter = av.AudioResampler(format='s16', layout='mono', rate=48000)
            writer.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
            for frame in source.decode(audio=0):
                for chunk in converter.resample(frame):
                    writer.writeframes(chunk.to_ndarray().astype('<i2').tobytes())
            for chunk in converter.resample(None):
                writer.writeframes(chunk.to_ndarray().astype('<i2').tobytes())
        with wave.open(str(decoded)) as f:
            native_seconds = f.getnframes()/f.getframerate()
        if native_seconds <= 0:
            raise ValueError('Empty provider audio')
        processed = temp/'delivery.wav'
        # The delivery PCM is byte-identical to the decoded native PCM.
        # No FFmpeg, atempo, rubberband, rate reinterpretation, or sample stretching.
        os.link(decoded, processed)
        seconds = native_seconds
        info = dict(provider='Volcengine', model=profile['model'],
                    request=dict(text=job['text'], spoken_text=job['spoken_text'],
                                 voice=profile['voice_type'], speed=1.3, language='en-us'),
                    sample_rate=48000, audio_sha256=digest(processed), duration_seconds=seconds,
                    original_file=native_file.relative_to(ROOT).as_posix(), original_sha256=digest(args.audio),
                    native_pcm_file=native_pcm.relative_to(ROOT).as_posix(), native_pcm_sha256=digest(decoded),
                    native_seconds=native_seconds, provider_receipt_sha256=digest(args.receipt),
                    profile_sha256=digest(ROOT/'voice-config.json'),
                    processing=dict(provider_speed=1.3, delivery_speed=1.3, speech_rate=30, atempo_passes=0,
                                    time_stretch=False, stage='format conversion only; native timing retained'))
        # Freeze the production-relevant receipt fields, without browser/session credentials.
        kept = {k: receipt[k] for k in ('provider', 'model', 'voice', 'controls', 'instruction', 'text',
                'spoken_text', 'text_sha256', 'spoken_text_sha256', 'sha256', 'bytes', 'duration',
                'generated_utc', 'method', 'billing_mode', 'provider_speed', 'speech_rate',
                'post_synthesis_tempo_processing', 'rate_evidence') if k in receipt}
        write(temp/'provider.json', kept)
        write(temp/'delivery.json', info)
        (temp/'source').write_bytes(args.audio.read_bytes())
        staged = [temp/'source', decoded, temp/'provider.json', processed, temp/'delivery.json']
        committed = []
        try:
            for src, dst in zip(staged, destinations):
                os.link(src, dst)  # exclusive: another import cannot overwrite a take
                committed.append(dst)
        except BaseException:
            for dst in committed:
                dst.unlink()
            raise
    print(json.dumps({'chapter': args.chapter, 'native_seconds': native_seconds,
                      'delivery_seconds': seconds, 'rate': 1.3, 'atempo_passes': 0}))


if __name__ == '__main__':
    main()
