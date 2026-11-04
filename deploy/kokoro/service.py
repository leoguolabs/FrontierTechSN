"""Bounded, authenticated Kokoro CPU jobs; no downloads during requests."""
import asyncio
import contextlib
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
import wave
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

LOG = logging.getLogger("kokoro")
VERSION = "nr-test-kokoro-v1"
LANGUAGES = ("en-us", "en-gb")


class SpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=2000)
    voice: str = Field(default="af_heart", max_length=40)
    language: str = Field(default="en-us", max_length=10)
    speed: float = Field(default=1.0, ge=0.7, le=1.3, allow_inf_nan=False)
    cache: bool = True


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_engine(model_dir, threads):
    import onnxruntime as ort
    from kokoro_onnx import Kokoro

    manifest = json.loads((model_dir / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if sha256(model_dir / name) != expected["sha256"]:
            raise RuntimeError("Model integrity check failed: " + name)
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.add_session_config_entry("session.intra_op.allow_spinning", "0")
    options.add_session_config_entry("session.inter_op.allow_spinning", "0")
    session = ort.InferenceSession(
        str(model_dir / "kokoro-v1.0.onnx"), options,
        providers=["CPUExecutionProvider"],
    )
    engine = Kokoro.from_session(session, str(model_dir / "voices-v1.0.bin"))
    # Loading ONNX weights alone does not exercise the native phonemizer.
    # Do real, bounded synthesis in each advertised language before readiness.
    for voice, language in [("af_heart", "en-us"), ("bm_george", "en-gb")]:
        audio, rate = engine.create("Ready.", voice=voice, lang=language, speed=1.0)
        if rate != 24000 or len(audio) < 2400 or not np.isfinite(audio).all():
            raise RuntimeError("Startup synthesis failed: " + language)
    return engine, manifest


class Jobs:
    def __init__(self, root, engine, identity, limit=8, retention=604800, max_bytes=2**31):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.engine = engine
        self.identity = identity
        self.queue = asyncio.Queue(maxsize=limit)
        self.records = {}
        self.active = None
        self.retention = retention
        self.max_bytes = max_bytes
        self.voices = sorted(v for v in engine.get_voices() if v[:2] in {"af", "am", "bf", "bm"})
        # This runs before a worker exists. Never remove temporary files while
        # the synthesis thread can be publishing a completed WAV.
        for file in self.root.glob("*.tmp"):
            file.unlink(missing_ok=True)
        for file in self.root.glob("*.json"):
            record = json.loads(file.read_text())
            if record["status"] in {"queued", "running"}:
                record.update(status="failed", error="Service restarted; resubmit the request.", finished_at=time.time())
                self.save(record)
            self.records[record["id"]] = record
        self.prune()

    def save(self, record):
        temporary = self.root / (record["id"] + ".json.tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, allow_nan=False))
        temporary.replace(self.root / (record["id"] + ".json"))

    def prune(self):
        now = time.time()
        completed = sorted(
            (r for r in self.records.values() if r["status"] in {"completed", "failed"}),
            key=lambda r: r["created_at"],
        )
        size = sum(p.stat().st_size for p in self.root.iterdir() if p.is_file())
        for record in completed:
            if now - record["created_at"] <= self.retention and size <= self.max_bytes:
                continue
            for suffix in (".json", ".wav", ".wav.tmp"):
                file = self.root / (record["id"] + suffix)
                if file.exists():
                    size -= file.stat().st_size
                    file.unlink()
            self.records.pop(record["id"], None)

    def submit(self, request):
        if request.language not in LANGUAGES:
            raise HTTPException(422, "This deployment has validated en-us and en-gb only.")
        if request.voice not in self.voices:
            raise HTTPException(422, "Unknown or unsupported voice. See /v1/voices.")
        if request.language == "en-us" and not request.voice.startswith("a"):
            raise HTTPException(422, "Use an American voice for en-us.")
        if request.language == "en-gb" and not request.voice.startswith("b"):
            raise HTTPException(422, "Use a British voice for en-gb.")
        payload = request.model_dump(exclude={"cache"})
        identity = json.dumps([self.identity, payload], sort_keys=True).encode()
        key = hashlib.sha256(identity).hexdigest()
        self.prune()
        old = self.records.get(key) if request.cache else None
        if old and old["status"] in {"queued", "running", "completed"}:
            if old["status"] != "completed" or (self.root / (key + ".wav")).is_file():
                return {**old, "cache_hit": old["status"] == "completed"}
        if self.queue.full():
            raise HTTPException(429, "Synthesis queue is full.", headers={"Retry-After": "10"})
        key = key if request.cache else uuid.uuid4().hex
        record = {"id": key, "status": "queued", "created_at": time.time(), "request": payload,
                  "identity": self.identity, "cache_hit": False}
        self.save(record)
        self.records[key] = record
        self.queue.put_nowait(key)
        return dict(record)

    def synthesize(self, record):
        start = time.monotonic()
        request = record["request"]
        samples, sr = self.engine.create(
            request["text"], voice=request["voice"], speed=request["speed"], lang=request["language"],
        )
        samples = np.asarray(samples, dtype=np.float32).reshape(-1)
        if not np.isfinite(samples).all() or not 0.2 <= len(samples) / sr <= 300:
            raise ValueError("Invalid or out-of-bounds generated audio.")
        peak = float(np.max(np.abs(samples)))
        if peak < 1e-5:
            raise ValueError("Generated audio is silent.")
        gain = min(1.0, 0.999 / peak)
        pcm = (np.clip(samples * gain, -1, 1) * 32767).astype("<i2").tobytes()
        destination = self.root / (record["id"] + ".wav")
        temporary = destination.with_suffix(".wav.tmp")
        with wave.open(str(temporary), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sr)
            output.writeframes(pcm)
        temporary.replace(destination)
        elapsed = time.monotonic() - start
        duration = len(samples) / sr
        return {"duration_seconds": duration, "generation_seconds": elapsed,
                "real_time_factor": elapsed / duration, "sample_rate": sr,
                "channels": 1, "encoding": "PCM_16", "bytes": destination.stat().st_size,
                "audio_sha256": sha256(destination), "model_float_peak": peak, "pcm_gain": gain}

    async def work(self):
        while True:
            key = await self.queue.get()
            self.active = key
            record = self.records[key]
            record.update(status="running", started_at=time.time())
            self.save(record)
            try:
                result = await asyncio.to_thread(self.synthesize, record)
                record.update(result, status="completed", finished_at=time.time())
            except Exception:
                LOG.exception("Synthesis failed: %s", key)
                record.update(status="failed", error="Synthesis failed; inspect server logs.", finished_at=time.time())
            finally:
                self.save(record)
                self.active = None
                self.queue.task_done()


def create_app(engine_loader=None):
    key = os.environ.get("KOKORO_API_KEY", "")
    threads = int(os.environ.get("KOKORO_CPU_THREADS", "4"))
    root = Path(os.environ.get("KOKORO_DATA_DIR", "/data/jobs"))
    model_dir = Path(os.environ.get("KOKORO_MODEL_DIR", "/models"))

    @asynccontextmanager
    async def lifespan(app):
        if len(key) < 32:
            raise RuntimeError("Set a randomly generated KOKORO_API_KEY of at least 32 characters.")
        if not 1 <= threads <= 8:
            raise RuntimeError("KOKORO_CPU_THREADS must be between 1 and 8.")
        start = time.monotonic()
        engine, manifest = await asyncio.to_thread(engine_loader or load_engine, model_dir, threads)
        identity = {"service": VERSION, "model": manifest["files"], "kokoro_onnx": "0.6.1"}
        app.state.jobs = Jobs(root, engine, identity)
        app.state.startup_prepare_seconds = time.monotonic() - start
        worker = asyncio.create_task(app.state.jobs.work())
        try:
            yield
        finally:
            # Uvicorn's graceful timeout bounds shutdown. Persist running status
            # so an interrupted job is explicitly failed on the next startup.
            worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker

    app = FastAPI(title="Kokoro CPU TTS", version=VERSION, lifespan=lifespan)

    def authorize(authorization: str | None = Header(default=None)):
        value = authorization or ""
        if not hmac.compare_digest(value, "Bearer " + key):
            raise HTTPException(401, "Invalid bearer token.")

    @app.middleware("http")
    async def bounded_body(request, call_next):
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 16384):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Request body too large."}, status_code=413)
        if request.method == "POST":
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 16384:
                    from fastapi.responses import JSONResponse
                    return JSONResponse({"detail": "Request body too large."}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    @app.get("/health")
    def health():
        jobs = app.state.jobs
        return {"status": "ok", "ready": True, "version": VERSION, "cpu_threads": threads,
                "queue_depth": jobs.queue.qsize(), "active": jobs.active is not None,
                "startup_prepare_seconds": app.state.startup_prepare_seconds}

    @app.get("/v1/voices", dependencies=[Depends(authorize)])
    def voices():
        return {"voices": app.state.jobs.voices, "languages": LANGUAGES}

    @app.get("/v1/capabilities", dependencies=[Depends(authorize)])
    def capabilities():
        jobs = app.state.jobs
        return {"identity": jobs.identity, "voices": jobs.voices, "languages": LANGUAGES,
                "max_characters": 2000, "max_queued_jobs": jobs.queue.maxsize,
                "synthesis_concurrency": 1, "cpu_threads": threads,
                "sample_rate": 24000, "format": "WAV PCM16 mono", "retention_days": 7}

    @app.post("/v1/jobs", status_code=202, dependencies=[Depends(authorize)])
    async def submit(request: SpeechRequest):
        return app.state.jobs.submit(request)

    @app.get("/v1/jobs/{job_id}", dependencies=[Depends(authorize)])
    def get_job(job_id: str):
        record = app.state.jobs.records.get(job_id)
        if record is None:
            raise HTTPException(404, "Unknown or expired job.")
        return dict(record)

    @app.get("/v1/jobs/{job_id}/audio", dependencies=[Depends(authorize)])
    def get_audio(job_id: str):
        jobs = app.state.jobs
        record = jobs.records.get(job_id)
        if record is None:
            raise HTTPException(404, "Unknown or expired job.")
        if record["status"] != "completed":
            raise HTTPException(409, "Audio is not completed.")
        file = jobs.root / (record["id"] + ".wav")
        if not file.is_file():
            raise HTTPException(404, "Audio has expired.")
        return FileResponse(file, media_type="audio/wav", filename=record["id"] + ".wav")

    return app


app = create_app()
