FROM python:3.12-slim AS base
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
EXPOSE 8000
# Apply schema migrations, then serve. Idempotent: a no-op when already at head.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
