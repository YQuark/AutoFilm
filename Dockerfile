FROM python:3.12.7-slim-bookworm

ENV TZ=Asia/Shanghai

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

COPY app /app

RUN useradd -r -s /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "/app/main.py"]