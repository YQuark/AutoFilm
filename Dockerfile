# syntax=docker/dockerfile:1
FROM python:3.12.7-slim-bookworm

ENV TZ=Asia/Shanghai

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata gosu && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt && \
    rm requirements.txt

COPY app /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /config /logs /media /fonts && \
    useradd -r -s /bin/false appuser && \
    chown -R appuser:appuser /app /config /logs /media /fonts

ENTRYPOINT ["/entrypoint.sh"]