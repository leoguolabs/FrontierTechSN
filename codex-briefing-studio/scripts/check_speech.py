#!/usr/bin/env python3
"""Observe provider WAVs with an unprompted recognizer; retain every observation."""
import argparse
import hashlib
import json
import re
import time
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "mlx-community/whisper-large-v3-turbo-q4"


def tokens(text):
    text = text.lower().replace("48", "forty eight").replace("17", "seventeen")
    text = text.replace("%", " percent").replace("practise", "practice")
    return re.findall(r"[a-z]+", text)


def inspect(row):
    import mlx_whisper
    source = ROOT / row["path"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != row["audio_sha256"]:
        raise RuntimeError(f"Changed audio for {row['id']}")
    cache = ROOT / "media/asr" / f"{row['id']}-{digest[:16]}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    result = mlx_whisper.transcribe(
        str(source), path_or_hf_repo=MODEL, language="en", word_timestamps=True,
        initial_prompt=None, condition_on_previous_text=False, temperature=0,
        verbose=False,
    )
    expected, actual = tokens(row["text"]), tokens(result["text"])
    changes = [
        {"type": op, "source": expected[a:b], "recognized": actual[c:d]}
        for op, a, b, c, d in SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes()
        if op != "equal"
    ]
    observation = {
        "id": row["id"], "model": MODEL, "audio_sha256": digest,
        "source": row["text"], "recognized": result["text"],
        "differences": changes,
        "words": [word for segment in result["segments"] for word in segment.get("words", [])],
        "quality_scope": "Automated transcription; not a claim of perceptual listening.",
    }
    cache.write_text(json.dumps(observation, indent=2) + "\n")
    print(json.dumps({"id": row["id"], "recognized": result["text"], "differences": changes}), flush=True)
    return observation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--follow", action="store_true")
    args = parser.parse_args()
    (ROOT / "media/asr").mkdir(parents=True, exist_ok=True)
    count = len(json.loads((ROOT / "content/narration.json").read_text()))
    while True:
        rows = json.loads((ROOT / "media/audio/manifest.json").read_text())
        observations = [inspect(row) for row in rows]
        temp = ROOT / "media/asr/observations.tmp"
        temp.write_text(json.dumps(observations, indent=2) + "\n")
        temp.replace(ROOT / "media/asr/observations.json")
        if not args.follow or len(rows) == count:
            break
        time.sleep(15)


if __name__ == "__main__":
    main()
