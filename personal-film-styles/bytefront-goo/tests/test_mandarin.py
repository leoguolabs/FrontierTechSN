import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

STARTER = Path(__file__).resolve().parents[1] / 'starter'
sys.path.insert(0, str(STARTER / 'scripts'))
import mandarin_audio
import synthesize_alloy as narration

PROFILE = json.loads((STARTER / 'profiles/zh-cedar.json').read_text())


def test_mandarin_uses_realtime_and_reuses_the_frozen_take(tmp_path, monkeypatch):
    job = {'id': 'intro', 'spoken_text': PROFILE['approved_reference']['script']}
    calls = []

    def fetch(request, service):
        assert request['voice'] == 'cedar'
        assert request['instructions'] == PROFILE['instruction']
        assert 'Standard mainland Putonghua' in request['instructions']
        assert service == PROFILE['keychain_service']
        calls.append(request)
        return b'provider audio', {'response_id': 'test-response', 'transcript': request['input']}

    monkeypatch.setattr(narration, 'fetch_realtime', fetch)
    monkeypatch.setattr(narration, 'fetch_speech', lambda *a: pytest.fail('Must use Realtime'))
    originals, staging = tmp_path / 'original', tmp_path / 'staging'
    originals.mkdir()
    staging.mkdir()
    raw, receipt_path = narration.freeze_source(PROFILE, job, originals, staging, None, None)
    receipt = json.loads(receipt_path.read_text())
    assert receipt['source'] == 'OpenAI Realtime API'
    assert receipt['sha256'] == hashlib.sha256(raw.read_bytes()).hexdigest()
    assert narration.freeze_source(PROFILE, job, originals, staging, None, None) == (raw, receipt_path)
    assert len(calls) == 1
    with pytest.raises(ValueError, match='request mismatch'):
        narration.freeze_source(PROFILE, {**job, 'spoken_text': '不同的台词。'}, originals, staging, None, None)


@pytest.mark.parametrize('project,requested', [('en', 'zh'), ('zh', 'en')])
def test_wrong_language_command_stops_before_calling_provider(monkeypatch, project, requested):
    monkeypatch.setattr(sys, 'argv', ['narrate', '--language', requested])
    monkeypatch.setattr(narration, 'read', lambda path: {'language': project} if path.name == 'episode.json' else PROFILE)
    monkeypatch.setattr(narration, 'fetch_realtime', lambda *a: pytest.fail('No request should be sent'))
    with pytest.raises(SystemExit) as error:
        narration.main()
    assert error.value.code == 2


def test_chinese_audio_rejects_silent_provider_output(tmp_path, monkeypatch):
    silence = mandarin_audio.np.zeros(24000, dtype='<f4').tobytes()
    monkeypatch.setattr(mandarin_audio, 'run', lambda *a, **kw: SimpleNamespace(stdout=silence, stderr=b''))
    with pytest.raises(ValueError, match='silent'):
        mandarin_audio.finish_mandarin(tmp_path / 'raw.wav', tmp_path / 'out.wav', '测试。', PROFILE)
