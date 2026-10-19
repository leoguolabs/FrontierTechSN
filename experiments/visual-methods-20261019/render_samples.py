"""Re-render samples using the isolated dependencies described in README.md."""

from pathlib import Path
import argparse
import os
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = ROOT / "outputs" / BASE.name
NAMES = ["lemo", "hyperframes", "shotcraft", "remotion", "bits", "motion"]


def run(args, cwd=ROOT, env=None):
    subprocess.run([str(a) for a in args], cwd=cwd, env=env, check=True)


def audio():
    folder = OUT / "audio"
    folder.mkdir(parents=True, exist_ok=True)
    sentences = [
        (0.6, "An AI model can give you an answer."),
        (6.3, "An agent can take the next step."),
        (12.1, "It reads a goal, uses a tool, and checks the result."),
        (18.1, "Then it tries again. Action. Feedback. Correction."),
    ]
    inputs, filters = [], []
    for i, (offset, text) in enumerate(sentences):
        path = folder / f"{i + 1:02}.aiff"
        run(["say", "-v", "Daniel", "-r", "175", "-o", path, text])
        inputs += ["-i", path]
        delay = round(offset * 1000)
        filters.append(f"[{i}:a]aresample=48000,adelay={delay}|{delay}[a{i}]")
    filters.append(
        "[a0][a1][a2][a3]amix=inputs=4:normalize=0,apad,atrim=0:24,loudnorm=I=-17:TP=-2:LRA=7[out]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-ar",
            "48000",
            folder / "narration.wav",
        ]
    )


def render(name, chrome):
    if name == "motion":
        # Export via the native Motion Canvas UI first. This script only muxes it.
        return OUT / "motion-export/agent-loop.mp4"
    silent = OUT / f"{name}-silent.mp4"
    if name == "lemo":
        env = dict(os.environ, PLAYWRIGHT_CHROME=chrome)
        run(
            [
                "node",
                OUT / "vendor/lemo-opuscar/core/render/video.mjs",
                BASE / "lemo",
                "--fps",
                "24",
                "--workers",
                "2",
                "--out",
                silent,
            ],
            env=env,
        )
    elif name == "hyperframes":
        run(
            [
                ROOT / "hyperframe/node_modules/.bin/hyperframes",
                "render",
                BASE / "hyperframes",
                "--fps",
                "24",
                "--workers",
                "2",
                "--output",
                silent,
            ]
        )
    else:
        if name == "shotcraft":
            run(["python", BASE / "prepare_shotcraft.py"])
        composition = {
            "shotcraft": "Shotcraft",
            "remotion": "RemotionCore",
            "bits": "RemotionBits",
        }[name]
        run(
            [
                "node_modules/.bin/remotion",
                "render",
                "index.tsx",
                composition,
                silent,
                "--concurrency=1",
                "--timeout=120000",
                "--chrome-mode=chrome-for-testing",
                f"--browser-executable={chrome}",
            ],
            cwd=BASE / "react",
        )
    return silent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("methods", nargs="*", choices=NAMES)
    parser.add_argument(
        "--audio", action="store_true", help="Regenerate the common macOS Daniel voice"
    )
    parser.add_argument("--mux-only", action="store_true")
    parser.add_argument("--chrome", default=os.environ.get("PLAYWRIGHT_CHROME"))
    args = parser.parse_args()
    if not args.mux_only and not args.chrome:
        parser.error(
            "Set PLAYWRIGHT_CHROME or --chrome to a compatible installed Chromium executable"
        )
    if args.audio:
        audio()
    (OUT / "final").mkdir(exist_ok=True)
    for method in args.methods or NAMES:
        silent = (
            (
                OUT / "motion-export/agent-loop.mp4"
                if method == "motion"
                else OUT / f"{method}-silent.mp4"
            )
            if args.mux_only
            else render(method, args.chrome)
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                silent,
                "-i",
                OUT / "audio/narration.wav",
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                "24",
                "-movflags",
                "+faststart",
                OUT / "final" / f"{method}.mp4",
            ]
        )
