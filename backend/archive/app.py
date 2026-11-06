"""NR-TEST entry point for the private FrontierTechSN workspace."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from anyio import CapacityLimiter, WouldBlock
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from backend.archive.auth import API_PREFIX, COOKIE, SESSION_AGE, ArchiveAuth
from backend.archive.library import COVER_LIMIT, DOCX_LIMIT, MIB, VIDEO_LIMIT, router

LOGIN_PATH = f"{API_PREFIX}/auth/login"
SESSION_PATH = f"{API_PREFIX}/auth/session"
PUBLIC_API = {"/api/health", SESSION_PATH, LOGIN_PATH}
FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "dist"


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


def create_app(
    *, archive_root: Path | None = None, username: str | None = None, verifier: str | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.auth = ArchiveAuth(
            username if username is not None else os.environ["FRONTIER_ARCHIVE_USER"],
            verifier if verifier is not None else os.environ["FRONTIER_ARCHIVE_PASSWORD_HASH"],
        )
        app.state.archive_root = archive_root or Path(os.getenv("FRONTIER_ARCHIVE_DIR", "data/archive"))
        app.state.archive_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        app.state.uploads = CapacityLimiter(2)
        yield

    app = FastAPI(title="FrontierTechSN", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _exc: RequestValidationError):
        return JSONResponse({"detail": "请求参数格式无效"}, status_code=422)

    @app.middleware("http")
    async def private_workspace(request: Request, call_next):
        path = request.url.path
        auth = request.app.state.auth
        session = request.cookies.get(COOKIE, "")
        if path.startswith("/api/") and path not in PUBLIC_API and not auth.authenticated(session):
            return JSONResponse({"detail": "请先登录"}, status_code=401, headers={"Cache-Control": "no-store"})

        is_write = request.method not in {"GET", "HEAD", "OPTIONS"}
        if is_write:
            origin = request.headers.get("origin")
            if (
                request.headers.get("sec-fetch-site") == "cross-site"
                or (origin and origin != f"{request.url.scheme}://{request.url.netloc}")
            ):
                return JSONResponse({"detail": "仅接受同源请求"}, status_code=403)

        upload = request.method == "POST" and path.startswith(f"{API_PREFIX}/topics")
        if upload or (request.method == "POST" and path == LOGIN_PATH):
            limit = 16 * 1024
            if upload:
                limit = (VIDEO_LIMIT + COVER_LIMIT if path.rstrip("/").endswith("/results") else DOCX_LIMIT) + MIB
            length = request.headers.get("content-length", "")
            if not length.isascii() or not length.isdecimal() or request.headers.get("transfer-encoding"):
                return JSONResponse({"detail": "请求缺少有效的文件大小"}, status_code=411)
            if len(length) > 12 or int(length) > limit:
                return JSONResponse({"detail": "上传大小超出限制"}, status_code=413)

        if upload:
            try:
                request.app.state.uploads.acquire_nowait()
            except WouldBlock:
                return JSONResponse({"detail": "已有上传正在进行，请稍后重试"}, status_code=429)
            try:
                response = await call_next(request)
            finally:
                request.app.state.uploads.release()
        else:
            response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; object-src 'none'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        if not path.startswith("/assets/"):
            response.headers["Cache-Control"] = "private, no-store"
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get(SESSION_PATH)
    def session_status(request: Request):
        return {"authenticated": request.app.state.auth.authenticated(request.cookies.get(COOKIE, ""))}

    @app.post(LOGIN_PATH)
    async def login(credentials: Login, request: Request, response: Response):
        auth = request.app.state.auth
        auth.admit_attempt()
        if not await run_in_threadpool(auth.verify, credentials.username, credentials.password):
            raise HTTPException(401, "用户名或密码不正确")
        auth.revoke(request.cookies.get(COOKIE, ""))
        response.set_cookie(
            COOKIE, auth.create_session(), max_age=SESSION_AGE, httponly=True,
            path=API_PREFIX, samesite="strict", secure=request.url.scheme == "https",
        )
        return {"authenticated": True}

    @app.post(f"{API_PREFIX}/auth/logout", status_code=204)
    def logout(request: Request):
        request.app.state.auth.revoke(request.cookies.get(COOKIE, ""))
        response = Response(status_code=204)
        response.delete_cookie(
            COOKIE, path=API_PREFIX, httponly=True, samesite="strict", secure=request.url.scheme == "https",
        )
        return response

    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets", check_dir=False), name="assets")

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    @app.api_route("/topics", methods=["GET", "HEAD"], include_in_schema=False)
    @app.api_route("/results", methods=["GET", "HEAD"], include_in_schema=False)
    def frontend():
        return FileResponse(FRONTEND / "archive.html")

    return app
