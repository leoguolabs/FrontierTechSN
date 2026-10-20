#!/usr/bin/env python3
"""Adopt an isolated speech repair after an independent exact-content check."""
import argparse
import json
from pathlib import Path

from check_speech import inspect
from speech import write

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_manifest", type=Path)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    path = ROOT / "media/audio/manifest.json"
    manifest = json.loads(path.read_text())
    source = json.loads((ROOT / "content/narration.json").read_text())
    if len(manifest) != len(source):
        raise SystemExit("Wait for the initial speech run to finish before adopting repairs.")
    candidates = json.loads(args.candidate_manifest.read_text())
    override_path = ROOT / "media/audio/accepted-overrides.json"
    overrides = json.loads(override_path.read_text()) if override_path.exists() else {}
    original_path = ROOT / "media/audio/manifest-before-repairs.json"
    if not original_path.exists():
        write(original_path, manifest)
    for row in candidates:
        original = next(item for item in manifest if item["id"] == row["id"])
        if row["text"] != original["text"]:
            raise ValueError("A content change is not an interchangeable speech repair.")
        observation = inspect(row)
        if observation["differences"]:
            raise ValueError(f"Candidate still differs: {row['id']}")
        base = overrides.get(row["id"], {}).get("base_identity", original["identity"])
        overrides[row["id"]] = {
            "base_identity": base,
            "record": row,
            "reason": args.reason,
            "superseded_audio_sha256": original["audio_sha256"],
            "verification": {
                "model": observation["model"],
                "audio_sha256": observation["audio_sha256"],
                "differences": observation["differences"],
            },
        }
        manifest[manifest.index(original)] = row
    write(override_path, overrides)
    write(path, manifest)
    print("Adopted verified candidates; original files and requests retained.")


if __name__ == "__main__":
    main()
