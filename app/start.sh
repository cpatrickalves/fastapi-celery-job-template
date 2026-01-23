#!/bin/sh

# Uncomment next line to automatically apply Alembic database
# migrations (currently is done automatically on FastAPI startup)
# alembic upgrade head

exec uvicorn main:app --host 0.0.0.0 --port 8080