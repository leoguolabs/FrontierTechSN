#!/usr/bin/env python3
"""Build from reviewed local inputs. Network speech generation is explicit."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    print("\n"+ " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=ROOT, check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--speech", action="store_true", help="Generate or resume provider audio before building.")
    p.add_argument("--frontier-config", action="store_true", help="Read only the parent app's Chatterbox credentials.")
    p.add_argument("--skip-atlases", action="store_true", help="Skip evidence generation, never mark visual review complete.")
    args = p.parse_args()
    python = sys.executable
    if args.speech:
        run(python, "scripts/speech.py", *(["--frontier-config"] if args.frontier_config else []))
        run(python, "scripts/transcribe.py")
    run("node", "scripts/validate.mjs")
    run("node", "scripts/render.mjs")
    run(python, "scripts/mix_audio.py")
    run(python, "scripts/export_metadata.py")
    run(python, "scripts/verify_delivery.py")
    run(python, "scripts/review_stills.py")
    if not args.skip_atlases:
        run(python, "scripts/analyze_frames.py", "media/does-ai-help-you-learn-3min.mp4",
            "--out", "review/candidate")
        run(python, "scripts/compare_frames.py", "media/does-ai-help-you-learn-3min.mp4",
            "--candidate-analysis", "review/candidate", "--out", "review/comparison")
    print("\nBuild complete. Visual inspection and playback review remain separate human/agent review steps.")


if __name__ == "__main__":
    main()
