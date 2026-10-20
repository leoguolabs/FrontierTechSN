#!/usr/bin/env python3
"""Measure an isolated, pinned Chatterbox MPS runtime without accepting its audio."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import signal
import sys
import time

STUDIO = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--line", default="52")
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    os.environ["HF_HOME"] = str(runtime / "cache/huggingface")
    os.environ["PKUSEG_HOME"] = str(runtime / "cache/pkuseg")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    sys.path.insert(0, str(runtime))

    from prefetch_models import FILES, REVISION, valid_file
    from prefetch_reference import verify_reference
    from apply_space_alignment import verify_patch

    snapshot = runtime / "cache/huggingface/hub/models--ResembleAI--chatterbox/snapshots" / REVISION
    for entry in FILES:
        if not valid_file(snapshot / entry["name"], entry):
            raise ValueError(f"Unverified model file: {entry['name']}")
    voice = runtime / "voices/en_f1.flac"
    verify_reference(voice)
    patch = verify_patch()
    source = json.loads(importlib.metadata.distribution("chatterbox-tts").read_text("direct_url.json"))
    if source.get("vcs_info", {}).get("commit_id") != "5de7a54aa4e5e2baadb0182dde554908b48b85c2":
        raise ValueError("The benchmark requires the same pinned upstream source as the service.")

    import numpy as np
    import soundfile as sf
    import torch
    from service import Settings, _load_model

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable.")
    rows = json.loads((STUDIO / "editions/long/content/narration.json").read_text())
    index, row = next((i, r) for i, r in enumerate(rows) if r["id"] == args.line)
    request = {
        "text": row["text"], "language_id": "en", "voice": "space-en-f1",
        "seed": 220 + index, "exaggeration": 0.5, "cfg_weight": 0.5,
        "temperature": 0.8, "repetition_penalty": 2.0, "min_p": 0.05,
        "top_p": 1.0, "speed": 1.0,
    }
    if len(row["text"]) > 250:
        raise ValueError("Benchmark source exceeds the existing service's request bound.")
    destination = runtime / "benchmark"
    destination.mkdir(exist_ok=True)
    record_path = destination / f"{row['id']}.json"
    wav_path = destination / f"{row['id']}.wav"
    if record_path.exists() or wav_path.exists():
        raise FileExistsError("Retain the previous benchmark; choose a fresh runtime directory.")
    record = {
        "status": "initializing", "device": "mps",
        "scope": "Isolated local speed and output experiment. No production manifest changes or subjective listening claim.",
        "request": request, "source_sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
        "upstream_source": source, "model_revision": REVISION,
        "model_files": FILES, "reference_sha256": digest(voice),
        "space_alignment": patch, "loader_sha256": digest(runtime / "service.py"),
        "mps_fallback_enabled": True, "cpu_threads": 4,
    }

    def save():
        record_path.write_text(json.dumps(record, indent=2) + "\n")

    def expired(*_):
        raise TimeoutError("Bounded local acceleration experiment exceeded five minutes.")

    save()
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(300)
    try:
        settings = Settings(api_key="", data_dir=destination, device="mps", cpu_threads=4)
        started = time.monotonic()
        model = _load_model(settings)
        torch.mps.synchronize()
        record["initialization_seconds"] = time.monotonic() - started
        record["backbone_device"] = str(next(model.t3.parameters()).device)
        if not record["backbone_device"].startswith("mps"):
            raise RuntimeError("The backbone was not loaded on MPS.")
        record["status"] = "generating"
        save()
        print(json.dumps({"status": "generating", "initialization_seconds": record["initialization_seconds"]}), flush=True)
        random.seed(request["seed"])
        np.random.seed(request["seed"])
        torch.manual_seed(request["seed"])
        kwargs = {key: request[key] for key in (
            "language_id", "exaggeration", "cfg_weight", "temperature",
            "repetition_penalty", "min_p", "top_p",
        )}
        started = time.monotonic()
        with torch.inference_mode():
            samples = model.generate(request["text"], audio_prompt_path=str(voice), **kwargs)
        torch.mps.synchronize()
        record["generation_seconds"] = time.monotonic() - started
        samples = samples.detach().cpu().numpy().reshape(-1)
        if not len(samples) or not np.isfinite(samples).all():
            raise ValueError("Empty or nonfinite synthesis output.")
        sf.write(wav_path, samples, model.sr, subtype="PCM_16", format="WAV")
        record.update({
            "status": "generated_not_accepted", "audio_sha256": digest(wav_path),
            "sample_rate": model.sr, "duration": len(samples) / model.sr,
            "generation_seconds_per_audio_second": record["generation_seconds"] / (len(samples) / model.sr),
            "torch_version": torch.__version__,
        })
        save()
        print(json.dumps({key: record[key] for key in (
            "status", "duration", "generation_seconds", "generation_seconds_per_audio_second",
        )}), flush=True)
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        save()
        raise
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
