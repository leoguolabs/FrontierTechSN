#!/usr/bin/env python3
"""Independent, unprompted ASR review of hash-bound provider audio."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[1]


def words(text):
    text = re.sub(r"\bai\b", "a i", text.lower())
    # Orthography only: these pairs are pronounced identically.
    text = re.sub(r"\bbusywork\b", "busy work", text)
    text = re.sub(r"\bpractise\b", "practice", text)
    replacements = {"48": "forty eight", "17": "seventeen", "1000": "one thousand",
                    "%": " percent"}
    for a, b in replacements.items():
        text = text.replace(a, b)
    return re.findall(r"[a-z]+", text)

def align_source(text, recognized):
    """Preserve source copy; use ASR spans only as timing observations."""
    source = text.split()
    normalize = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    matcher = difflib.SequenceMatcher(None, [normalize(s) for s in source],
                                     [normalize(w["word"]) for w in recognized],
                                     autojunk=False)
    aligned = [None] * len(source)
    for tag, i, j, k, l in matcher.get_opcodes():
        if i == j:
            continue
        if tag == "equal":
            for a, b in zip(range(i, j), range(k, l)):
                aligned[a] = {"word": source[a], "start": recognized[b]["start"],
                              "end": recognized[b]["end"]}
        else:
            start = recognized[k]["start"] if k < len(recognized) else recognized[-1]["end"]
            end = recognized[l-1]["end"] if l > k else start + .02
            for a in range(i, j):
                aligned[a] = {"word": source[a], "start": start+(end-start)*(a-i)/(j-i),
                              "end": start+(end-start)*(a-i+1)/(j-i)}
    return aligned


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-turbo-q4")
    args = parser.parse_args()
    import mlx_whisper
    directory = ROOT / "media/asr"
    directory.mkdir(parents=True, exist_ok=True)
    expected_count = len(json.loads((ROOT / "content/narration.json").read_text()))
    while True:
        manifest = json.loads((ROOT / "media/audio/manifest.json").read_text())
        reviews = []
        for row in manifest:
            audio = ROOT / row["path"]
            sha = hashlib.sha256(audio.read_bytes()).hexdigest()
            if sha != row["audio_sha256"]:
                raise ValueError("Audio changed since provider retrieval")
            target = directory / f"{row['id']}-{sha[:12]}.json"
            if target.exists() and json.loads(target.read_text()).get("model") != args.model:
                # A second recognizer gets its own record; retain the first observation.
                model_key = re.sub(r"[^a-zA-Z0-9_-]", "-", args.model)
                target = directory / f"{row['id']}-{sha[:12]}-{model_key}.json"
            if target.exists():
                review = json.loads(target.read_text())
                if review.get("model") != args.model or review.get("audio_sha256") != sha:
                    raise ValueError("Cached transcription belongs to another model or audio.")
            else:
                result = mlx_whisper.transcribe(
                    str(audio), path_or_hf_repo=args.model, language="en",
                    word_timestamps=True, temperature=0, initial_prompt=None,
                    condition_on_previous_text=False, verbose=False)
                expected, actual = words(row["text"]), words(result["text"])
                changes = [dict(kind=tag, expected=expected[i:j], heard=actual[k:l])
                           for tag, i, j, k, l in difflib.SequenceMatcher(
                               None, expected, actual, autojunk=False).get_opcodes()
                           if tag != "equal"]
                review = {"id": row["id"], "audio_sha256": sha, "model": args.model,
                          "expected": row["text"], "transcript": result["text"],
                          "normalized_changes": changes,
                          "words": [w for seg in result["segments"] for w in seg.get("words", [])],
                          "segments": result["segments"],
                          "listening_review": "not established by ASR"}
                target.write_text(json.dumps(review, indent=2) + "\n")
                print(json.dumps({k: review[k] for k in
                                  ["id", "transcript", "normalized_changes"]}), flush=True)
            expected, actual = words(row["text"]), words(review["transcript"])
            review["normalized_changes"] = [
                dict(kind=tag, expected=expected[i:j], heard=actual[k:l])
                for tag, i, j, k, l in difflib.SequenceMatcher(
                    None, expected, actual, autojunk=False).get_opcodes() if tag != "equal"]
            review["aligned_source_words"] = align_source(row["text"], review["words"])
            target.write_text(json.dumps(review, indent=2) + "\n")
            reviews.append(review)
        temp = directory / "review.tmp"
        temp.write_text(json.dumps(reviews, indent=2) + "\n")
        temp.replace(directory / "review.json")
        if len(reviews) == expected_count or not args.follow:
            break
        time.sleep(15)


if __name__ == "__main__":
    main()
