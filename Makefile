.PHONY: setup test lint format typecheck precommit prepush verify ci \
        examples-quick examples-openai examples-anthropic examples-gemini examples-ollama \
        smoke-examples \
        itest docs-serve docs-build dist release docs-sync-brand

PY ?= python

setup:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e .[dev]

test:
	$(PY) -m pytest -q

lint:
	ruff check .
	@if command -v black >/dev/null 2>&1; then \
	  black --check .; \
	else \
	  echo "[lint] black not found; skipping black check"; \
	fi

format:
	ruff check --fix .
	@if command -v black >/dev/null 2>&1; then \
	  black .; \
	else \
	  echo "[format] black not found; skipping black format"; \
	fi

typecheck:
	mypy .

precommit:
	pre-commit run --all-files

prepush:
	pre-commit run --all-files --hook-stage pre-push --show-diff-on-failure

verify: format typecheck

ci: lint typecheck test

# Run a few fast, provider-agnostic examples with the fake backend
examples-quick:
	@echo "[examples] Running quick smoke tests with ALLOY_BACKEND=fake"
	ALLOY_BACKEND=fake $(PY) examples/10-commands/01_first_command.py
	ALLOY_BACKEND=fake $(PY) examples/20-typed/02_dataclass_output.py
	ALLOY_BACKEND=fake $(PY) examples/30-tools/01_simple_tool.py

# Provider-specific invoice extraction examples (require API keys)
examples-openai:
	@if command -v dotenv >/dev/null 2>&1; then \
	  ALLOY_MODEL?=gpt-5-mini; \
	  dotenv -f .env run -- env ALLOY_MODEL=$$ALLOY_MODEL $(PY) examples/70-providers/01_same_task_openai.py; \
	else \
	  ALLOY_MODEL?=gpt-5-mini; \
	  env ALLOY_MODEL=$$ALLOY_MODEL $(PY) examples/70-providers/01_same_task_openai.py; \
	fi

examples-anthropic:
	@if command -v dotenv >/dev/null 2>&1; then \
	  ALLOY_MODEL?=claude-sonnet-4-20250514; \
	  ALLOY_MAX_TOKENS?=512; \
	  dotenv -f .env run -- env ALLOY_MODEL=$$ALLOY_MODEL ALLOY_MAX_TOKENS=$$ALLOY_MAX_TOKENS $(PY) examples/70-providers/02_same_task_anthropic.py; \
	else \
	  ALLOY_MODEL?=claude-sonnet-4-20250514; \
	  ALLOY_MAX_TOKENS?=512; \
	  env ALLOY_MODEL=$$ALLOY_MODEL ALLOY_MAX_TOKENS=$$ALLOY_MAX_TOKENS $(PY) examples/70-providers/02_same_task_anthropic.py; \
	fi

examples-gemini:
	@if command -v dotenv >/dev/null 2>&1; then \
	  ALLOY_MODEL?=gemini-2.5-flash; \
	  dotenv -f .env run -- env ALLOY_MODEL=$$ALLOY_MODEL $(PY) examples/70-providers/03_same_task_gemini.py; \
	else \
	  ALLOY_MODEL?=gemini-2.5-flash; \
	  env ALLOY_MODEL=$$ALLOY_MODEL $(PY) examples/70-providers/03_same_task_gemini.py; \
	fi

examples-ollama:
	@echo "[examples] Ensure a local model is running: e.g., 'ollama run <model>'"
	@if command -v dotenv >/dev/null 2>&1; then \
	  dotenv -f .env run -- $(PY) examples/70-providers/04_same_task_ollama.py; \
	else \
	  $(PY) examples/70-providers/04_same_task_ollama.py; \
	fi

# CI-friendly smoketest (fake backend; no provider keys)
smoke-examples:
	ALLOY_BACKEND=fake $(PY) scripts/smoke_examples.py

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
docs-serve:
	@if command -v mkdocs >/dev/null 2>&1; then \
	  mkdocs serve -a 127.0.0.1:8000; \
	else \
	  echo "[docs] mkdocs not found. Try: pip install 'alloy-ai[docs]'"; \
	fi

docs-build: docs-sync-brand
	@if command -v mkdocs >/dev/null 2>&1; then \
	  mkdocs build --strict; \
	else \
	  echo "[docs] mkdocs not found. Try: pip install 'alloy-ai[docs]'"; \
	fi
dist:
	@python -m pip install --upgrade build >/dev/null 2>&1 || true
	python -m build
	@ls -lh dist || true

release:
	@echo "Create and push a tag to publish via GitHub Actions (trusted publishing):"
	@echo "  git tag v$${VERSION:-0.1.1} && git push origin v$${VERSION:-0.1.1}"
	@echo "Ensure PyPI trusted publishing is configured for this repo under the 'alloy-ai' project."
docs-sync-brand:
	@if command -v $(PY) >/dev/null 2>&1; then \
	  $(PY) scripts/sync_brand_assets.py || true; \
	else \
	  echo "[docs] python not found; skipping brand asset sync"; \
	fi
