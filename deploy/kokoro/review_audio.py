"""Objective WAV and independent ASR checks; not a listening review."""
import argparse
import hashlib
import json
import re
import wave
from pathlib import Path

import numpy as np


def words(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower().replace('’', "'"))


def distance(expected, actual):
    previous = list(range(len(actual) + 1))
    for i, token in enumerate(expected, 1):
        current = [i]
        for j, other in enumerate(actual, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(token != other)))
        previous = current
    return previous[-1]


def review(directory, model):
    import mlx_whisper
    directory = Path(directory)
    results = []
    for record in json.loads((directory/'benchmark.json').read_text()):
        name = record['case']['id']
        path = directory/(name+'.wav')
        with wave.open(str(path), 'rb') as audio:
            assert audio.getnchannels() == 1 and audio.getsampwidth() == 2
            rate = audio.getframerate()
            raw = np.frombuffer(audio.readframes(audio.getnframes()), dtype='<i2')
        samples = raw.astype(np.float64)/32768
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        cached_path = directory/(name+'.asr.json')
        cached = json.loads(cached_path.read_text()) if cached_path.exists() else {}
        if cached.get('audio_sha256') == digest and cached.get('asr_model') == model:
            transcript = cached['result']
        else:
            transcript = mlx_whisper.transcribe(str(path), path_or_hf_repo=model, language='en',
                                              temperature=0, condition_on_previous_text=False)
            cached_path.write_text(json.dumps({'audio_sha256':digest,'asr_model':model,'result':transcript}, indent=2))
        expected, actual = words(record['case']['text']), words(transcript['text'])
        differences = distance(expected, actual)
        block = int(rate * 0.01)
        rms = np.sqrt(np.mean(samples[:len(samples)//block*block].reshape(-1,block)**2,axis=1))
        active = np.flatnonzero(rms > 0.001)
        maximum = run = 0
        for silent in (rms[active[0]:active[-1]+1] <= 0.001):
            run = run + 1 if silent else 0
            maximum = max(maximum, run)
        result = {'case':name, 'expected_text':record['case']['text'], 'recognized_text':transcript['text'].strip(),
                  'word_count':len(expected), 'word_edit_distance':differences, 'word_error_rate':differences/len(expected),
                  'duration_seconds':len(raw)/rate, 'sample_rate':rate, 'peak_dbfs':20*np.log10(max(abs(samples))),
                  'rms_dbfs':20*np.log10(np.sqrt(np.mean(samples**2))), 'clipped_samples':int(np.count_nonzero(np.abs(raw.astype(np.int32))>=32767)),
                  'leading_quiet_seconds':int(active[0])*.01, 'trailing_quiet_seconds':(len(rms)-int(active[-1])-1)*.01,
                  'longest_internal_quiet_seconds':maximum*.01,
                  'review_scope':'Independent ASR and decoded waveform measurements; no subjective listening.'}
        results.append(result)
        (directory/'audio-review.json').write_text(json.dumps(results,indent=2))
        print(json.dumps(result), flush=True)
    return results


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--model', required=True)
    arguments=parser.parse_args()
    review(arguments.directory,arguments.model)
