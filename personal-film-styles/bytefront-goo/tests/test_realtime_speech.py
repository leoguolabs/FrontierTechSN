import base64
from io import BytesIO
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import wave

import pytest
from websockets.sync import client

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter/scripts'))
import realtime_speech
import synthesize_alloy as narration

REQUEST = {
    'model': 'gpt-realtime-2.1-mini',
    'voice': 'cedar',
    'speed': 1.0,
    'instructions': 'Read verbatim in a General American male voice.',
    'input': 'This is Goo.',
}


@pytest.mark.parametrize('status', ['completed', 'incomplete'])
def test_realtime_requires_complete_response(monkeypatch, status):
    waveform = bytes(range(16))
    events = iter([
        {'type': 'session.created'},
        {'type': 'session.updated', 'session': {'model': REQUEST['model'], 'audio': {'output': {
            'voice': 'cedar', 'format': {'type': 'audio/pcm', 'rate': 24000}
        }}}},
        {'type': 'conversation.item.added'},
        {'type': 'response.output_audio.delta', 'delta': base64.b64encode(waveform).decode()},
        {'type': 'response.done', 'response': {'status': status, 'id': 'response-test', 'output': [
            {'content': [{'type': 'output_audio', 'transcript': REQUEST['input']}]}
        ]}},
    ])
    sent = []

    class Socket:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def send(self, packet):
            sent.append(json.loads(packet))
        def recv(self, *, timeout):
            return json.dumps(next(events))

    def connect(url, *, additional_headers, **kwargs):
        assert url == 'wss://api.openai.com/v1/realtime?model=gpt-realtime-2.1-mini'
        assert additional_headers == {'Authorization': 'Bearer test-token'}
        return Socket()

    monkeypatch.setattr(client, 'connect', connect)
    monkeypatch.setattr(realtime_speech, 'api_key', lambda service: 'test-token')
    if status == 'completed':
        audio, receipt = realtime_speech.fetch_realtime(REQUEST, 'test-service')
        with wave.open(BytesIO(audio)) as wav:
            assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (24000, 1, 2)
            assert wav.readframes(wav.getnframes()) == waveform
        assert receipt == {'response_id': 'response-test', 'transcript': REQUEST['input']}
    else:
        with pytest.raises(ValueError, match='did not complete'):
            realtime_speech.fetch_realtime(REQUEST, 'test-service')

    assert [event['type'] for event in sent] == ['session.update', 'conversation.item.create', 'response.create']
    assert sent[0]['session']['audio']['output']['voice'] == 'cedar'
    assert sent[1]['item']['content'][0]['text'] == REQUEST['input']


def test_cedar_pacing_keeps_the_requested_output_path(monkeypatch, tmp_path):
    profile = json.loads((Path(narration.ROOT) / 'profiles/en-cedar.json').read_text())
    target = tmp_path / 'delivery.wav'
    signal = narration.np.full(3 * narration.RATE, 0.02, dtype='<f4')

    def run(args, **kwargs):
        if args[-1] == 'pipe:1':
            return SimpleNamespace(stdout=signal.tobytes(), stderr=b'')
        assert args[-1] == str(target)
        with wave.open(str(target), 'wb') as audio:
            audio.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
            audio.writeframes(b'\x01\x00' * 48000)

    monkeypatch.setattr(narration, 'run', run)
    monkeypatch.setattr(narration, 'tempo', lambda audio, factor: audio)
    timing = narration.finish_audio(tmp_path / 'source.wav', target, REQUEST['input'], profile)
    assert timing['calibrated_tempo'] == profile['delivery_tempo_ceiling']
    assert target.is_file()
