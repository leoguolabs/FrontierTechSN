#!/usr/bin/env python3
"""Copy a reviewable local production without dependencies or private task data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from production import production

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def reviewed_video(project):
    technical = json.loads((project.root/"review/technical-delivery.json").read_text())
    review = json.loads((project.root/"review/delivery.json").read_text())
    sha = digest(project.video)
    if not technical["checks_passed"] or technical["video_sha256"] != sha:
        raise ValueError(f"{project.name}: current video has not passed technical verification.")
    if review["video_sha256"] != sha or not review["complete_frame_review"]:
        raise ValueError(f"{project.name}: current video lacks complete frame review.")
    return sha


def edition_files(project):
    root = project.root
    files = list(p for p in (root/"review").glob("*") if p.is_file())
    for folder in ["reference", "candidate", "comparison", "final-stills"]:
        files.extend(p for p in (root/"review"/folder).rglob("*") if p.is_file())
    for folder in ["audio", "asr"]:
        files.extend(p for p in (root/"media"/folder).rglob("*") if p.is_file())
    for name in [
        project.movie_name, "poster.jpg", "captions.srt", "captions.vtt",
        "timeline.json", "events.json", "delivery-timeline.json", "audio-mix-provenance.json",
        "loudness-first-pass.json", "picture-v1.mp4.render.json", "mix-master.wav",
    ]:
        files.append(root/"media"/name)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--include-long", action="store_true",
                        help="Include the long edition only after its complete delivery review.")
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError("Export outside the authoring folder.")
    marker = destination/"export-receipt.json"
    if destination.exists() and any(destination.iterdir()) and not marker.exists():
        raise ValueError("Destination contains unrelated files; choose an empty folder.")
    projects = [production("short")]
    if args.include_long:
        projects.append(production("long"))
    hashes = {project.name: reviewed_video(project) for project in projects}
    sha = hashes["short"]

    files = []
    for pattern in ["*.md", "*.html", "*.css", "*.mjs", "*.json", "*.txt", ".gitignore"]:
        files.extend(p for p in ROOT.glob(pattern) if p.is_file())
    for folder in ["src", "scripts", "content", "fonts", "assets", "article"]:
        files.extend(p for p in (ROOT/folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    for project in projects:
        files.extend(edition_files(project))
        if project.name != "short":
            files.extend(p for p in (project.root/"content").rglob("*") if p.is_file())
            files.extend(p for p in project.root.glob("*.md") if p.is_file())
            files.append(project.root/".gitignore")
    files.append(ROOT/"reference/whiteboard.mp4")
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for source in sorted(set(files)):
        relative = source.relative_to(ROOT)
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.exporting")
        shutil.copy2(source, temporary)
        source_hash = digest(source)
        if digest(temporary) != source_hash:
            raise IOError(f"Export hash mismatch: {relative}")
        temporary.replace(target)
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
               "edition_video_sha256": hashes,
               "source_git_commit": revision, "source_git_dirty": dirty,
               "files": records, "total_bytes": sum(r["bytes"] for r in records),
               "excluded": ["node_modules", "private original-task project data",
                            "credentials", "development renders", "Git repository"]}
    marker.write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps({"destination": str(destination), "files": len(records),
                      "total_bytes": receipt["total_bytes"], "video_sha256": sha}))


if __name__ == "__main__":
    main()
