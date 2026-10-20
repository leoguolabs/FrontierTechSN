"""Script-driven viral thumbnail generation through ChatGPT Web + OpenCLI.

The prompt formula is deliberately stored in ``backend/prompts`` and loaded at
call time, so an Admin -> Prompts edit affects the next task without a restart.
The generated prompt, image, and provenance manifest stay together under the
task output directory.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from backend import config
from backend.pipeline.digester import _chat, _resolve_provider
from backend.pipeline.opencli import OpenCLIError, OpenCLIResult, first_json, run_opencli

logger = logging.getLogger(__name__)
LogCallback = Callable[[str], None]

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_IMAGE_SIGNATURES = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
)
MAX_PROMPT_REVISIONS = 2
_TERMINAL_IMAGE_ERRORS = {"CHATGPT_IMAGE_GENERATION_FAILED", "CHATGPT_IMAGE_INPUT_MISSING"}


@dataclass(frozen=True)
class ThumbnailArtifact:
    prompt_path: str
    image_path: str
    manifest_path: str
    conversation_url: str = ""


def _log(log: LogCallback | None, message: str) -> None:
    if log is not None:
        log(message)
    else:
        logger.info(message)


def _clean_model_prompt(value: str) -> str:
    clean = value.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    if not clean:
        raise RuntimeError("Thumbnail art director returned an empty image prompt")
    return clean


def _rows(value: Any) -> list[dict[str, Any]]:
    """Normalize common OpenCLI JSON envelopes to a list of result rows."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("data", "items", "results", "rows"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [value]
    return []


def _field(row: dict[str, Any], name: str) -> str:
    for key, value in row.items():
        if str(key).lower() == name.lower():
            text = str(value or "").strip()
            for prefix in ("📁", "🔗"):
                if text.startswith(prefix):
                    text = text[len(prefix) :].strip()
            return text
    return ""


def _looks_like_image(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 32:
            return False
        with path.open("rb") as handle:
            header = handle.read(12)
        if not (header.startswith(_IMAGE_SIGNATURES) or (
            header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        )):
            return False
        # A timeout can leave a valid header followed by incomplete image data.
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
        return True
    except (OSError, ValueError, SyntaxError):
        return False


def _new_image_files(image_dir: Path, before: set[Path]) -> list[Path]:
    root = image_dir.resolve()
    candidates = [
        path.resolve()
        for path in image_dir.iterdir()
        if path.is_file()
        and not path.is_symlink()
        and path.suffix.lower() in _IMAGE_SUFFIXES
        and root in path.resolve().parents
        and path.resolve() not in before
        and _looks_like_image(path)
    ]
    return sorted(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))


def _reported_image_files(rows: list[dict[str, Any]], image_dir: Path) -> list[Path]:
    root = image_dir.resolve()
    files: list[Path] = []
    for row in rows:
        raw = _field(row, "file")
        if not raw or raw == "-":
            continue
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = config.PROJECT_ROOT / path
        resolved = path.resolve()
        if (resolved == root or root in resolved.parents) and _looks_like_image(resolved):
            files.append(resolved)
    return files


def _record_command_diagnostics(manifest: dict[str, Any], result: OpenCLIResult) -> None:
    manifest["command_returncode"] = result.returncode
    manifest["command_diagnostics"] = result.stderr[-8000:]
    for line in result.stderr.splitlines():
        if not line.startswith("[chatgpt/image] "):
            continue
        try:
            progress = json.loads(line.removeprefix("[chatgpt/image] "))
        except ValueError:
            continue
        if not isinstance(progress, dict):
            continue
        if progress.get("stage"):
            manifest["last_stage"] = str(progress["stage"])
        if progress.get("conversation_url"):
            manifest["conversation_url"] = str(progress["conversation_url"])
        observation = progress.get("observation")
        if (
            isinstance(observation, dict)
            and observation.get("terminal_error") in _TERMINAL_IMAGE_ERRORS
            and isinstance(observation.get("provider_message"), str)
            and observation["provider_message"].strip()
            and re.fullmatch(r"https://chatgpt\.com/c/[A-Za-z0-9_-]{8,}", str(progress.get("conversation_url", "")))
        ):
            manifest["provider_error"] = {
                "code": observation["terminal_error"],
                "message": observation["provider_message"],
                "conversation_url": progress["conversation_url"],
            }


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


@contextmanager
def _thumbnail_lock(directory: Path) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".generation.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Thumbnail generation is already running for this task") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Invalid thumbnail request metadata at {path}")
    return value


