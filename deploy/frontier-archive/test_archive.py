import io
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.archive.app import create_app
from backend.archive.auth import COOKIE, password_hash

PASSWORD = "test-only archive password"
SALT = b"0123456789abcdef"
LOGIN = {"username": "test-admin", "password": PASSWORD}
DOCX_MAIN = """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <w:body>
      <w:p><w:r><w:t>选题 Topic</w:t></w:r>
        <w:hyperlink r:id="rId1"><w:r><w:t>Bad link</w:t></w:r></w:hyperlink></w:p>
      <w:tbl><w:tr><w:tc><w:p><w:r><w:t>表格</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    </w:body>
</w:document>"""
DOCX_RELS = """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
      Target="javascript:alert(1)" TargetMode="External"/>
</Relationships>"""


def docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", DOCX_MAIN)
        archive.writestr("word/_rels/document.xml.rels", DOCX_RELS)
    return buffer.getvalue()


def cover_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (24, 16), "green").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def client(tmp_path: Path):
    verifier = f"{SALT.hex()}:{password_hash(PASSWORD, SALT).hex()}"
    with TestClient(create_app(archive_root=tmp_path, username=LOGIN["username"], verifier=verifier)) as client:
        yield client


def test_archive_authentication_and_logout(client):
    assert client.get("/api/health").status_code == 200
    assert not client.get("/api/auth/session").json()["authenticated"]
    assert client.get("/api/archive/topics").status_code == 401
    assert client.post("/api/archive/topics").status_code == 401
    assert client.post("/api/auth/login", json={**LOGIN, "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json=LOGIN, headers={"Origin": "https://elsewhere.test"}).status_code == 403

    response = client.post("/api/auth/login", json=LOGIN)
    assert response.status_code == 200
    cookie = response.headers["Set-Cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    token = client.cookies.get(COOKIE)
    assert client.get("/api/auth/session").json()["authenticated"]
    assert client.get("/api/archive/topics").json() == []

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/archive/results", headers={"Cookie": f"{COOKIE}={token}"}).status_code == 401


def test_topic_preview_download_and_video_ranges(client, tmp_path):
    client.post("/api/auth/login", json=LOGIN)
    invalid = client.post("/api/archive/topics", files={"document": ("bad.docx", b"invalid")})
    assert invalid.status_code == 422
    assert list(tmp_path.iterdir()) == []

    document = docx_bytes()
    response = client.post("/api/archive/topics", files={"document": ("双语脚本.docx", document)})
    assert response.status_code == 201, response.text
    topic = response.json()
    assert topic["title"] == "双语脚本"
    topic_url = f"/api/archive/topics/{topic['id']}"
    preview = client.get(topic_url).json()["preview_html"]
    assert "选题 Topic" in preview and "<table>" in preview
    assert "Bad link" in preview and "javascript:" not in preview
    downloaded = client.get(f"{topic_url}/document")
    assert downloaded.content == document
    assert downloaded.headers["Content-Disposition"].startswith("attachment;")

    video = b"\x00\x00\x00\x14ftypisom" + bytes(range(128))
    files = {"video": ("film.mp4", video), "cover": ("cover.png", cover_bytes())}
    assert client.post(f"{topic_url}/results", files={**files, "cover": ("fake.png", b"fake")}).status_code == 422
    assert client.get("/api/archive/results").json() == []
    result = client.post(f"{topic_url}/results", data={"title": "English long film"}, files=files).json()
    assert result["topic_id"] == topic["id"]
    assert client.post(f"{topic_url}/results", files=files).status_code == 201
    assert len(client.get("/api/archive/results").json()) == 2

    asset_url = f"{topic_url}/results/{result['id']}"
    partial = client.get(f"{asset_url}/video", headers={"Range": "bytes=10-39"})
    assert partial.status_code == 206
    assert partial.headers["Content-Range"] == f"bytes 10-39/{len(video)}"
    assert partial.content == video[10:40]
    assert client.head(f"{asset_url}/video").headers["Accept-Ranges"] == "bytes"
    assert client.get(f"{asset_url}/video?download=1").headers["Content-Disposition"].startswith("attachment;")
    assert client.get(f"{asset_url}/cover").headers["Content-Type"] == "image/png"

    client.post("/api/auth/logout")
    for route in (f"{topic_url}/document", f"{asset_url}/cover", f"{asset_url}/video"):
        assert client.get(route, headers={"Range": "bytes=0-8"}).status_code == 401
