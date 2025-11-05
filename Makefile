.PHONY: install lock build test lint clean

install:
	uv sync --dev

lock:
	uv lock

build:
	uv build

test:
	uv run pytest

lint:
	uv run ruff format .
	uv run ruff check . --fix

clean:
	rm -rf .pytest_cache .ruff_cache dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete

