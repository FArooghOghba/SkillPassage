#!/bin/sh
set -e

echo "Running development server..."
uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir /app/src
