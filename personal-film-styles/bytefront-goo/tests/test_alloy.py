from email.message import Message
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

STARTER = Path(__file__).resolve().parents[1] / 'starter'
sys.path.insert(0, str(STARTER / 'scripts'))
import synthesize_alloy as alloy

PROFILE = json.loads((STARTER / 'profiles/en-alloy.json').read_text())


def test_request_keeps_brand_direction_out_of_body_chapters(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    payload = alloy.speech_request(PROFILE, {'spoken_text': 'The test is ready.'}, 'wav')
    assert payload['speed'] == 1.0
    assert "I'm Goo" not in payload['instructions']
    assert 'General American' in payload['instructions']

    def fake_open(request, *, timeout):
        assert request.full_url == 'https://api.openai.com/v1/audio/speech'
        assert request.get_method() == 'POST'
        assert request.get_header('Authorization') == 'Bearer test-key'
        assert json.loads(request.data) == payload
        response = BytesIO(b'provider audio')
        response.headers = Message()
        response.headers['Content-Type'] = 'audio/wav'
        response.headers['x-request-id'] = 'req-test'
        return response

    monkeypatch.setattr(alloy.urllib.request, 'urlopen', fake_open)
    assert alloy.fetch_speech(payload) == (b'provider audio', 'req-test')


def test_freeze_rejects_changed_source_and_resumes_without_fetch(tmp_path, monkeypatch):
    original = tmp_path / 'take.mp3'
    original.write_bytes(b'original audio')
    receipt = tmp_path / 'receipt.json'
    job = {'id': 'intro', 'spoken_text': "I'm Goo and this is Ooh, Lemme See. Here we go."}
    request = alloy.speech_request(PROFILE, job, 'mp3')
    assert 'through the show name' in request['instructions']
    assert "Let's put these stories together" not in request['instructions']
    source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    raw_dir = tmp_path / 'original'
    raw_dir.mkdir()
    staging = tmp_path / 'staging'
    staging.mkdir()

    receipt.write_text(json.dumps(dict(source='OpenAI.fm', sha256='wrong', request=request)))
    with pytest.raises(ValueError, match='take or request mismatch'):
        alloy.freeze_source(PROFILE, job, raw_dir, staging, original, receipt)
    assert list(raw_dir.iterdir()) == []

    receipt.write_text(json.dumps(dict(source='OpenAI.fm', sha256=source_hash, request=request)))
    paths = alloy.freeze_source(PROFILE, job, raw_dir, staging, original, receipt)
    assert paths[0].read_bytes() == original.read_bytes()

    def fail_fetch(_):
        pytest.fail('An existing original take must be reused')

    monkeypatch.setattr(alloy, 'fetch_speech', fail_fetch)
    assert alloy.freeze_source(PROFILE, job, raw_dir, staging, None, None) == paths


def test_opening_can_follow_a_hook_when_asr_starts_inside_the_pause(monkeypatch):
    words = [
        ('First', 0.0, 0.50), ('a', 0.50, 0.60), ('hook.', 0.60, 1.18),
        ("I'm", 1.54, 2.10), ('Goo,', 2.10, 2.34), ('and', 2.58, 2.96),
        ('this', 2.96, 3.18), ('is', 3.18, 3.40), ('Ooh,', 3.40, 3.76),
        ('Let', 4.20, 4.32), ('Me', 4.32, 4.46), ('See.', 4.46, 4.70),
        ('Now', 5.38, 5.94), ('watch.', 5.94, 6.20),
    ]
    result = {'segments': [{'words': [dict(word=word, start=start, end=end)
                                    for word, start, end in words]}]}
    monkeypatch.setitem(sys.modules, 'mlx_whisper', SimpleNamespace(transcribe=lambda *a, **kw: result))
    entry, goo, title, at_start = alloy.opening_gaps(
        "First a hook. I'm Goo and this is Ooh, Lemme See. Now watch.",
        alloy.np.zeros(24000),
        [(1.33, 1.85), (2.50, 2.85), (3.94, 4.19), (4.83, 5.74)],
    )
    assert (entry, goo, title, at_start) == ((1.33, 1.85), (2.50, 2.85), (4.83, 5.74), False)
