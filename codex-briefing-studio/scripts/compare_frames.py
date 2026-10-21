#!/usr/bin/env python3
"""Compare every encoded frame without pretending different stories share pixels."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "review"
# Reference ranges were observed in the complete reference review. These pairs
# compare visual functions; they do not assert equal shot lengths or subjects.
FUNCTIONS = {
    "hook": (0, 239, "close detail, physical props, delayed verdict"),
    "measures": (240, 347, "rule established before the measured examples"),
    "practice": (348, 431, "detail opens into blue dimension and result"),
    "exam": (448, 539, "measurement followed by red shortfall"),
    "tutor": (576, 659, "annotation followed by an extended readable hold"),
    "scope": (618, 659, "qualification remains readable"),
    "physics": (540, 659, "separate object, measurement, qualification"),
    "thinking": (660, 719, "camera reveals the next part of the argument"),
    "recognition": (240, 347, "rule and annotation"),
    "example": (0, 119, "close physical example"),
    "attempt": (360, 431, "first comparison detail and hold"),
    "recall": (480, 539, "second comparison detail and hold"),
    "transfer": (720, 779, "third comparison and final qualification"),
    "closing": (780, 859, "follow the argument before the whole-board reveal"),
}


def read_frames(name):
    with (REVIEW / f"{name}-frames.csv").open() as handle:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def quantiles(values):
    return {str(q): round(float(np.quantile(values, q)), 5) for q in (0, .1, .5, .9, 1)}


def paired_atlases(rows, reference_count, final_count, final_name="final", paired_name="paired"):
    """Put every final frame beside its function-matched reference frame."""
    output = REVIEW / "atlases" / paired_name
    output.mkdir(parents=True, exist_ok=True)
    cache = {}

    def cell(name, frame, count):
        first = frame // 20 * 20
        key = (name, first)
        if key not in cache:
            path = REVIEW / "atlases" / name / f"{first:05d}-{min(count-1,first+19):05d}.jpg"
            with Image.open(path) as source:
                cache[key] = source.copy()
        slot = frame % 20
        x, y = slot % 4 * 384, slot // 4 * 239
        return cache[key].crop((x, y, x + 384, y + 216))

    sheets = []
    for start in range(0, len(rows), 20):
        subset = rows[start:start+20]
        sheet = Image.new("RGB", (1536, 2390), "#20242a")
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(subset):
            x, y = i % 2 * 768, i // 2 * 239
            final = row["final_frame"]
            ref = row["reference_function_frame"]
            sheet.paste(cell("reference", ref, reference_count), (x, y))
            sheet.paste(cell(final_name, final, final_count), (x + 384, y))
            draw.text((x + 8, y + 220), f"REFERENCE {ref:04d}", fill="#99b8ff")
            draw.text((x + 392, y + 220), f"FINAL {final:04d}  {row['region']}", fill="white")
        name = f"{start:05d}-{start+len(subset)-1:05d}.jpg"
        sheet.save(output / name, quality=91)
        sheets.append({"file": name, "first": start, "last": start+len(subset)-1})
        # Retain only the small reference atlas cache between sheets.
        cache = {key: value for key, value in cache.items() if key[0] == "reference"}
    return sheets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-name", default="final")
    parser.add_argument("--paired-name", default="paired")
    parser.add_argument("--report-name", default="comparison")
    args = parser.parse_args()
    reference, final = read_frames("reference"), read_frames(args.final_name)
    timeline = json.loads((ROOT / "content/timeline.json").read_text())
    regions = [{"start": 0, "end": timeline["shots"][0]["start"], "region": "intro"}]
    regions += timeline["shots"]
    regions += [{"start": timeline["shots"][-1]["end"], "end": len(final), "region": "outro"}]
    mappings = dict(FUNCTIONS, intro=(0, 25, "opening detail"),
                    outro=(860, 959, "one whole-board reveal and closing hold"))
    rows = []
    for frame, actual in enumerate(final):
        region = next(s for s in regions if s["start"] <= frame < s["end"])
        lo, hi, purpose = mappings[region["region"]]
        progress = (frame - region["start"]) / max(1, region["end"] - region["start"] - 1)
        paired = min(len(reference) - 1, round(lo + (hi - lo) * progress))
        ref = reference[paired]
        row = {
            "final_frame": frame,
            "final_seconds": frame / 24,
            "region": region["region"],
            "function": purpose,
            "reference_function_frame": paired,
            "reference_normalized_frame": round(frame * (len(reference) - 1) / (len(final) - 1)),
            "mean_rgb_distance": math.sqrt(sum(
                (actual[k] - ref[k]) ** 2 for k in ("mean_r", "mean_g", "mean_b"))),
        }
        for key in ("dark_share", "blue_share", "red_share", "motion_mae"):
            row[f"final_{key}"] = actual[key]
            row[f"reference_{key}"] = ref[key]
            row[f"delta_{key}"] = actual[key] - ref[key]
        rows.append(row)
    csv_name = "frame-comparison.csv" if args.report_name == "comparison" else f"frame-{args.report_name}.csv"
    with (REVIEW / csv_name).open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    names = ("mean_r", "mean_g", "mean_b", "dark_share", "blue_share", "red_share", "motion_mae")
    report = {
        "reference": json.loads((REVIEW / "reference-analysis.json").read_text())["sha256"],
        "final": json.loads((REVIEW / f"{args.final_name}-analysis.json").read_text())["sha256"],
        "final_frames_compared": len(rows),
        "reference_frames_in_normalized_alignment": len({r["reference_normalized_frame"] for r in rows}),
        "reference_frames_in_function_alignment": len({r["reference_function_frame"] for r in rows}),
        "functions": {key: {"reference": value[:2], "purpose": value[2]} for key, value in mappings.items()},
        "appearance_and_motion_quantiles": {
            name: {key: quantiles([row[key] for row in source]) for key in names}
            for name, source in (("reference", reference), ("final", final))
        },
        "limitations": [
            "All frames are decoded and measured at 384x216; metrics are not a perceptual identity score.",
            "Normalized alignment covers every reference frame but does not equate narrative moments.",
            "Function alignment compares the observed visual grammar while permitting different story pacing.",
            "Different subjects, English captions, and added people change pixel occupancy.",
            "Visual review is recorded separately and must not be inferred from this report.",
        ],
        "paired_atlases": paired_atlases(rows, len(reference), len(final), args.final_name, args.paired_name),
        "paired_directory": f"review/atlases/{args.paired_name}",
        "paired_layout": "20 consecutive final frames per sheet; reference on the left of each pair, final on the right; 384x216 cells.",
    }
    (REVIEW / f"{args.report_name}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "final_frames_compared", "reference_frames_in_normalized_alignment",
        "reference_frames_in_function_alignment")}))


if __name__ == "__main__":
    main()
