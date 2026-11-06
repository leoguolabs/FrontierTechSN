"""Private, append-only topic and deliverable storage."""

import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from PIL import Image
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from backend.archive.documents import DOCX_LIMIT, render_docx

router = APIRouter(prefix="/api/archive")
logger = logging.getLogger(__name__)

MIB = 1024**2
VIDEO_LIMIT = 4 * 1024**3
COVER_LIMIT = 16 * MIB
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
VIDEO_TYPES = {".mp4": "video/mp4", ".webm": "video/webm"}
COVER_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


def find_entry(folder: Path, entry_id: str) -> Path:
    if re.fullmatch(r"[0-9a-f]{32}", entry_id):
        entry = folder / entry_id
        if (entry / "record.json").is_file():
            return entry
    raise HTTPException(404, "找不到该档案")


def read_record(entry: Path) -> dict:
    return json.loads((entry / "record.json").read_text(encoding="utf-8"))


def list_records(folder: Path) -> list[dict]:
    if not folder.is_dir():
        return []
    records = [read_record(entry) for entry in folder.iterdir() if (entry / "record.json").is_file()]
    return sorted(records, key=lambda item: item["created_at"], reverse=True)


def save_record(stage: Path, folder: Path, title: str, **metadata) -> dict:
    record = {
        "id": uuid4().hex,
        "title": title,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **metadata,
    }
    (stage / "record.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    folder.mkdir(parents=True, exist_ok=True)
    stage.rename(folder / record["id"])
    return record


def upload_name(upload: UploadFile) -> str:
    name = (upload.filename or "").replace("\\", "/").split("/")[-1]
    name = "".join(char for char in name if char.isprintable()).strip()
    if not name or len(name) > 240:
        raise HTTPException(422, "文件名无效或过长")
    return name


def upload_file(form, field: str, limit: int) -> tuple[UploadFile, str]:
    upload = form.get(field)
    if not isinstance(upload, UploadFile) or not upload.size:
        raise HTTPException(422, "请选择要上传的文件")
    if upload.size > limit:
        raise HTTPException(413, f"文件大小超出限制（{limit // MIB} MB）")
    return upload, upload_name(upload)


def title_from(form, fallback: str) -> str:
    title = form.get("title", "")
    if not isinstance(title, str):
        raise HTTPException(422, "标题无效")
    title = title.strip() or fallback
    if not title or len(title) > 240:
        raise HTTPException(422, "标题须在 240 字以内")
    return title


def copy_upload(upload: UploadFile, path: Path) -> None:
    upload.file.seek(0)
    with path.open("wb") as out:
        shutil.copyfileobj(upload.file, out, MIB)


def store_topic(stage: Path, folder: Path, upload: UploadFile, name: str, title: str) -> dict:
    original = stage / "source.docx"
    copy_upload(upload, original)
    try:
        html = render_docx(original)
    except Exception as exc:
        logger.info("DOCX preview could not be generated: %s", type(exc).__name__)
        raise HTTPException(422, "无法读取此 DOCX，请用 Word 重新保存后上传") from exc
    (stage / "preview.html").write_text(html, encoding="utf-8")
    return save_record(stage, folder, title, document_name=name)


def store_result(stage: Path, folder: Path, video: UploadFile, cover: UploadFile, title: str) -> dict:
    video_name = upload_name(video)
    video_type = VIDEO_TYPES.get(Path(video_name).suffix.lower())
    header = video.file.read(16)
    if not (
        (video_type == "video/mp4" and header[4:8] == b"ftyp")
        or (video_type == "video/webm" and header.startswith(b"\x1a\x45\xdf\xa3"))
    ):
        raise HTTPException(422, "视频须为 MP4 或 WebM")
    try:
        with Image.open(cover.file, formats=list(COVER_TYPES)) as image:
            cover_type = COVER_TYPES[image.format]
            if image.width * image.height > 25_000_000:
                raise ValueError("Image exceeds size limit")
            image.verify()
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, "封面须为有效的 PNG、JPEG 或 WebP 图片") from exc

    copy_upload(video, stage / "video")
    copy_upload(cover, stage / "cover")
    return save_record(
        stage, folder, title,
        video_name=video_name, video_type=video_type,
        cover_name=upload_name(cover), cover_type=cover_type,
    )


def topics_path(request: Request) -> Path:
    return request.app.state.archive_root / "topics"


@router.get("/topics")
def topics(request: Request):
    return list_records(topics_path(request))


@router.post("/topics", status_code=201)
async def add_topic(request: Request):
    async with request.form(max_files=1, max_fields=1, max_part_size=4096) as form:
        upload, name = upload_file(form, "document", DOCX_LIMIT)
        if Path(name).suffix.lower() != ".docx":
            raise HTTPException(422, "请选择 .docx 文件")
        title = title_from(form, Path(name).stem)
        with TemporaryDirectory(dir=request.app.state.archive_root, prefix=".upload-") as stage:
            return await run_in_threadpool(store_topic, Path(stage), topics_path(request), upload, name, title)


@router.get("/topics/{topic_id}")
def topic(request: Request, topic_id: str):
    entry = find_entry(topics_path(request), topic_id)
    return {**read_record(entry), "preview_html": (entry / "preview.html").read_text(encoding="utf-8")}


@router.api_route("/topics/{topic_id}/document", methods=["GET", "HEAD"])
def document(request: Request, topic_id: str):
    entry = find_entry(topics_path(request), topic_id)
    return FileResponse(entry / "source.docx", filename=read_record(entry)["document_name"], media_type=DOCX_TYPE)


@router.get("/results")
def results(request: Request):
    root = topics_path(request)
    items = [
        {**result, "topic_id": topic["id"], "topic_title": topic["title"]}
        for topic in list_records(root)
        for result in list_records(root / topic["id"] / "results")
    ]
    return sorted(items, key=lambda item: item["created_at"], reverse=True)


@router.post("/topics/{topic_id}/results", status_code=201)
async def add_result(request: Request, topic_id: str):
    entry = find_entry(topics_path(request), topic_id)
    async with request.form(max_files=2, max_fields=1, max_part_size=4096) as form:
        video, video_name = upload_file(form, "video", VIDEO_LIMIT)
        cover, _ = upload_file(form, "cover", COVER_LIMIT)
        title = title_from(form, Path(video_name).stem)
        with TemporaryDirectory(dir=request.app.state.archive_root, prefix=".upload-") as stage:
            record = await run_in_threadpool(store_result, Path(stage), entry / "results", video, cover, title)
    return {**record, "topic_id": topic_id, "topic_title": read_record(entry)["title"]}


@router.api_route("/topics/{topic_id}/results/{result_id}/{asset}", methods=["GET", "HEAD"])
def result_asset(request: Request, topic_id: str, result_id: str, asset: str, download: bool = False):
    if asset not in {"video", "cover"}:
        raise HTTPException(404, "找不到该文件")
    topic_entry = find_entry(topics_path(request), topic_id)
    entry = find_entry(topic_entry / "results", result_id)
    record = read_record(entry)
    return FileResponse(
        entry / asset, media_type=record[f"{asset}_type"], filename=record[f"{asset}_name"],
        content_disposition_type="attachment" if download else "inline",
    )
