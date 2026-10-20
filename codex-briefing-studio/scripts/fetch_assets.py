#!/usr/bin/env python3
"""Fetch credited public assets without any account or browser session."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    ("reference/briefing-board.mp4",
     "https://github.com/lemomo-ai/lemo-opuscar/releases/download/films/briefing-board.mp4",
     "cf09a6db65a100fc877d4e7ffee8113aee642e6056822ad2055a48189f7a80cc"),
    ("assets/photos/notebook.jpg",
     "https://images.unsplash.com/photo-1483546416237-76fd26bbcdd1?w=5184&q=95&fm=jpg&fit=max", None),
]

if __name__ == "__main__":
    manifest = []
    for name, url, expected in ASSETS:
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "BriefingStudio/1.0"})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if expected and hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f"Reference asset changed: {name}")
            target.write_bytes(data)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if expected and digest != expected:
            raise ValueError(f"Local reference asset changed: {name}")
        manifest.append({"path": name, "url": url, "sha256": digest, "bytes": target.stat().st_size})
    (ROOT / "assets/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Credited assets verified.")
