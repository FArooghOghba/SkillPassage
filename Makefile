.PHONY: install-pre-commit-hooks check-pre-commit docker-compose-build docker-compose-run-test docker-compose-down

# Docker compose files
DC_DEV := docker-compose.dev.yml

install-pre-commit-hooks:
	pre-commit uninstall && pre-commit clean && pre-commit install

check-pre-commit:
	pre-commit run --all-files

# Start all services except test
docker-compose-build:
	docker compose -f $(DC_DEV) up -d db pgadmin fastapi

# Start only test environment
docker-compose-run-test:
	docker compose -f $(DC_DEV) up -d test_db
	docker compose -f $(DC_DEV) run --rm test

# Stop services
docker-compose-down:
	docker compose -f $(DC_DEV) down
