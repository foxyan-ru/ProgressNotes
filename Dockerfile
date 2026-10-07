# NOT built or run as part of scaffolding this project.
# A starting point for local development once the app has been wired up
# and verified to run.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

RUN pip install uv && uv sync --no-dev

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
