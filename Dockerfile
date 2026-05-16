FROM python:3.11-alpine AS builder

WORKDIR /transcreve-api

RUN apk add --no-cache git ffmpeg build-base

COPY . .

RUN pip install --no-cache-dir -r requirements.txt --target=/transcreve-api/venv

FROM python:3.11-alpine

WORKDIR /transcreve-api

RUN apk add --no-cache \
    bash \
    dumb-init \
    tzdata \
    ffmpeg \
    flac \
    wget \
    ca-certificates

ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY --from=builder /transcreve-api /transcreve-api

ENV PYTHONPATH=/transcreve-api/venv
ENV PATH=/transcreve-api/venv/bin:$PATH

EXPOSE 5000

ENTRYPOINT ["dumb-init", "--"]

ENV PORT=5000
ENV WORKERS=16
ENV THREADS=2
ENV TIMEOUT=3600
ENV GRACEFUL_TIMEOUT=300
ENV KEEP_ALIVE=5
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=100
ENV WORKER_TMP_DIR=/dev/shm
ENV LOGLEVEL="info"

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} main:app --workers ${WORKERS:-16} --worker-class gthread --threads ${THREADS:-2} --timeout ${TIMEOUT:-3600} --graceful-timeout ${GRACEFUL_TIMEOUT:-300} --keep-alive ${KEEP_ALIVE:-5} --max-requests ${MAX_REQUESTS:-1000} --max-requests-jitter ${MAX_REQUESTS_JITTER:-100} --worker-tmp-dir ${WORKER_TMP_DIR:-/dev/shm} --log-level ${LOGLEVEL:-info}"]
