.PHONY: all
.PHONY: install
.PHONY: reinstall
.PHONY: compile
.PHONY: lock
.PHONY: format
.PHONY: format-check
.PHONY: lint
.PHONY: type-check
.PHONY: test
.PHONY: check
.PHONY: test-plugins
.PHONY: test-plugin
.PHONY: type-check-plugin
.PHONY: lint-plugin
.PHONY: format-plugin
.PHONY: format-check-plugin
.PHONY: check-plugin
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
else
	@echo "Notice: uv not found; ensure dependencies are installed in .venv"
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

test:
	$(EXEC)pytest

check: format-check lint type-check test

test-plugins:
	$(EXEC)pytest plugins/

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

ci: check build

build:
ifneq ($(strip $(UV)),)
	$(UV) build
else
	python3 -m build
endif

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find plugins -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true