async def generate_thumbnail_prompt(
    *,
    title: str,
    script: str,
    provider_id: int | None = None,
    ai_endpoint: str | None = None,
    ai_model: str | None = None,
    log: LogCallback | None = None,
) -> str:
    """Turn the final narration script into one complete image-generation prompt."""
    template = (config.PROMPTS_DIR / "thumbnail.txt").read_text(encoding="utf-8")
    endpoint, model, api_key = await _resolve_provider(provider_id, ai_endpoint, ai_model)
    source = json.dumps(
        {"video_title": title, "audio_script": script},
        indent=2,
        ensure_ascii=False,
    )
    result = await _chat(
        template,
        source,
        endpoint,
        model,
        api_key,
        log,
        "Thumbnail art direction",
        max_tokens=3072,
    )
    return _clean_model_prompt(result)


def _source_request_hash(title: str, script: str) -> str:
    return hashlib.sha256(json.dumps(
        {"title": title, "script": script}, sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")).hexdigest()


def _prompt_revision_state(root: Path) -> tuple[Path, list[dict[str, Any]]]:
    """Find the persisted active revision without resetting its attempt budget."""
    state = _read_manifest(root / "prompt-revisions.json")
    revisions = state.get("revisions", [])
    if not isinstance(revisions, list) or len(revisions) > MAX_PROMPT_REVISIONS:
        raise RuntimeError("Invalid thumbnail prompt revision history")
    directory = root
    for number, revision in enumerate(revisions, 1):
        if (
            not isinstance(revision, dict) or revision.get("number") != number
            or not isinstance(revision.get("prompt"), str)
            or hashlib.sha256(revision["prompt"].encode()).hexdigest() != revision.get("prompt_sha256")
        ):
            raise RuntimeError("Invalid thumbnail prompt revision binding")
        directory = root / f"revision-{number}-{revision['prompt_sha256'][:16]}"
        saved = directory / "prompt.txt"
        if not saved.is_file() or saved.read_text(encoding="utf-8").strip() != revision["prompt"]:
            raise RuntimeError("Saved thumbnail revision prompt is missing or changed")
    return directory, revisions


async def revise_thumbnail_prompt(
    *, title: str, script: str, prompt: str, provider_error: dict[str, Any],
    revisions: list[dict[str, Any]], provider_id: int | None,
    ai_endpoint: str | None, ai_model: str | None, log: LogCallback | None,
) -> dict[str, str]:
    """Ask the configured project AI to address the observed terminal response."""
    editorial = (config.PROMPTS_DIR / "thumbnail.txt").read_text(encoding="utf-8")
    repair = (config.PROMPTS_DIR / "thumbnail_repair.txt").read_text(encoding="utf-8")
    endpoint, model, api_key = await _resolve_provider(provider_id, ai_endpoint, ai_model)
    response = await _chat(
        editorial + "\n\n" + repair,
        json.dumps({
            "video_title": title, "audio_script": script, "failed_prompt": prompt,
            "provider_error": provider_error, "previous_revisions": revisions,
        }, ensure_ascii=False, indent=2),
        endpoint, model, api_key, log, "Thumbnail prompt repair", max_tokens=4096,
    )
    value = json.loads(_clean_model_prompt(response))
    if not isinstance(value, dict):
        raise RuntimeError("Thumbnail prompt repair must return an object")
    revised = value.get("prompt")
    rationale = value.get("rationale")
    if not isinstance(revised, str) or not revised.strip() or not isinstance(rationale, str) or not rationale.strip():
        raise RuntimeError("Thumbnail prompt repair requires a prompt and rationale")
    revised = revised.strip()
    if re.sub(r"\s+", " ", revised) == re.sub(r"\s+", " ", prompt.strip()):
        raise RuntimeError("Thumbnail prompt repair did not change the rejected prompt")
    return {"prompt": revised, "rationale": rationale.strip()}


async def _revise_failed_thumbnail(
    *, task_dir: Path, title: str, script_path: Path, provider_id: int | None,
    ai_endpoint: str | None, ai_model: str | None, log: LogCallback | None,
) -> bool:
    manifest_path = task_dir / "thumbnail" / "manifest.json"
    manifest = _read_manifest(manifest_path)
    failure = manifest.get("provider_error")
    if manifest.get("status") != "failed" or not isinstance(failure, dict):
        return False  # Timeout, transport uncertainty, or an unowned response.
    script = script_path.read_text(encoding="utf-8").strip()
    source_hash = _source_request_hash(title, script)
    if manifest.get("request_sha256") != source_hash:
        raise RuntimeError("Thumbnail repair source differs from the failed request")
    root = task_dir / "thumbnail" / "requests" / source_hash
    directory, revisions = _prompt_revision_state(root)
    state_path = directory / "image-request.json"
    state = _read_manifest(state_path)
    prompt = (directory / "prompt.txt").read_text(encoding="utf-8").strip()
    if (
        failure.get("code") not in _TERMINAL_IMAGE_ERRORS
        or not failure.get("message")
        or manifest.get("request_state_path") != str(state_path.resolve())
        or state.get("prompt") != f"Generate an image of: {prompt}"
        or state.get("conversationUrl") != failure.get("conversation_url")
        or manifest.get("conversation_url") != failure.get("conversation_url")
    ):
        raise RuntimeError("Thumbnail repair requires the exact rejected request checkpoint")
    # Preserve the actual response and failed attempt, even when repair fails.
    _write_manifest(directory / "failure.json", manifest)
    if len(revisions) >= MAX_PROMPT_REVISIONS:
        _log(log, "Thumbnail: bounded prompt revisions exhausted; all request evidence retained")
        return False
    _log(log, "Thumbnail: confirmed provider error; asking project AI to revise the saved prompt")
    repair = await revise_thumbnail_prompt(
        title=title, script=script, prompt=prompt, provider_error=failure,
        revisions=revisions, provider_id=provider_id, ai_endpoint=ai_endpoint,
        ai_model=ai_model, log=log,
    )
    number = len(revisions) + 1
    prompt_hash = hashlib.sha256(repair["prompt"].encode()).hexdigest()
    revision = {
        "number": number, **repair, "prompt_sha256": prompt_hash,
        "parent_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "parent_request_state_path": str(state_path.resolve()),
        "provider_error": failure, "revised_at": datetime.now(timezone.utc).isoformat(),
    }
    target = root / f"revision-{number}-{prompt_hash[:16]}"
    target.mkdir(parents=True, exist_ok=True)
    saved = target / "prompt.txt"
    if saved.exists() and saved.read_text(encoding="utf-8").strip() != repair["prompt"]:
        raise RuntimeError("Thumbnail revision conflicts with an existing saved prompt")
    saved.write_text(repair["prompt"] + "\n", encoding="utf-8")
    # Publish the revision pointer before any new provider submission.
    _write_manifest(root / "prompt-revisions.json", {"revisions": [*revisions, revision]})
    _log(log, f"Thumbnail: saved AI prompt revision {number}/{MAX_PROMPT_REVISIONS}: {repair['rationale']}")
    return True


async def generate_thumbnail(
    *,
    task_id: str,
    task_dir: Path,
    title: str,
    script_path: Path,
    provider_id: int | None = None,
    ai_endpoint: str | None = None,
    ai_model: str | None = None,
    log: LogCallback | None = None,
    resume_conversation_url: str | None = None,
    allow_legacy_regeneration: bool = False,
) -> ThumbnailArtifact:
    """Recover an existing request, then revise only a confirmed failed prompt.

    ``resume_conversation_url`` explicitly adopts the saved prompt for a legacy
    request. OpenCLI still verifies that conversation's exact submitted prompt
    before accepting its images. Uncertain requests are never replaced; an
    explicit terminal response permits at most two persisted AI prompt revisions.
    Intentional script regeneration may explicitly replace an untracked legacy
    request by setting ``allow_legacy_regeneration``.
    """
    with _thumbnail_lock(task_dir / "thumbnail"):
        while True:
            try:
                return await _generate_thumbnail_locked(
                    task_id=task_id, task_dir=task_dir, title=title, script_path=script_path,
                    provider_id=provider_id, ai_endpoint=ai_endpoint, ai_model=ai_model,
                    log=log, resume_conversation_url=resume_conversation_url,
                    allow_legacy_regeneration=allow_legacy_regeneration,
                )
            except OpenCLIError:
                if not await _revise_failed_thumbnail(
                    task_dir=task_dir, title=title, script_path=script_path,
                    provider_id=provider_id, ai_endpoint=ai_endpoint, ai_model=ai_model, log=log,
                ):
                    raise
                resume_conversation_url = None


async def _generate_thumbnail_locked(
    *,
    task_id: str,
    task_dir: Path,
    title: str,
    script_path: Path,
    provider_id: int | None,
    ai_endpoint: str | None,
    ai_model: str | None,
    log: LogCallback | None,
    resume_conversation_url: str | None,
    allow_legacy_regeneration: bool,
) -> ThumbnailArtifact:
    thumbnail_dir = task_dir / "thumbnail"
    image_dir = thumbnail_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = thumbnail_dir / "manifest.json"
    prompt_path = thumbnail_dir / "prompt.txt"
    previous = _read_manifest(manifest_path)
    script = script_path.read_text(encoding="utf-8").strip()
    if not script:
        raise RuntimeError(f"Thumbnail source script is empty at {script_path}")
    request_sha256 = _source_request_hash(title, script)
    request_dir, revisions = _prompt_revision_state(thumbnail_dir / "requests" / request_sha256)
    saved_prompt_path = request_dir / "prompt.txt"
    state_path = request_dir / "image-request.json"
    same_request = previous.get("request_sha256") == request_sha256

    # A legacy failure has no content hash or submission checkpoint. Replaying
    # it could silently create a second image; require explicit recovery first.
    if (
        not resume_conversation_url
        and not allow_legacy_regeneration
        and previous.get("status") in {"failed", "generating"}
        and not previous.get("request_sha256")
        and (
            not previous.get("source_script")
            or Path(str(previous["source_script"])).resolve() == script_path.resolve()
        )
        and prompt_path.is_file()
    ):
        raise RuntimeError(
            "Saved legacy thumbnail request needs a verified resume_conversation_url; "
            "the original image prompt was not replayed"
        )

    if (
        not resume_conversation_url and same_request
        and previous.get("status") == "ready" and saved_prompt_path.is_file()
    ):
        raw_image = previous.get("image_path")
        image_path = Path(raw_image) if raw_image else None
        if (
            image_path is not None
            and not image_path.is_symlink()
            and image_dir.resolve() in image_path.resolve().parents
            and _looks_like_image(image_path)
        ):
            prompt_path.write_text(saved_prompt_path.read_text(encoding="utf-8"), encoding="utf-8")
            _log(log, f"Thumbnail: reusing completed image at {image_path}")
            return ThumbnailArtifact(
                str(prompt_path.resolve()), str(image_path.resolve()),
                str(manifest_path.resolve()), str(previous.get("conversation_url") or ""),
            )

    if resume_conversation_url and not re.fullmatch(
        r"https://chatgpt\.com/c/[A-Za-z0-9_-]{8,}", resume_conversation_url,
    ):
        raise ValueError("Thumbnail recovery requires a canonical ChatGPT conversation URL")
    # Validate recovery inputs before replacing the previous failure evidence.
    recovery_prompt = None
    if resume_conversation_url:
        source_prompt = saved_prompt_path if saved_prompt_path.is_file() else prompt_path
        if not source_prompt.is_file():
            raise RuntimeError("Thumbnail recovery requires the original saved prompt")
        recovery_prompt = source_prompt.read_text(encoding="utf-8").strip()
        if not recovery_prompt:
            raise RuntimeError("Thumbnail recovery cannot use an empty saved prompt")
        prior_state = _read_manifest(state_path)
        submitted_prompt = f"Generate an image of: {recovery_prompt}"
        if prior_state and prior_state.get("prompt") != submitted_prompt:
            raise RuntimeError("Thumbnail recovery prompt differs from the saved request")
        request_dir.mkdir(parents=True, exist_ok=True)
        _write_manifest(state_path, {
            "prompt": submitted_prompt,
            "stage": "recovery_requested",
            "conversationUrl": resume_conversation_url,
            "beforeUrls": prior_state.get("beforeUrls", []),
        })
    started_at = datetime.now(timezone.utc).isoformat()

    manifest: dict[str, Any] = {
        "task_id": task_id,
        "status": "generating",
        "provider": "chatgpt_web",
        "source_script": str(script_path),
        "request_sha256": request_sha256,
        "request_state_path": str(state_path.resolve()),
        "prompt_revision": len(revisions),
        "prompt_path": str(prompt_path),
        "image_path": "",
        "image_paths": [],
        "conversation_url": resume_conversation_url or (
            previous.get("conversation_url", "")
            if same_request and previous.get("request_state_path") == str(state_path.resolve()) else ""
        ),
        "started_at": started_at,
        "completed_at": None,
        "error": None,
    }
    if resume_conversation_url:
        manifest["recovery_origin"] = {
            "prompt_path": str(source_prompt.resolve()),
            "previous_request_sha256": previous.get("request_sha256"),
            "conversation_url": resume_conversation_url,
        }
    if previous:
        history_dir = thumbnail_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_path = history_dir / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S.%fZ}.json"
        _write_manifest(history_path, previous)
        manifest["previous_manifest_path"] = str(history_path.resolve())
        if prompt_path.is_file():
            history_prompt_path = history_path.with_suffix(".prompt.txt")
            history_prompt_path.write_text(prompt_path.read_text(encoding="utf-8"), encoding="utf-8")
            manifest["previous_prompt_path"] = str(history_prompt_path.resolve())
    _write_manifest(manifest_path, manifest)

    try:
        if recovery_prompt is not None:
            prompt = recovery_prompt
            _log(log, "Thumbnail: recovering the original saved image request")
        elif saved_prompt_path.is_file():
            prompt = saved_prompt_path.read_text(encoding="utf-8").strip()
            if not prompt:
                raise RuntimeError("Saved thumbnail prompt is empty; original request was not replayed")
            _log(log, "Thumbnail: reusing the saved prompt and request checkpoint")
        elif state_path.exists():
            raise RuntimeError("Saved thumbnail request has no prompt; original request was not replayed")
        else:
            _log(log, "Thumbnail: deriving a viral cover prompt from the final audio script")
            prompt = await generate_thumbnail_prompt(
                title=title,
                script=script,
                provider_id=provider_id,
                ai_endpoint=ai_endpoint,
                ai_model=ai_model,
                log=log,
            )
        request_dir.mkdir(parents=True, exist_ok=True)
        saved_prompt_path.write_text(prompt + "\n", encoding="utf-8")
        prompt_path.write_text(prompt + "\n", encoding="utf-8")
        _log(log, f"Thumbnail: prompt saved to {prompt_path}")

        before = {
            path.resolve()
            for path in image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
        }
        timeout = config.THUMBNAIL_CHATGPT_TIMEOUT
        command_error: OpenCLIError | None = None
        try:
            result = await run_opencli([
                "chatgpt",
                "image",
                prompt,
                "--op",
                str(image_dir.resolve()),
                "--state-file",
                str(state_path.resolve()),
                "--timeout",
                str(timeout),
                "--window",
                "background",
                "--site-session",
                "ephemeral",
                "--keep-tab",
                "false",
                "-f",
                "json",
            ], timeout=timeout + 45)
        except OpenCLIError as exc:
            # The process is reaped before run_opencli raises. A completed file
            # can survive a timeout during export/cleanup; never submit again.
            command_error = exc
            result = exc.result
        parsed_rows = []
        if result is not None:
            _record_command_diagnostics(manifest, result)
            try:
                parsed_rows = _rows(first_json(result.stdout))
            except OpenCLIError:
                pass  # A fresh, fully decoded local image is sufficient proof.
        conversation_url = next(
            (_field(row, "link") for row in parsed_rows if _field(row, "link")),
            manifest["conversation_url"],
        )
        manifest["conversation_url"] = conversation_url
        reported = _reported_image_files(parsed_rows, image_dir)
        created = _new_image_files(image_dir, before)
        # Output may mention an older cover or a symlink; only accept files
        # freshly downloaded into this task's image directory by this attempt.
        reported_new = [path for path in reported if path in created]
        images = list(dict.fromkeys([*reported_new, *created]))
        if not images:
            if command_error is not None:
                raise command_error
            raise OpenCLIError(
                "ChatGPT Web completed without a valid downloaded image in the task thumbnail directory"
            )
        if command_error is not None:
            manifest["recovered_download"] = True
            manifest["command_warning"] = str(command_error)
            _log(log, "Thumbnail: recovered a complete downloaded image after a command failure")

        artifact = ThumbnailArtifact(
            prompt_path=str(prompt_path.resolve()),
            image_path=str(images[0]),
            manifest_path=str(manifest_path.resolve()),
            conversation_url=conversation_url,
        )
        manifest.update(
            {
                "status": "ready",
                "image_path": artifact.image_path,
                "image_paths": [str(path) for path in images],
                "conversation_url": conversation_url,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _write_manifest(manifest_path, manifest)
        _log(log, f"Thumbnail: ChatGPT Web image saved to {artifact.image_path}")
        return artifact
    except Exception as exc:
        manifest.update(
            {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }
        )
        _write_manifest(manifest_path, manifest)
        raise


def artifact_dict(artifact: ThumbnailArtifact) -> dict[str, str]:
    """Small JSON-friendly helper for scripts and acceptance checks."""
    return asdict(artifact)
