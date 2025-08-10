.PHONY: setup test lint format typecheck precommit ci examples itest

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

examples:
	$(PY) examples/basic_usage.py
	$(PY) examples/tools_demo.py

itest:
	@if command -v dotenv >/dev/null 2>&1; then \
	  echo "[itest] Using dotenv to load .env"; \
	  dotenv -f .env run -- $(PY) -m pytest -q tests/integration || \
	    (echo "[itest] dotenv CLI failed. Tip: pip install 'python-dotenv[cli]'"; \
	     echo "[itest] Falling back to running without .env"; \
	     $(PY) -m pytest -q tests/integration); \
	else \
	  echo "[itest] dotenv CLI not found; running without .env"; \
	  echo "[itest] Tip: pip install 'python-dotenv[cli]' to load .env automatically"; \
	  $(PY) -m pytest -q tests/integration; \
	fi


itest-openai:
	@if command -v dotenv >/dev/null 2>&1; then 	  dotenv -f .env run -- $(PY) -m pytest -q tests/integration/test_openai_end_to_end.py; 	else 	  $(PY) -m pytest -q tests/integration/test_openai_end_to_end.py; 	fi

itest-anthropic:
	@if command -v dotenv >/dev/null 2>&1; then 	  ALLOY_IT_MODEL?=claude-3.5-sonnet; 	  dotenv -f .env run -- env ALLOY_IT_MODEL=$$ALLOY_IT_MODEL $(PY) -m pytest -q tests/integration/test_anthropic_end_to_end.py; 	else 	  ALLOY_IT_MODEL?=claude-3.5-sonnet; 	  env ALLOY_IT_MODEL=$$ALLOY_IT_MODEL $(PY) -m pytest -q tests/integration/test_anthropic_end_to_end.py; 	fi

itest-gemini:
	@if command -v dotenv >/dev/null 2>&1; then 	  ALLOY_IT_MODEL?=gemini-1.5-pro; 	  dotenv -f .env run -- env ALLOY_IT_MODEL=$$ALLOY_IT_MODEL $(PY) -m pytest -q tests/integration/test_gemini_end_to_end.py; 	else 	  ALLOY_IT_MODEL?=gemini-1.5-pro; 	  env ALLOY_IT_MODEL=$$ALLOY_IT_MODEL $(PY) -m pytest -q tests/integration/test_gemini_end_to_end.py; 	fi

itest-ollama:
	@if command -v dotenv >/dev/null 2>&1; then 	  ALLOY_IT_MODEL?=ollama:gpt-oss; 	  dotenv -f .env run -- env ALLOY_IT_MODEL=$$ALLOY_IT_MODEL $(PY) -m pytest -q tests/integration/test_ollama_end_to_end.py; 	else 	  ALLOY_IT_MODEL?=ollama:gpt-oss; 	  env ALLOY_IT_MODEL=$$ALLOY_IT_MODEL $(PY) -m pytest -q tests/integration/test_ollama_end_to_end.py; 	fi
