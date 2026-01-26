FROM python:3.12.8-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

ADD pyproject.toml .
RUN uv pip install --system -r pyproject.toml
RUN uv pip install --system watchdog

ADD app/ /code/app

RUN chown -R appuser:appuser /code

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
