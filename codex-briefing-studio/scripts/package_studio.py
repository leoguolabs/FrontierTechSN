#!/usr/bin/env python3
"""Build a portable local delivery without credentials or dependency caches."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "delivery"
    output.mkdir(exist_ok=True)
    files = set()
    for name in ("src", "scripts", "content", "article", "assets"):
        files.update(p for p in (ROOT / name).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    files.update(p for p in ROOT.iterdir()
                 if p.is_file() and (p.suffix in {".md", ".html", ".json"} or p.name in {".gitignore", "requirements.txt"}))
    files.update(p for p in (ROOT / "review").iterdir() if p.is_file())
    files.update(p for p in (ROOT / "review/revisions").rglob("*")
                 if p.is_file() and p.suffix in {".md", ".json"})
    for name in ("reference", "final", "paired"):
        files.update(p for p in (ROOT / "review/atlases" / name).rglob("*") if p.is_file())
    files.update(p for p in (ROOT / "review/final-stills").glob("*.png"))
    files.add(ROOT / "reference/briefing-board.mp4")
    for name in ("does-ai-help-you-learn.mp4", "poster.jpg", "captions.vtt", "captions.srt",
                 "audio/manifest.json", "audio/accepted-overrides.json", "asr/observations.json"):
        files.add(ROOT / "media" / name)
    for row in json.loads((ROOT / "media/audio/manifest.json").read_text()):
        files.add(ROOT / row["path"])
    for path in files:
        if not path.is_file():
            raise ValueError(f"Missing delivery file: {path.relative_to(ROOT)}")
    inventory = [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
    target = output / "briefing-studio.zip"
    with zipfile.ZipFile(target, "w") as archive:
        for path in sorted(files):
            archive.write(path, "briefing-studio/" + str(path.relative_to(ROOT)),
                          compress_type=zipfile.ZIP_STORED if path.suffix in {".mp4", ".jpg", ".png", ".ttf"}
                          else zipfile.ZIP_DEFLATED)
        archive.writestr("briefing-studio/delivery-manifest.json", json.dumps(inventory, indent=2))
    (output / "package.json").write_text(json.dumps({
        "file": str(target.relative_to(ROOT)),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "bytes": target.stat().st_size, "files": len(files),
        "scope": "Offline viewing and rerendering sources; no API keys, session data, or provider request checkpoints.",
    }, indent=2) + "\n")
    print(f"{target}: {len(files)} files, {target.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
