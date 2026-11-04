# NR-TEST voice library

One independent Nginx container serves both sample catalogues on the LAN:

- `http://10.60.11.3:9014/`: engine selector.
- `http://10.60.11.3:9014/kokoro/`: all 28 English voices exposed by the deployed Kokoro service.
- `http://10.60.11.3:9014/pocket/`: the 21 built-in English voices for the currently deployed Pocket TTS English model.
- `/health`: static web-service health; this does not represent model readiness.

Both catalogues support search, groups, individual playback, seeking, continuous
playback, individual WAV downloads, and a complete WAV/manifest ZIP. The same
English script is used for both engines. Waveforms come from the actual PCM.
Samples are already generated: visiting the pages does not call a model or
require a TTS API key. This service is a listening library, not a synthesis API.

## Runtime isolation

Remote directory: `/home/guoliang/tts-voice-gallery-deploy`.
Compose project: `tts-voice-gallery`; image: `tts-voice-gallery:nr-test-v1`.
The container has 0.5 CPU / 128 MiB / 32 PID limits, a read-only filesystem,
unprivileged UID, dropped capabilities, a small temporary filesystem, bounded
logs, a health check, and `restart: unless-stopped`. Docker must remain enabled
at host boot. `site/` is a persistent read-only bind mount outside the image.
No TTS model, API key, or Docker socket is mounted. Audio byte ranges are served
by Nginx for playback and seeking. The base image is pinned by digest and
supports the host's ARM64 architecture.

This Compose project does not manage the existing Pocket TTS (8090),
Chatterbox (8092), Kokoro (8094), or any unrelated container.

## Rebuild the external site

Generated samples, manifests, ZIPs and rendered HTML remain in an external
production directory and must not be committed. The source templates, player,
builder and deployment configuration live here. To collect Pocket samples,
first inspect the running upstream voice registry and language configuration.
The 2026-11-04 deployed source is `adde0654090b1d54f6ee416ed10fd1b108069f13`;
its registry and HTTP page identify 21 English voices and 5 other-language
voices. The latter are outside this English-model catalogue.

```sh
python collect_pocket.py --source http://10.60.11.3:8090 \
  --voices alba,anna,azelma,bill_boerst,caro_davy,charles,cosette,eponine,eve,fantine,george,jane,javert,jean,marius,mary,michael,paul,peter_yearsley,stuart_bell,vera \
  --text-file /absolute/external-project/sample.txt \
  --output /absolute/external-project/pocket --timeout-seconds 900

python build_site.py \
  --kokoro /absolute/kokoro-voice-samples-project \
  --pocket /absolute/external-project/pocket \
  --output /absolute/external-project/site
```

The collector submits one synthesis request at a time with a gap between
requests. It rewrites Pocket's streaming WAV length placeholders into a final
WAV header without modifying PCM. Resuming reuses only records whose text and
audio hash match. Schedule collection when the model service is idle.
An uncached voice can first download several megabytes of pinned upstream
voice-state data. This may take longer than synthesis; allow a longer client
timeout and resume the batch after the cache is ready instead of restarting
the model service.
The builder checks the complete voice inventory, unique IDs, file hashes,
complete 24 kHz mono PCM16 audio, duration, and a non-silent signal. It records
peak and clipped-sample counts in each catalogue's `verification.json`.
These checks do not replace a subjective listening review.

## Deploy or update

Copy `Dockerfile`, `nginx.conf`, `compose.nr-test.yaml`, `.dockerignore` and the
built `site/` to the remote deployment directory. Confirm port 9014 is free on
first installation, and record existing container IDs, start times and health.
The retained source sample directories are separate from model job caches.

```sh
cd /home/guoliang/tts-voice-gallery-deploy
docker compose -f compose.nr-test.yaml config --quiet
docker build --network=none --pull=false -t tts-voice-gallery:nr-test-v1 .
docker compose -f compose.nr-test.yaml up -d --no-build
curl --fail http://10.60.11.3:9014/health
```

Deploy updates as a complete `site/` tree. Preserve a backup of the previous
tree for rollback and recreate only the gallery container if replacing the
bind-mount directory. Do not restart the Docker daemon or another Compose
project. Check both pages, all WAV hashes, ZIP downloads, HTTP byte ranges,
desktop/mobile playback, and pre-existing container/health state afterwards.

To remove only this web service, run `docker compose -f compose.nr-test.yaml
down` in its deployment directory. The source samples and `site/` remain.
