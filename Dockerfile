FROM python:3.12.8-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ADD pyproject.toml .
RUN uv pip install --system -r pyproject.toml
RUN uv pip install --system watchdog

ADD app/ /app

RUN chmod +x /app/start.sh
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["/app/start.sh"]
