#!/usr/bin/env python3
"""Decode every frame once, measure appearance/motion, and make gapless review atlases."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    out = ROOT / "review"
    atlas_dir = out / "atlases" / args.name
    atlas_dir.mkdir(parents=True, exist_ok=True)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(args.video)]))
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    numerator, denominator = map(int, v["r_frame_rate"].split("/"))
    fps = numerator / denominator
    width, height = 384, 216
    process = subprocess.Popen([
        "ffmpeg", "-v", "error", "-i", str(args.video), "-map", "0:v:0",
        "-vf", f"scale={width}:{height}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ], stdout=subprocess.PIPE)
    frame = 0
    previous = None
    atlas = None
    sheets = []
    with (out / f"{args.name}-frames.csv").open("w") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame", "seconds", "mean_r", "mean_g", "mean_b",
                         "dark_share", "blue_share", "red_share", "motion_mae"])
        while True:
            raw = process.stdout.read(width * height * 3)
            if not raw:
                break
            if len(raw) != width * height * 3:
                raise ValueError("Incomplete decoded frame")
            pixels = np.frombuffer(raw, np.uint8).reshape(height, width, 3)
            r, g, b = [pixels[:, :, n].astype(np.float32) for n in range(3)]
            motion = 0 if previous is None else float(np.abs(pixels.astype(float) - previous).mean())
            writer.writerow([frame, frame / fps, *pixels.mean((0, 1)).round(4),
                             float((pixels.mean(2) < 110).mean()),
                             float(((b > r * 1.12) & (b > g * 1.06)).mean()),
                             float(((r > g * 1.3) & (r > b * 1.25)).mean()), motion])
            previous = pixels.astype(float)
            slot = frame % 20
            if slot == 0:
                atlas = Image.new("RGB", (width * 4, (height + 23) * 5), "#20242a")
            x, y = (slot % 4) * width, (slot // 4) * (height + 23)
            atlas.paste(Image.fromarray(pixels), (x, y))
            ImageDraw.Draw(atlas).text((x + 8, y + height + 4),
                                      f"{frame:05d}   {frame / fps:07.3f}s", fill="white")
            frame += 1
            if slot == 19:
                name = f"{frame - 20:05d}-{frame - 1:05d}.jpg"
                atlas.save(atlas_dir / name, quality=91)
                sheets.append({"file": name, "first": frame - 20, "last": frame - 1})
        if frame % 20:
            first = frame - frame % 20
            name = f"{first:05d}-{frame - 1:05d}.jpg"
            atlas.save(atlas_dir / name, quality=91)
            sheets.append({"file": name, "first": first, "last": frame - 1})
    if process.wait():
        raise RuntimeError("Decode failed")
    report = dict(video=str(args.video), sha256=hashlib.sha256(args.video.read_bytes()).hexdigest(),
                  decoded_frames=frame, fps=fps, duration=frame / fps, stream=v,
                  automated_coverage=f"0..{frame-1}", atlas_cell=[width, height],
                  atlas_columns=4, atlas_rows=5, sheets=sheets,
                  visually_inspected_sheets=[], note="Generating atlases does not inspect them.")
    (out / f"{args.name}-analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["decoded_frames", "fps", "duration", "sha256"]}))


if __name__ == "__main__":
    main()
