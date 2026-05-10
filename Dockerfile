FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY . .

EXPOSE 8000

RUN chmod +x scripts/entrypoint.sh

CMD ["./scripts/entrypoint.sh"]