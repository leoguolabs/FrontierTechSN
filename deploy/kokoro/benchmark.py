"""Run fresh serial synthesis requests and save reproducible WAV/JSON evidence."""
import argparse
import json
import os
import time
import urllib.request
from pathlib import Path

CASES = [
    {"id": "short-af-heart", "voice": "af_heart", "language": "en-us",
     "text": "A clear voice begins with a clear idea. This short sample checks the opening, the natural pause, and the final word."},
    {"id": "technical-am-michael", "voice": "am_michael", "language": "en-us",
     "text": "Inside the imaging satellite, a reaction wheel changes the direction of the spacecraft without firing a rocket. Solar panels supply electrical power, while the battery carries the system through darkness. The camera records reflected sunlight. A radio then sends the observations to Earth. Each component has a different job, and the complete system depends on their timing."},
    {"id": "british-bm-george", "voice": "bm_george", "language": "en-gb",
     "text": "A snowflake begins with a tiny crystal in a cold cloud. Water vapour joins its surface, and the shape grows as the crystal travels. Temperature changes which faces grow fastest. Humidity changes how much water is available. The familiar sixfold pattern follows the structure of ice, while the details record a changing journey through the air."},
    {"id": "long-af-heart", "voice": "af_heart", "language": "en-us",
     "text": "When the ocean grows dark, a daily migration begins. Small animals rise from deeper water to find food near the surface. They feed on drifting plants and on one another. But the trip is a balance between opportunity and danger. Near the surface there is more food, and there are also predators. As dawn approaches, many of these animals return to deeper water. Some of the carbon they consumed travels with them. Their breathing, their waste, and the food they leave behind connect the bright surface to the darker ocean below. Scientists study this movement with nets, acoustic instruments, and careful observations. No single measurement tells the whole story. Different animals travel to different depths, and the pattern changes with location and season. The important point is the connection: the ocean is not a set of isolated layers. Living animals move material between them, one journey at a time."},
]


def run(base_url, key, directory, upload=None, case_ids=None, upload_prefix=""):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}

    def request(path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(base_url + path, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.load(response)

    results = []
    for case in CASES:
        if case_ids and case['id'] not in case_ids:
            continue
        payload = {k: v for k, v in case.items() if k != "id"}
        payload.update(speed=1.0, cache=False)
        start = time.monotonic()
        job = request("/v1/jobs", payload)
        deadline = time.monotonic() + 900
        while job["status"] in {"queued", "running"}:
            if time.monotonic() > deadline:
                raise RuntimeError("Benchmark deadline exceeded: " + case["id"])
            time.sleep(0.5)
            job = request("/v1/jobs/" + job["id"])
        if job["status"] != "completed":
            raise RuntimeError("Synthesis failed: " + case["id"])
        job["http_completion_seconds"] = time.monotonic() - start
        job["case"] = case
        req = urllib.request.Request(base_url + "/v1/jobs/" + job["id"] + "/audio", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            audio = response.read()
        (directory / (case["id"] + ".wav")).write_bytes(audio)
        (directory / (case["id"] + ".json")).write_text(json.dumps(job, indent=2))
        results.append(job)
        (directory / "benchmark.json").write_text(json.dumps(results, indent=2))
        if upload:
            for name, data in [(case["id"] + ".wav", audio), (case["id"] + ".json", json.dumps(job).encode()), ("benchmark.json", json.dumps(results).encode())]:
                req = urllib.request.Request(upload + "/" + upload_prefix + name, data=data, method="PUT")
                urllib.request.urlopen(req, timeout=30).read()
        print(json.dumps({"case": case["id"], "audio_seconds": job["duration_seconds"],
                          "generation_seconds": job["generation_seconds"], "rtf": job["real_time_factor"],
                          "http_seconds": job["http_completion_seconds"]}), flush=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://10.60.11.3:8094")
    parser.add_argument("--output", default="evidence/benchmark")
    parser.add_argument("--upload-url")
    parser.add_argument("--upload-prefix", default="")
    parser.add_argument("--case-ids", help="Comma-separated case IDs for a bounded comparison")
    args = parser.parse_args()
    run(args.base_url, os.environ["KOKORO_API_KEY"], args.output, args.upload_url,
        set(args.case_ids.split(',')) if args.case_ids else None, args.upload_prefix)
