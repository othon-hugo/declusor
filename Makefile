.PHONY: all
.PHONY: install
.PHONY: install-plugins
.PHONY: reinstall
.PHONY: compile
.PHONY: lock
.PHONY: format
.PHONY: format-check
.PHONY: lint
.PHONY: type-check
.PHONY: test
.PHONY: test-unit
.PHONY: test-e2e
.PHONY: check
.PHONY: test-plugins
.PHONY: test-plugin
.PHONY: type-check-plugin
.PHONY: lint-plugin
.PHONY: format-plugin
.PHONY: format-check-plugin
.PHONY: check-plugin
.PHONY: check-shell-assets
.PHONY: check-py-assets
.PHONY: build-plugins
.PHONY: build-all
.PHONY: ci
.PHONY: build
.PHONY: clean

UV ?= $(shell command -v uv 2>/dev/null)
UV_LINK_MODE ?= copy

ifneq ($(strip $(UV)),)
EXEC ?= $(UV) run 
else
VENV ?= .venv
EXEC ?= $(VENV)/bin/
endif

PLUGIN ?=
PLUGIN_PATH = $(if $(PLUGIN),plugins/$(PLUGIN),plugins)
PLUGIN_TEST_PATH = $(if $(PLUGIN),plugins/$(PLUGIN)/tests,plugins)

all: check

install:
ifneq ($(strip $(UV)),)
	$(UV) sync --link-mode=$(UV_LINK_MODE)
	$(MAKE) install-plugins
else
	@if [ -d ".venv" ]; then \
		$(EXEC)pip install -e ".[dev,testing]" 2>/dev/null || $(EXEC)python -m pip install -e ".[dev,testing]" 2>/dev/null || true; \
		$(MAKE) install-plugins; \
	else \
		echo "Notice: uv not found; ensure dependencies are installed in .venv"; \
	fi
endif

install-plugins:
ifneq ($(strip $(UV)),)
	@for p in plugins/*; do \
		if [ -f "$$p/pyproject.toml" ]; then \
			$(UV) pip install --no-deps -e "$$p"; \
		fi; \
	done
else
	@for p in plugins/*; do \
		if [ -f "$$p/pyproject.toml" ]; then \
			$(EXEC)pip install --no-deps -e "$$p" 2>/dev/null || $(EXEC)python -m pip install --no-deps -e "$$p" 2>/dev/null || true; \
		fi; \
	done
endif

reinstall:
	if [ -d ".venv" ]; then rm -rf ".venv"; fi
	$(MAKE) install

compile:
	$(EXEC)python -m compileall -q src tests plugins

lock:
ifneq ($(strip $(UV)),)
	$(UV) lock
else
	@echo "Notice: uv not found; cannot update lockfile."
endif

format:
	$(EXEC)ruff format .
	$(EXEC)ruff check . --fix

format-check:
	$(EXEC)ruff format . --check
	$(EXEC)ruff check .

lint:
	$(EXEC)ruff check .

type-check:
	$(EXEC)mypy .

test: test-unit test-e2e test-plugins

test-unit:
	@for dir in tests/unit/*; do \
		if [ -d "$$dir" ] && [ "$$(basename "$$dir")" != "__pycache__" ]; then \
			echo "==> Running unit tests in $$dir..."; \
			$(EXEC)pytest "$$dir" || exit 1; \
		fi; \
	done

test-e2e:
	@if [ -d "tests/e2e" ]; then \
		echo "==> Running e2e tests..."; \
		$(EXEC)pytest tests/e2e || exit 1; \
	fi

check: format-check lint type-check test

test-plugins:
	@for p in plugins/*; do \
		if [ -d "$$p/tests" ]; then \
			echo "==> Running plugin tests in $$p/tests..."; \
			$(EXEC)pytest "$$p/tests" || exit 1; \
		fi; \
	done

test-plugin:
	$(EXEC)pytest $(PLUGIN_TEST_PATH)

type-check-plugin:
	$(EXEC)mypy $(PLUGIN_PATH)

lint-plugin:
	$(EXEC)ruff check $(PLUGIN_PATH)

format-plugin:
	$(EXEC)ruff format $(PLUGIN_PATH)
	$(EXEC)ruff check $(PLUGIN_PATH) --fix

format-check-plugin:
	$(EXEC)ruff format $(PLUGIN_PATH) --check
	$(EXEC)ruff check $(PLUGIN_PATH)

check-plugin: format-check-plugin lint-plugin type-check-plugin test-plugin

check-shell-assets:
	@command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck is required" >&2; exit 1; }
	@cd plugins/shell_socket && find assets -type f -name '*.sh' -print0 | xargs -0 shellcheck -s bash -S info

check-py-assets:
	$(EXEC)ruff check --config plugins/py_socket/assets/ruff.toml plugins/py_socket/assets
	$(EXEC)python -m compileall -q plugins/py_socket/assets

ci: check build

build:
ifneq ($(strip $(UV)),)
	$(UV) build
else
	python3 -m build
endif

build-plugins:
ifneq ($(strip $(UV)),)
	@for p in plugins/*; do \
		if [ -f "$$p/pyproject.toml" ]; then \
			$(UV) build "$$p" --out-dir "$$p/dist"; \
		fi; \
	done
else
	@for p in plugins/*; do \
		if [ -f "$$p/pyproject.toml" ]; then \
			python3 -m build --outdir "$$p/dist" "$$p"; \
		fi; \
	done
endif

build-all: build build-plugins

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find plugins -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true