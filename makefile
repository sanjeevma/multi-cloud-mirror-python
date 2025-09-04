# Makefile for Multi-Cloud Mirror

.PHONY: help install dev-install test test-coverage lint format typecheck clean build publish docker-build docker-run validate

# Default target
help:
	@echo "Multi-Cloud Mirror - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  setup        Run setup script for cloud tools"
	@echo ""
	@echo "Development:"
	@echo "  test         Run all tests"
	@echo "  test-coverage Run tests with coverage report"
	@echo "  lint         Run linting checks"
	@echo "  format       Auto-format code"
	@echo "  typecheck    Run type checking"
	@echo ""
	@echo "Application:"
	@echo "  validate     Validate setup and configuration"
	@echo "  mirror       Run image mirroring"
	@echo "  debug        Run with debug logging"
	@echo ""
	@echo "Build:"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build distribution packages"
	@echo "  publish      Publish to PyPI"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run in Docker container"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e .[dev]

setup:
	python scripts/setup.py

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=core --cov=registries --cov=utils --cov-report=html --cov-report=term

test-watch:
	pytest-watch tests/

# Code quality
lint:
	flake8 core/ registries/ utils/ main.py
	mypy core/ registries/ utils/ main.py

format:
	black core/ registries/ utils/ main.py tests/
	isort core/ registries/ utils/ main.py tests/

typecheck:
	mypy core/ registries/ utils/ main.py

# Application commands
validate:
	python main.py --validate

mirror:
	python main.py

debug:
	python main.py --debug

mirror-example:
	python main.py -f examples/example-list.txt -j 2 -d

# Build and publish
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -name __pycache__ -delete
	find . -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	twine upload dist/*

publish-test: build
	twine upload --repository testpypi dist/*

# Docker
docker-build:
	docker build -t multi-cloud-mirror:latest .

docker-run:
	docker run --rm -it \
		--env-file .env \
		-v $(PWD)/config:/app/config \
		-v ~/.aws:/root/.aws:ro \
		-v ~/.config/gcloud:/root/.config/gcloud:ro \
		-v ~/.azure:/root/.azure:ro \
		multi-cloud-mirror:latest

docker-validate:
	docker run --rm -it \
		--env-file .env \
		-v $(PWD)/config:/app/config \
		-v ~/.aws:/root/.aws:ro \
		-v ~/.config/gcloud:/root/.config/gcloud:ro \
		-v ~/.azure:/root/.azure:ro \
		multi-cloud-mirror:latest \
		python main.py --validate

# Development helpers
dev-setup: dev-install
	pre-commit install

check: lint typecheck test

ci: check test-coverage

# Cleanup
clean-all: clean
	docker system prune -f
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/

# Release helpers
bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

bump-major:
	bumpversion major

# Local registry for testing
start-local-registry:
	docker-compose -f examples/docker-compose.yml up -d local-registry registry-ui

stop-local-registry:
	docker-compose -f examples/docker-compose.yml down
