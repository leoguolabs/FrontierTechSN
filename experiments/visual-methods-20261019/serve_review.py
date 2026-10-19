"""Stage and serve only this experiment's review files on localhost."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import shutil
import subprocess

BASE = Path(__file__).resolve().parent
OUT = BASE.parents[1] / "outputs" / BASE.name


def stage():
    public = OUT / "review"
    public.mkdir(exist_ok=True)
    for source, target in [
        ("review.html", "index.html"),
        ("research.json", "research.json"),
        ("RESEARCH.md", "research.md"),
        ("narration.srt", "narration.srt"),
    ]:
        shutil.copy2(BASE / source, public / target)
    (public / "narration.vtt").write_text(
        "WEBVTT\n\n" + (BASE / "narration.srt").read_text().replace(",", ".")
    )
    (public / "media").mkdir(exist_ok=True)
    (public / "posters").mkdir(exist_ok=True)
    checks = {}
    for item in json.loads((BASE / "research.json").read_text()):
        name = item["id"]
        video = OUT / "final" / f"{name}.mp4"
        link = public / "media" / video.name
        if not link.exists():
            link.symlink_to(video)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-ss",
                "3",
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-vf",
                "scale=960:-1",
                str(public / "posters" / f"{name}.jpg"),
            ],
            check=True,
        )
        report = OUT / "qa" / name / "delivery-check.json"
        if report.exists():
            data = json.loads(report.read_text())
            checks[name] = {
                k: data[k]
                for k in (
                    "checks_passed",
                    "decoded_frames",
                    "fps",
                    "width",
                    "height",
                    "audio_present",
                    "audio_measurement",
                    "timeline_comparison",
                )
            }
    (public / "qa.json").write_text(json.dumps(checks, indent=2))
    return public


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9020)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    root = stage()
    if not args.stage_only:
        print(f"Review: http://127.0.0.1:{args.port}/", flush=True)
        ThreadingHTTPServer(
            ("127.0.0.1", args.port),
            partial(SimpleHTTPRequestHandler, directory=str(root)),
        ).serve_forever()
