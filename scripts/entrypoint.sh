#!/bin/bash

uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000 --host 0.0.0.0