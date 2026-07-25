FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root --no-interaction --no-ansi

COPY . /app

CMD ["sh", "-c", "poetry run alembic upgrade head && uvicorn main:app --host", "0.0.0.0", "--port", "8000"]

