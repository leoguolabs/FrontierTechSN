#!/usr/bin/env python3
"""Copy a reviewable local production without dependencies or private task data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError("Export outside the authoring folder.")
    marker = destination/"export-receipt.json"
    if destination.exists() and any(destination.iterdir()) and not marker.exists():
        raise ValueError("Destination contains unrelated files; choose an empty folder.")
    technical = json.loads((ROOT/"review/technical-delivery.json").read_text())
    review = json.loads((ROOT/"review/delivery.json").read_text())
    video = ROOT/"media/does-ai-help-you-learn-3min.mp4"
    sha = digest(video)
    if not technical["checks_passed"] or technical["video_sha256"] != sha:
        raise ValueError("Current encoded video has not passed technical verification.")
    if review["video_sha256"] != sha or not review["complete_frame_review"]:
        raise ValueError("Current encoded video lacks complete frame review.")

    files = []
    for pattern in ["*.md", "*.html", "*.css", "*.mjs", "*.json", "*.txt", ".gitignore"]:
        files.extend(p for p in ROOT.glob(pattern) if p.is_file())
    for folder in ["src", "scripts", "content", "fonts", "assets", "article"]:
        files.extend(p for p in (ROOT/folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    files.extend(p for p in (ROOT/"review").glob("*") if p.is_file())
    for folder in ["reference", "candidate", "comparison", "final-stills"]:
        files.extend(p for p in (ROOT/"review"/folder).rglob("*") if p.is_file())
    files.extend(p for p in (ROOT/"media/audio").rglob("*") if p.is_file())
    files.extend(p for p in (ROOT/"media/asr").rglob("*") if p.is_file())
    for name in [
        "does-ai-help-you-learn-3min.mp4", "poster.jpg", "captions.srt", "captions.vtt",
        "timeline.json", "events.json", "delivery-timeline.json", "audio-mix-provenance.json",
        "loudness-first-pass.json", "picture-v1.mp4.render.json", "mix-master.wav",
    ]:
        files.append(ROOT/"media"/name)
    files.append(ROOT/"reference/whiteboard.mp4")
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for source in sorted(set(files)):
        relative = source.relative_to(ROOT)
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        source_hash = digest(source)
        if digest(target) != source_hash:
            raise IOError(f"Export hash mismatch: {relative}")
        records.append({"path": str(relative), "bytes": source.stat().st_size,
                        "sha256": source_hash})
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "src/film.mjs"],
        capture_output=True, text=True, check=False)
    revision, dirty = None, None
    if tracked.returncode == 0:
        revision = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--", "."],
            capture_output=True, text=True, check=True).stdout.strip())
    receipt = {"project": "Codex Whiteboard Studio", "video_sha256": sha,
               "source_git_commit": revision, "source_git_dirty": dirty,
               "files": records, "total_bytes": sum(r["bytes"] for r in records),
               "excluded": ["node_modules", "private original-task project data",
                            "credentials", "development renders", "Git repository"]}
    marker.write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps({"destination": str(destination), "files": len(records),
                      "total_bytes": receipt["total_bytes"], "video_sha256": sha}))


if __name__ == "__main__":
    main()
