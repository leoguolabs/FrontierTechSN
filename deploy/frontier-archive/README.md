# FrontierTechSN archive on NR-TEST

The archive runs on `http://10.60.11.3:8101` on the internal network. The archive
entry point serves the login and archive UI, without loading the old video
worker, news scheduler, or their APIs.

## Build

Run these commands at the repository root. Use Python 3.11 and a Node version
supported by the frontend lockfile. Build in a clean release workspace.

```sh
npm ci --prefix frontend
npm run build --prefix frontend -- --mode archive
mkdir -p wheelhouse
python3.11 -m pip download -r requirements-archive.txt --dest wheelhouse \
  --only-binary=:all: --implementation cp --python-version 3.11 \
  --platform manylinux_2_28_aarch64 --platform manylinux2014_aarch64
```

Transfer `backend/archive`, `frontend/dist`, `requirements-archive.txt`,
`wheelhouse`, and this deployment directory to a release directory on NR-TEST.
Use the transfer as the Docker build context.

```sh
docker build -f deploy/frontier-archive/Dockerfile -t "frontier-archive:$release" .
```

Verify the archive API in a development environment with
`requirements-archive.txt`, `pytest`, and `httpx` installed.

```sh
python -m pytest -q deploy/frontier-archive/test_archive.py
```

## Run

Use a stable deployment directory with the Compose file and a private `.env`.
Create its `data` directory with mode `0700`, owned by UID and GID `10001`.
Keep `FRONTIER_ARCHIVE_RELEASE`, `FRONTIER_ARCHIVE_USER`, and
`FRONTIER_ARCHIVE_PASSWORD_HASH` in the deployment's `.env` with mode `0600`.

Generate a verifier with the prompt below in a checkout with
`requirements-archive.txt` installed. Store the printed verifier as
`FRONTIER_ARCHIVE_PASSWORD_HASH`. Use a unique password.

```sh
python - <<'PY'
import getpass
import secrets
from backend.archive.auth import password_hash

password = getpass.getpass("Archive password: ")
if not 20 <= len(password) <= 256:
    raise SystemExit("Use a password between 20 and 256 characters")
salt = secrets.token_bytes(16)
print(f"{salt.hex()}:{password_hash(password, salt).hex()}")
PY
```

Start with `docker compose -f compose.nr-test.yaml up -d` and verify
`/api/health`, login, an authenticated file download, and HTTP 206 for video
range requests. A restart revokes existing sessions. Keep one instance per
archive directory. Back up `data/` for topic and result recovery.

Uploads preserve the original files. DOCX preview is a readable HTML rendition
with headings, tables, lists, and supported embedded images. The video player
uses byte ranges and browser-native decoding. Use H.264/AAC in an MP4 with
fast-start layout for broad playback support.
