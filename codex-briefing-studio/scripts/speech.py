#!/usr/bin/env python3
"""Submit exact narration directly to Chatterbox, retaining resumable job identity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]


def sha(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-config", action="store_true")
    parser.add_argument("--only", help="Generate one narration ID into an isolated candidate folder")
    parser.add_argument("--seed-offset", type=int, default=0)
    args = parser.parse_args()
    endpoint = os.getenv("CHATTERBOX_TTS_URL", "")
    secret = os.getenv("CHATTERBOX_TTS_API_KEY", "")
    if args.frontier_config:
        sys.path.insert(0, str(ROOT.parent))
        from backend import config
        endpoint, secret = config.CHATTERBOX_TTS_URL, config.CHATTERBOX_TTS_API_KEY
    if not endpoint:
        raise SystemExit("Supply CHATTERBOX_TTS_URL or --frontier-config.")

    def request(route, payload=None, key=None, raw=False):
        headers = {"X-API-Key": secret}
        if key:
            headers["Idempotency-Key"] = key
        body = None if payload is None else json.dumps(payload).encode()
        if body:
            headers["Content-Type"] = "application/json"
        for attempt in range(4):
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(endpoint.rstrip("/") + route, body, headers), timeout=45
                ) as response:
                    result = response.read()
                return result if raw else json.loads(result)
            except (OSError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(3 * (attempt + 1))

    directory = ROOT / "media/audio"
    if args.only:
        directory = ROOT / "media/candidates" / f"{args.only}-seed-{args.seed_offset}"
    directory.mkdir(parents=True, exist_ok=True)
    capabilities = request("/v1/capabilities")
    write(directory / "capabilities.json", capabilities)
    voice = next(v for v in capabilities["voices"] if v["id"] == "space-en-f1")
    lines = json.loads((ROOT / "content/narration.json").read_text())
    override_path = ROOT / "media/audio/accepted-overrides.json"
    overrides = json.loads(override_path.read_text()) if override_path.exists() else {}
    manifest = []
    for i, line in enumerate(lines):
        if args.only and line["id"] != args.only:
            continue
        payload = dict(text=line["text"], language_id="en", voice=voice["id"],
                       seed=510 + i + args.seed_offset, exaggeration=0.5, cfg_weight=0.5, temperature=0.8,
                       repetition_penalty=2.0, min_p=0.05, top_p=1.0, speed=1.0)
        if len(payload["text"]) > capabilities["max_chars"]:
            raise ValueError("Narration exceeds provider limit")
        binding = dict(payload=payload, deployment=capabilities["fingerprint"],
                       voice=voice["fingerprint"])
        identity = sha(binding)
        checkpoint_path = directory / f'{line["id"]}-{identity[:12]}.json'
        checkpoint = (json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else
                      dict(identity=identity, binding=binding,
                           idempotency_key="codex-briefing-" + identity))
        write(checkpoint_path, checkpoint)
        if "job_id" not in checkpoint:
            checkpoint["job_id"] = request("/v1/jobs", payload, checkpoint["idempotency_key"])["id"]
            write(checkpoint_path, checkpoint)
        job_id = checkpoint["job_id"]
        print(f'{line["id"]}: following {job_id}', flush=True)
        last = None
        while True:
            job = request(f"/v1/jobs/{job_id}")
            if job["status"] != last:
                last = job["status"]
                print(f'{line["id"]}: {last}', flush=True)
                checkpoint["job"] = job
                write(checkpoint_path, checkpoint)
            if last == "completed":
                break
            if last not in {"queued", "running"}:
                raise RuntimeError(f"Job retained with status {last}: {job_id}")
            time.sleep(5)
        if job.get("request") != payload or job.get("voice_fingerprint") != voice["fingerprint"]:
            raise ValueError("Provider response identity mismatch")
        wav_path = directory / f'{line["id"]}-{identity[:12]}.wav'
        if not wav_path.exists() or sha(wav_path.read_bytes()) != job["audio_sha256"]:
            audio = request(f"/v1/jobs/{job_id}/audio", raw=True)
            if sha(audio) != job["audio_sha256"]:
                raise ValueError("Audio checksum mismatch")
            wav_path.write_bytes(audio)
        with wave.open(str(wav_path)) as wav:
            duration = wav.getnframes() / wav.getframerate()
        record = dict(**line, path=str(wav_path.relative_to(ROOT)),
                      duration=duration, job_id=job_id, identity=identity,
                      audio_sha256=job["audio_sha256"])
        accepted = overrides.get(line["id"]) if not args.only else None
        if accepted and accepted["base_identity"] == identity:
            replacement = accepted["record"]
            if replacement["text"] != line["text"]:
                raise ValueError("Accepted repair source changed")
            if sha((ROOT / replacement["path"]).read_bytes()) != replacement["audio_sha256"]:
                raise ValueError("Accepted repair audio changed")
            record = replacement
        manifest.append(record)
        write(directory / "manifest.json", manifest)
        print(f'{line["id"]}: {duration:.3f} seconds retained', flush=True)


if __name__ == "__main__":
    main()
