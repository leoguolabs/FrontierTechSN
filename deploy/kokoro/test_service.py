"""Service behavior tests run without loading a speech model."""
import asyncio
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location("kokoro_deployment", Path(__file__).with_name("service.py"))
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class Engine:
    def get_voices(self):
        return ["af_heart", "am_michael", "bm_george", "zf_xiaobei"]

    def create(self, text, **kwargs):
        return np.sin(np.arange(24000, dtype=np.float32) * 0.03) * 0.3, 24000


def loader(*args):
    return Engine(), {"files": {"model.onnx": {"sha256": "test"}}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("KOKORO_API_KEY", "x" * 40)
    monkeypatch.setenv("KOKORO_DATA_DIR", str(tmp_path))
    with TestClient(service.create_app(loader)) as client:
        yield client


AUTH = {"Authorization": "Bearer " + "x" * 40}


def test_auth_and_bounded_request(client):
    assert client.get("/health").json()["ready"] is True
    assert client.get("/v1/voices").status_code == 401
    assert client.post("/v1/jobs", json={"text": "hello"}).status_code == 401
    assert client.post("/v1/jobs", json={"text": "a" * 2001}, headers=AUTH).status_code == 422
    assert client.post("/v1/jobs", content=b"x" * 17000, headers=AUTH).status_code == 413
    assert client.post("/v1/jobs", json={"text": "hello", "voice": "../../etc/passwd"}, headers=AUTH).status_code == 422
    assert client.post("/v1/jobs", json={"text": "hello", "language": "cmn"}, headers=AUTH).status_code == 422
    assert client.post("/v1/jobs", json={"text": "hello", "voice": "bm_george"}, headers=AUTH).status_code == 422
    assert client.post("/v1/jobs", json={"text": "hello", "speed": 10}, headers=AUTH).status_code == 422


def test_complete_audio_cache_and_unique_benchmark(client):
    payload = {"text": "The spacecraft is ready."}
    first = client.post("/v1/jobs", json=payload, headers=AUTH)
    assert first.status_code == 202
    key = first.json()["id"]
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = client.get("/v1/jobs/" + key, headers=AUTH).json()
        if job["status"] == "completed":
            break
        time.sleep(0.01)
    assert job["status"] == "completed"
    assert job["duration_seconds"] == 1.0
    audio = client.get("/v1/jobs/" + key + "/audio", headers=AUTH)
    assert audio.content.startswith(b"RIFF")
    assert audio.content[8:12] == b"WAVE"
    assert client.post("/v1/jobs", json=payload, headers=AUTH).json()["cache_hit"] is True
    fresh = client.post("/v1/jobs", json={**payload, "cache": False}, headers=AUTH).json()
    assert fresh["id"] != key
    assert client.get("/v1/jobs/unknown/audio", headers=AUTH).status_code == 404


def test_queue_capacity_dedup_and_interrupted_recovery(tmp_path):
    async def run():
        jobs = service.Jobs(tmp_path, Engine(), {"model": "test"}, limit=1)
        record = jobs.submit(service.SpeechRequest(text="First request."))
        assert jobs.submit(service.SpeechRequest(text="First request."))["id"] == record["id"]
        with pytest.raises(HTTPException) as error:
            jobs.submit(service.SpeechRequest(text="Second request."))
        assert error.value.status_code == 429
        recovered = service.Jobs(tmp_path, Engine(), {"model": "test"})
        assert recovered.records[record["id"]]["status"] == "failed"
        assert recovered.submit(service.SpeechRequest(text="First request."))["status"] == "queued"
    asyncio.run(run())


def test_expired_jobs_are_removed(tmp_path):
    async def run():
        jobs = service.Jobs(tmp_path, Engine(), {}, retention=1)
        record = jobs.submit(service.SpeechRequest(text="One."))
        record = jobs.records[record["id"]]
        record.update(status="completed", created_at=time.time() - 3)
        jobs.save(record)
        (tmp_path / (record["id"] + ".wav")).write_bytes(b"expired")
        jobs.prune()
        assert record["id"] not in jobs.records
        assert not list(tmp_path.iterdir())
    asyncio.run(run())
