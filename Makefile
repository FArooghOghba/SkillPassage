.PHONY: install-pre-commit-hooks check-pre-commit \
		 docker-compose-build docker-compose-down \
		 run-pytest \
		 alembic-migrations alembic-migrate

# Docker compose files
DC_DEV := docker-compose.dev.yml

install-pre-commit-hooks:
	pre-commit uninstall && pre-commit clean && pre-commit install

check-pre-commit:
	pre-commit run --all-files

# Start all services except test
docker-compose-build:
	docker compose -f $(DC_DEV) up -d db test_db pgadmin fastapi

# Start only test environment
run-pytest:
	docker compose -f $(DC_DEV) run --rm test

# Stop services
docker-compose-down:
	docker compose -f $(DC_DEV) down

# Generate the Migration Script
alembic-migrations:
	docker compose -f docker-compose.dev.yml exec fastapi sh -c \
	'alembic revision -m $(message) --autogenerate'

# Generate the Migrate Script
alembic-migrate:
	docker compose -f docker-compose.dev.yml exec fastapi sh -c \
	'alembic upgrade head'
