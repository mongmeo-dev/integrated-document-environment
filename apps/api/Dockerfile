FROM python:3.14-slim AS builder

ENV POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN python -m pip install --no-cache-dir poetry==2.2.1

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction

FROM python:3.14-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src

USER app
EXPOSE 8000

CMD ["uvicorn", "ide_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
