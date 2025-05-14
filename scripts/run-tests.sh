#!/bin/sh
set -e

# Load environment variables from .env.test to get DB connection details
# This is crucial if your psql commands need them and they aren't globally available
# in the 'test' container's environment by default (though env_file in docker-compose should handle it)
# If .env.test is already sourced by the container, this might be redundant
# but it's safer to be explicit.
if [ -f .env.test ]; then
    export "$(cat .env.test | sed 's/#.*//g' | xargs)"
fi

echo "Preparing test database..."

# Use psql to connect to the 'postgres' database (or another default db)
# to drop and recreate the test database.
# The 'test_db' service name from docker-compose is the hostname.
PG_HOST=${POSTGRES_HOST:-test_db} # Use POSTGRES_HOST from .env.test if set, else default to service name
PG_USER=${POSTGRES_USER:-skillpassage_test}
DB_NAME=${POSTGRES_DB:-skillpassage_test}

# Set PG_PASSWORD environment variable specifically for the psql commands
# This value comes from POSTGRES_PASSWORD set by docker-compose via .env.test
export PGPASSWORD="${POSTGRES_PASSWORD:-skillpassage_test}"

echo "Attempting to drop database: ${DB_NAME} on host ${PG_HOST}..."
poetry run psql -h "${PG_HOST}" -U "${PG_USER}" -d postgres -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";"
# Note: PGPASSWORD is set via poetry run's environment or needs to be exported explicitly
# For psql, it often looks for PGPASSWORD env var.
# If your .env.test has POSTGRES_PASSWORD, poetry run should pass it.

echo "Attempting to create database: ${DB_NAME} on host ${PG_HOST}..."
poetry run psql -h "${PG_HOST}" -U "${PG_USER}" -d postgres -c "CREATE DATABASE \"${DB_NAME}\";"

# Unset PGPASSWORD after use (good practice, though maybe less critical in a short-lived script)
unset PGPASSWORD


echo "Running database migrations for test database..."
# poetry run alembic will use DATABASE_URL which includes the password,
# or if alembic's underlying connection also uses libpq, PGPASSWORD might be used if set.
# However, DATABASE_URL is more direct for SQLAlchemy/Alembic.
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
