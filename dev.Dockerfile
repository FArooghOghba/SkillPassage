FROM python:3.11.8-alpine3.18
LABEL maintainer="FAroogh"

# Python configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \

    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \

    # poetry
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \

    # virtualenv
    VIRTUAL_ENV="/app/.venv" \

    # Add poetry and venv to path
    PATH="/opt/poetry/bin:/app/.venv/bin:$PATH"

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/src /app/tests

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Copy scripts
COPY scripts /app/scripts/

# Install system dependencies and poetry dependencies in one layer
RUN apk add --no-cache \
    postgresql-client \
    postgresql-dev \
    build-base \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry install --no-root \
    && chmod +x /app/scripts/*

# Copy only necessary project files
COPY src /app/src/
COPY tests /app/tests/

EXPOSE 8000
