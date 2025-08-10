.PHONY: setup test lint format typecheck precommit ci

PY ?= python

setup:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e .[dev]

test:
	$(PY) -m pytest -q

lint:
	ruff .
	black --check .

format:
	ruff --fix .
	black .

typecheck:
	mypy .

precommit:
	pre-commit run --all-files

ci: lint typecheck test

