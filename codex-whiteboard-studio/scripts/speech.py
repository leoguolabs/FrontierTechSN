#!/usr/bin/env python3
"""Direct, resumable Chatterbox client. No project tasks or pipeline imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    if not isinstance(data, bytes):
        data = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def save(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-config", action="store_true",
                        help="Read the parent app's existing service credentials only.")
    parser.add_argument("--only", help="Comma-separated line IDs for a bounded repair; preserve other manifest rows.")
    args = parser.parse_args()
    url = os.environ.get("CHATTERBOX_TTS_URL", "")
    key = os.environ.get("CHATTERBOX_TTS_API_KEY", "")
    if args.frontier_config:
        sys.path.insert(0, str(ROOT.parent))
        from backend import config
        url, key = config.CHATTERBOX_TTS_URL, config.CHATTERBOX_TTS_API_KEY
    if not url:
        raise SystemExit("Set CHATTERBOX_TTS_URL or use --frontier-config.")
    directory = ROOT / "media/audio"
    directory.mkdir(parents=True, exist_ok=True)
    lines = json.loads((ROOT / "content/narration.json").read_text())

    def request(path, payload=None, idem=None, binary=False):
        headers = {"X-API-Key": key}
        if idem:
            headers["Idempotency-Key"] = idem
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode()
        req = urllib.request.Request(url.rstrip("/") + path, body, headers)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    raw = response.read()
                return raw if binary else json.loads(raw)
            except (urllib.error.URLError, TimeoutError):
                if attempt == 4:
                    raise
                time.sleep(3 * (attempt + 1))

    cap = request("/v1/capabilities")
    save(directory / "capabilities.json", cap)
    voice = "space-en-f1"
    voice_info = next(v for v in cap["voices"] if v["id"] == voice)
    manifest_path = directory / "manifest.json"
    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    manifest = {row["id"]: row for row in existing}
    selected = set(args.only.split(",")) if args.only else {line["id"] for line in lines}
    if selected - {line["id"] for line in lines}:
        raise ValueError("Unknown line selected for repair.")
    for index, line in enumerate(lines):
        if line["id"] not in selected:
            continue
        if len(line["text"]) > cap["max_chars"]:
            raise ValueError(f"Line {line['id']} exceeds the service's character bound.")
        payload = {
            "text": line["text"], "language_id": "en", "voice": voice,
            "seed": 220 + index, "exaggeration": 0.5, "cfg_weight": 0.5,
            "temperature": 0.8, "repetition_penalty": 2.0,
            "min_p": 0.05, "top_p": 1.0, "speed": 1.0,
        }
        binding = {"payload": payload, "deployment": cap["fingerprint"],
                   "voice": voice_info["fingerprint"]}
        identity = digest(binding)
        stem = f"{line['id']}-{identity[:12]}"
        checkpoint_path = directory / f"{stem}.request.json"
        checkpoint = (json.loads(checkpoint_path.read_text()) if checkpoint_path.exists()
                      else {"identity": identity, "idempotency_key": f"codex-whiteboard-{identity}",
                            "source_sha256": digest(line["text"].encode()), "binding": binding})
        if checkpoint["identity"] != identity:
            raise ValueError("Checkpoint identity mismatch.")
        save(checkpoint_path, checkpoint)
        if "job_id" not in checkpoint:
            job = request("/v1/jobs", payload, checkpoint["idempotency_key"])
            checkpoint["job_id"] = job["id"]
            save(checkpoint_path, checkpoint)
        jid = checkpoint["job_id"]
        print(f"Line {line['id']}: following {jid}", flush=True)
        previous = None
        while True:
            job = request(f"/v1/jobs/{jid}")
            state = job["status"]
            if state != previous:
                print(f"Line {line['id']}: {state}", flush=True)
                previous = state
                save(directory / f"{stem}.job.json", job)
            if state == "failed":
                raise RuntimeError(f"Retained failed job {jid}: {job.get('error')}")
            if state == "completed":
                break
            if state not in {"queued", "running"}:
                raise RuntimeError(f"Unknown job status {state}")
            time.sleep(5)
        if job.get("request") != payload:
            raise RuntimeError("Completed job is not bound to the exact request.")
        if job.get("voice_fingerprint") != voice_info["fingerprint"]:
            raise RuntimeError("Completed job voice fingerprint changed.")
        path = directory / f"{stem}.wav"
        if not path.exists() or digest(path.read_bytes()) != job["audio_sha256"]:
            data = request(f"/v1/jobs/{jid}/audio", binary=True)
            if digest(data) != job["audio_sha256"]:
                raise RuntimeError("Provider audio hash mismatch.")
            path.write_bytes(data)
        with wave.open(str(path)) as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 24000):
                raise ValueError("Unexpected provider WAV format.")
            duration = wav.getnframes() / wav.getframerate()
        manifest[line["id"]] = {**line, "path": str(path.relative_to(ROOT)),
                         "duration": duration, "job_id": jid,
                         "audio_sha256": job["audio_sha256"],
                         "source_sha256": checkpoint["source_sha256"],
                         "voice": voice, "speed": 1.0}
        save(manifest_path, [manifest[n["id"]] for n in lines if n["id"] in manifest])
        print(f"Line {line['id']}: retained {duration:.2f}s WAV; ASR/listening pending.", flush=True)
    print("All requested provider WAVs downloaded; audio review is still required.", flush=True)


if __name__ == "__main__":
    main()
