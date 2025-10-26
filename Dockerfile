# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg curl ca-certificates nodejs npm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Tailwind CLI
RUN curl -fsSL https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
  -o /usr/local/bin/tailwindcss && chmod +x /usr/local/bin/tailwindcss

COPY app ./app
COPY web ./web
COPY scripts ./scripts
COPY tailwind.config.cjs ./tailwind.config.cjs

RUN mkdir -p web/static && \
    tailwindcss -i ./web/static/scss/main.scss -o ./web/static/styles.css -c tailwind.config.cjs --minify && \
    curl -fsSL https://cdn.jsdelivr.net/npm/daisyui@latest/dist/full.css -o web/static/daisyui.css

RUN chmod +x ./scripts/run.sh
EXPOSE 8080
CMD ["./scripts/run.sh"]