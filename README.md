# API for library
To build and run containers run:
```commandline
docker-compose build --no-cache

docker-compose up
```
Application should be available on port 8000 on localhost.

To run tests create virtual environment with uv and run:
```commandline
uv sync --dev
uv run pytest
```