FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

WORKDIR /app
COPY wheels /wheels
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-index --find-links=/wheels --require-hashes -r requirements.lock \
    && python -m pip check \
    && python -c "import onnxruntime, kokoro_onnx; assert hasattr(kokoro_onnx.Kokoro, 'from_session')" \
    && rm -rf /wheels
COPY service.py /app/service.py
USER 10001:10001
ENTRYPOINT ["python", "-m", "uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "32", "--timeout-keep-alive", "5", "--timeout-graceful-shutdown", "40", "--no-access-log"]
