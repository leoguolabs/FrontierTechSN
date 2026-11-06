FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-archive.txt .
COPY wheelhouse /wheelhouse
RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse -r requirements-archive.txt
COPY backend/archive backend/archive
COPY frontend/dist frontend/dist

USER 10001:10001
CMD ["python", "-m", "uvicorn", "backend.archive.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8101", "--no-proxy-headers"]
