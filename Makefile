.DEFAULT_GOAL := help

.PHONY: help install lint format typecheck test build clean all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install package in editable mode with dev deps
	pip install -e ".[dev,evm]"
	pre-commit install

lint: ## Run ruff linter
	ruff check .

format: ## Run ruff formatter (auto-fix)
	ruff check --fix .
	ruff format .

typecheck: ## Run mypy type checker
	mypy src/x402_openai

test: ## Run pytest
	pytest

build: ## Build wheel and sdist
	python -m build

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info .mypy_cache .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

all: format lint typecheck test ## Run all checks (format → lint → typecheck → test)
