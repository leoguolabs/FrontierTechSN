#!/usr/bin/env python3
"""Check the actual encoded delivery, separately from visual and listening review."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video", nargs="?", type=Path, default=Path("media/does-ai-help-you-learn.mp4"))
    parser.add_argument("--report", default="review/delivery-check.json")
    args = parser.parse_args()
    video = ROOT / args.video
    timeline = json.loads((ROOT / "content/timeline.json").read_text())
    info = json.loads(run(
        "ffprobe", "-v", "error", "-count_frames", "-show_streams",
        "-show_format", "-of", "json", str(video),
    ).stdout)
    picture = next(s for s in info["streams"] if s["codec_type"] == "video")
    sound = next(s for s in info["streams"] if s["codec_type"] == "audio")
    run("ffmpeg", "-v", "error", "-xerror", "-err_detect", "explode",
        "-i", str(video), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-")
    frames = json.loads(run(
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(video),
    ).stdout)["frames"]
    times = [float(f["best_effort_timestamp_time"]) for f in frames]
    cadence_error = max(abs(t-times[0]-i/timeline["fps"]) for i, t in enumerate(times))
    result = run(
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
        "-map", "0:a:0", "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-",
    )
    loudness = json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind("{"):])[0]
    checks = {
        "full_decode": True,
        "frame_count": len(times) == int(picture["nb_read_frames"]) == timeline["duration_frames"],
        "frame_rate": float(Fraction(picture["avg_frame_rate"])) == timeline["fps"],
        "timestamp_cadence": cadence_error <= float(Fraction(picture["time_base"])) + .000002,
        "dimensions": (picture["width"], picture["height"]) == (1920, 1080),
        "video_encoding": picture["codec_name"] == "h264" and picture["pix_fmt"] == "yuv420p",
        "audio_encoding": sound["codec_name"] == "aac" and int(sound["sample_rate"]) == 48000,
        "duration": abs(float(picture["duration"])-timeline["duration_frames"]/timeline["fps"]) < 1/24,
        "audio_video_duration": abs(float(picture["duration"])-float(sound["duration"])) < .05,
        "loudness": -17 <= float(loudness["input_i"]) <= -15,
        "true_peak": float(loudness["input_tp"]) <= -1,
    }
    report = {
        "file": str(video.relative_to(ROOT)),
        "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "decoded_frames": len(times),
        "max_timestamp_error_seconds": cadence_error,
        "audio_measurement": {key: loudness[key] for key in ("input_i", "input_tp", "input_lra")},
        "streams": info["streams"],
        "scope": "Encoded technical checks; visual review and perceptual listening are separate.",
    }
    (ROOT / args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "decoded_frames", "audio_measurement")}))
    if not report["passed"]:
        raise SystemExit("Failed: " + ", ".join(k for k, value in checks.items() if not value))


if __name__ == "__main__":
    main()
