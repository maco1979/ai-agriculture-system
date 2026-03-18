FROM python:3.9-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-dev

COPY src/ ./src/

EXPOSE 8000

CMD ["python", "-m", "src.main"]