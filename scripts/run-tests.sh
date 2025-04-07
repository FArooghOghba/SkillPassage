#!/bin/sh
set -e

echo "Updating dependencies..."
poetry update

echo "Running database migrations for test database..."
poetry run alembic upgrade head

echo "Running tests..."

poetry run pytest \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Tests completed successfully!"
else
    echo "Tests failed!"
    exit 1
fi
