#!/usr/bin/env python3
"""Record only atlases actually inspected; invalidate records when media changes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numbers(value):
    result = set()
    for item in value.split(","):
        bounds = list(map(int, item.split("-")))
        if len(bounds) > 2 or bounds[-1] < bounds[0]:
            raise ValueError(f"Invalid inspection range: {item}")
        result.update(range(bounds[0], bounds[-1]+1))
    return sorted(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheets", help="Inspected zero-based sheets, e.g. 0-3,8")
    parser.add_argument("--stills", help="Inspected one-based final stills, e.g. 1-19")
    parser.add_argument("--note", default="")
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    movie = ROOT/"media/does-ai-help-you-learn-3min.mp4"
    binding = {"video_sha256": sha(movie),
               "reference_sha256": sha(ROOT/"reference/whiteboard.mp4"),
               "mapping_sha256": sha(ROOT/"review/comparison/pairs.csv")}
    ledger_path = ROOT/"review/visual-ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
        **binding, "reviewer": "Codex visual inspection",
        "method": "Every consecutive paired atlas; 320x180 generated tiles. "
                  "Full-resolution inspection is separately listed.",
        "sheets": {}, "full_resolution_stills": []}
    if any(ledger[k] != value for k, value in binding.items()):
        raise ValueError("Media or pairing changed. Archive the old ledger before a new review.")
    comparison = json.loads((ROOT/"review/comparison/comparison.json").read_text())
    if (comparison["candidate_sha256"] != binding["video_sha256"]
            or comparison["reference_sha256"] != binding["reference_sha256"]):
        raise ValueError("Comparison atlases belong to different media.")
    index = comparison["atlases"]
    cursor = 0
    for entry in index:
        if entry["first"] != cursor or entry["last"] < entry["first"]:
            raise ValueError("Atlas coverage is not contiguous.")
        cursor = entry["last"]+1
    if cursor != comparison["candidate_frames"]:
        raise ValueError("Atlas coverage does not include every candidate frame.")
    if args.sheets:
        for number in numbers(args.sheets):
            if number < 0 or number >= len(index):
                raise ValueError(f"Unknown atlas {number}")
            entry = index[number]
            path = ROOT/"review/comparison/contact-sheets"/entry["file"]
            ledger["sheets"][str(number)] = {
                **entry, "sha256": sha(path), "observation": args.note,
                "recorded_at": datetime.now(timezone.utc).isoformat()}
    if args.stills:
        still_index = json.loads((ROOT/"review/final-stills/index.json").read_text())
        if still_index["video_sha256"] != binding["video_sha256"]:
            raise ValueError("Full-resolution stills belong to another video.")
        recorded = {entry["file"]: entry for entry in ledger["full_resolution_stills"]}
        for number in numbers(args.stills):
            if number < 1 or number > len(still_index["stills"]):
                raise ValueError(f"Unknown full-resolution still {number}")
            entry = still_index["stills"][number-1]
            if sha(ROOT/"review/final-stills"/entry["file"]) != entry["sha256"]:
                raise ValueError(f"Full-resolution still changed: {number}")
            recorded[entry["file"]] = {
                **entry, "observation": args.note,
                "recorded_at": datetime.now(timezone.utc).isoformat()}
        ledger["full_resolution_stills"] = sorted(recorded.values(), key=lambda e: e["frame"])
    if args.sheets or args.stills:
        ledger_path.write_text(json.dumps(ledger, indent=2)+"\n")
    inspected = len(ledger["sheets"])
    print(f"Recorded actual visual inspection: {inspected}/{len(index)} paired atlases.")
    if args.finalize:
        if set(ledger["sheets"]) != {str(i) for i in range(len(index))}:
            raise ValueError("Unreviewed atlases remain.")
        for number, recorded in ledger["sheets"].items():
            path = ROOT/"review/comparison/contact-sheets"/recorded["file"]
            if sha(path) != recorded["sha256"]:
                raise ValueError(f"Atlas changed after inspection: {number}")
        for recorded in ledger["full_resolution_stills"]:
            path = ROOT/"review/final-stills"/recorded["file"]
            if sha(path) != recorded["sha256"]:
                raise ValueError(f"Full-resolution still changed: {recorded['file']}")
        technical = json.loads((ROOT/"review/technical-delivery.json").read_text())
        if not technical["checks_passed"] or technical["video_sha256"] != binding["video_sha256"]:
            raise ValueError("Technical delivery checks do not match this video.")
        if technical["decoded_frames"] != cursor:
            raise ValueError("Technical and visual frame counts differ.")
        delivery = {
            **binding, "status_label": "Frame review complete",
            "decoded_frames": technical["decoded_frames"],
            "duration": technical["duration"], "fps": 24,
            "complete_frame_review": True, "paired_atlases_inspected": inspected,
            "full_resolution_stills_inspected": len(ledger["full_resolution_stills"]),
            "reference_frames_reviewed": 2664,
            "scope": ledger["method"],
            "visual_judgment": "See visual-review.md for observations and remaining stylistic differences.",
            "pixel_identity_claimed": False,
            "audio_evidence": "Independent transcription, provider bindings, final-mix waveform placement "
                              "and loudness checks; subjective listening is not established.",
            "user_approval": "Pending short-edition review; long edition not started.",
            "publication": "Process article prepared locally; not published."
        }
        (ROOT/"review/delivery.json").write_text(json.dumps(delivery, indent=2)+"\n")


if __name__ == "__main__":
    main()
