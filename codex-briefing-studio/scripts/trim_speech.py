#!/usr/bin/env python3
"""Retain an exact PCM prefix as a candidate; adoption still requires fresh ASR."""
import argparse
import hashlib
import json
from pathlib import Path
import wave

from speech import write

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    parser.add_argument("--end", type=float, required=True)
    args = parser.parse_args()
    rows = json.loads((ROOT / "media/audio/manifest.json").read_text())
    source = next(row for row in rows if row["id"] == args.id)
    path = ROOT / source["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["audio_sha256"]:
        raise ValueError("Source WAV changed")
    with wave.open(str(path)) as original:
        params = original.getparams()
        frames = round(args.end * params.framerate)
        if not 0 < frames < params.nframes:
            raise ValueError("Trim must retain a nonempty prefix shorter than the original")
        pcm = original.readframes(frames)
    directory = ROOT / "media/candidates" / f"{args.id}-trim-{frames}"
    directory.mkdir(parents=True, exist_ok=True)
    identity = hashlib.sha256(
        f"{source['audio_sha256']}:pcm-prefix:{frames}".encode()
    ).hexdigest()
    output = directory / f"{args.id}-{identity[:12]}.wav"
    with wave.open(str(output), "wb") as target:
        target.setparams(params)
        target.writeframes(pcm)
    candidate = dict(source, path=str(output.relative_to(ROOT)),
                     duration=frames/params.framerate, identity=identity,
                     audio_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                     derived_from={
                         "path": source["path"], "audio_sha256": source["audio_sha256"],
                         "job_id": source["job_id"], "operation": "exact_pcm_prefix",
                         "retained_frames": frames, "sample_rate": params.framerate,
                     })
    write(directory / "manifest.json", [candidate])
    print(directory / "manifest.json")


if __name__ == "__main__":
    main()
