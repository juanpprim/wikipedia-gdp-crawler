.PHONY: setup test lint type-check coverage format clean run

# Default Python interpreter
PYTHON = python
VENV = .venv

setup:
	poetry install

format:
	poetry run ruff format src tests

lint:
	poetry run ruff check src tests

type-check:
	poetry run mypy src tests

test:
	poetry run pytest

test-verbose:
	poetry run pytest -v

coverage:
	poetry run coverage run -m pytest
	poetry run coverage report -m
	poetry run coverage html

run:
	poetry run wiki-gdp

clean:
	rm -rf .coverage htmlcov .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +

all: setup lint type-check test 