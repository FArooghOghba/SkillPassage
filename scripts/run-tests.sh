#!/bin/sh
set -e

echo "Running tests..."
pytest \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:/app/htmlcov \
    --junit-xml=/app/test-results/junit.xml
