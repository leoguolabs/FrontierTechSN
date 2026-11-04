# Kokoro CPU service on NR-TEST

This standalone deployment serves the retained Kokoro v1.0 FP32 ONNX model and
stock English voices. It does not change the application's selected TTS model.

- Host directory: `/home/guoliang/kokoro-tts-deploy`
- API: `http://10.60.11.3:8094`
- Compose project: `kokoro-tts`; service: `kokoro`
- CPU quota: 8 cores; ONNX intra-op threads: 8; inter-op threads: 1
- Memory limit: 4 GiB; one synthesis job at a time; eight waiting jobs
- Initial accepted languages: `en-us` with `af_*`/`am_*`, and `en-gb` with
  `bf_*`/`bm_*`. Other languages are not advertised as validated.

`requirements.lock` pins the complete ARM64 Python dependency set by version and
wheel SHA-256. `model-manifest.json` identifies the retained production model
snapshot. Its ONNX checksum belongs to the existing local cache; it must not be
represented as the checksum of a different upstream release asset with the same
filename. Place these exact retained model/voice files in `models/`, with the
manifest named `models/manifest.json`. Startup verifies their hashes.

The runtime uses the official Python 3.11 Bookworm image pinned by digest. It
loads the model once using ONNX Runtime's CPU provider, sets explicit thread
limits, and disables idle thread spinning. No request downloads dependencies,
models, or voices. The container has a read-only root filesystem, an unprivileged
user, a bounded temporary filesystem, dropped capabilities, and rotated logs.
The temporary mount permits executable mappings because phonemizer loads a
private temporary copy of its eSpeak shared library. Startup synthesizes a short
American and British English utterance before reporting readiness.

## Credentials and API

The bearer credential is generated on NR-TEST in the deployment's `.env` file,
owned by root with mode `0600`. Do not commit or print that file. Clients pass
the credential using `Authorization: Bearer <credential>`.

`GET /health` is unauthenticated and becomes available after model verification
and loading. All `/v1/` routes require the bearer credential:

| Route | Purpose |
| --- | --- |
| `GET /v1/voices` | List the deployed English stock voice IDs |
| `GET /v1/capabilities` | Return model identity, limits and audio format |
| `POST /v1/jobs` | Submit a queued synthesis request; returns HTTP 202 |
| `GET /v1/jobs/{id}` | Read queued/running/completed/failed state and timings |
| `GET /v1/jobs/{id}/audio` | Download a completed mono PCM16 WAV |

Example request body:

```json
{
  "text": "A clear voice begins with a clear idea.",
  "voice": "af_heart",
  "language": "en-us",
  "speed": 1.0,
  "cache": true
}
```

Requests are limited to 2,000 characters, a 16 KiB body and a speed range of
0.7–1.3. Unsupported voices/languages return 422. A full queue returns 429 and
`Retry-After`. A content/model-bound identity deduplicates cached requests.
Set `cache: false` for fresh benchmark generation; it creates a unique job.

Jobs and accepted WAV files survive container recreation in `data/jobs/`.
Completed/failed records expire after seven days, with an additional 2 GiB
retention budget, enforced at startup and on submissions. An interrupted job is
marked failed on restart and can be explicitly resubmitted. No incomplete WAV
is served. A restart while a job is running may interrupt that job, so perform
planned restarts while `/health` reports `active: false` and `queue_depth: 0`.

## Build and operate

Copy this directory's deployment files, the pinned wheel files into `wheels/`,
and the retained model files into `models/`. Keep `.env`, wheels, generated audio
and operational evidence outside Git. Ensure `data/` and `data/jobs/` are owned
by UID/GID 10001. The initial deployment builds offline from the supplied wheel
directory using pip's hash verification. No host Python packages are changed.

Run from the deployment directory:

```sh
docker compose -f compose.nr-test.yaml up -d --no-build kokoro
docker compose -f compose.nr-test.yaml ps
curl --fail http://10.60.11.3:8094/health
docker compose -f compose.nr-test.yaml logs --tail 60 kokoro
```

For an offline build without consuming more than two CPU cores:

```sh
DOCKER_BUILDKIT=0 docker build --pull=false --network=none --memory=2g --cpu-period=100000 --cpu-quota=200000 -t kokoro-tts:nr-test-v1 .
```

The Compose restart policy is `unless-stopped`. The existing host Docker service
must start on boot. Recreating or restarting this Compose service affects only
Kokoro; never restart the Docker daemon or another Compose project for this
deployment. To stop Kokoro while retaining its files:

```sh
docker compose -f compose.nr-test.yaml stop kokoro
```

## Validation

`test_service.py` covers authentication, request/voice/language bounds, WAV
publication, request deduplication, queue saturation, expiration, and interrupted
job recovery without loading the model. `benchmark.py` sends uncached serial
requests and records generation time separately from audio duration and HTTP
completion time. Real-time factor is generation seconds divided by audio
seconds; values below 1 mean synthesis is faster than playback.

Use `monitor.py` only during a deployment or benchmark. It reads existing TTS
health endpoints and container status, saving operational evidence without
submitting work to existing services. Stop it by creating
`evidence/monitor.stop`. Compare pre/post container IDs, images, start times,
restart counts, health status and endpoint latency. These checks establish
observed availability and resource behavior, not every other application's
business-workflow latency.

Runtime evidence and WAV examples for the initial deployment are retained in
the local ignored `outputs/kokoro-deployment-20261104/` and the remote
deployment's `evidence/` directory. ASR/text and waveform checks must be reported
separately from subjective listening.

The initial 4-core technical sample produced 24.82 seconds of audio in 39.37
seconds. A same-model 8-core comparison took 27.54 seconds. The deployed quota
was therefore set to eight cores with a low CPU share weight of 128; this is a
shared upper bound, not an exclusive reservation. The service retains its
4 GiB memory limit and single-job concurrency.
