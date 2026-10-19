# =============================================================================
# Configuration & Tooling Resolution
# =============================================================================
.DEFAULT_GOAL := help

UV           ?= $(shell command -v uv 2>/dev/null)
UV_LINK_MODE ?= copy
VENV         ?= .venv

ifneq ($(strip $(UV)),)
    EXEC      := $(UV) run 
    PIP_EDIT  := $(UV) pip install --no-deps -e
    BUILD_CMD  = $(UV) build $(1) $(if $(2),--out-dir $(2))
else
    EXEC      := $(if $(wildcard $(VENV)/bin),$(VENV)/bin/,)
    PIP_EDIT  := $(EXEC)python -m pip install --no-deps -e
    BUILD_CMD  = $(EXEC)python -m build $(if $(2),--outdir $(2)) $(1)
endif

# =============================================================================
# Project & Plugin Paths
# =============================================================================
PLUGIN           ?=
TARGET_PATH       = $(if $(PLUGIN),plugins/$(PLUGIN),.)
PLUGIN_PATH       = $(if $(PLUGIN),plugins/$(PLUGIN),plugins)
PLUGIN_TEST_PATH  = $(if $(PLUGIN),plugins/$(PLUGIN)/tests,plugins)

PLUGIN_DIRS      := $(patsubst %/pyproject.toml,%,$(wildcard plugins/*/pyproject.toml))
PLUGIN_TEST_DIRS := $(wildcard plugins/*/tests)
UNIT_TEST_DIRS   := $(filter-out %/__pycache__,$(wildcard tests/unit/*))

# =============================================================================
# Phony Targets
# =============================================================================
.PHONY: help \
        install install-plugins \
        check format format-check lint type-check \
        check-plugin format-plugin format-check-plugin lint-plugin type-check-plugin \
        test test-unit test-e2e test-plugins test-plugin \
        ci build build-plugins build-all clean \
        build-labs run-labs stop-labs clean-labs status-labs

##@ Help

help: ## Display this help message
	@awk 'BEGIN { \
		FS = ":.*##"; \
		printf "\n\033[1mUsage:\033[0m\n  make \033[36m<target>\033[0m [PLUGIN=<name>]\n" \
	} \
	/^[a-zA-Z0-9_-]+:.*?##/ { \
		printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 \
	} \
	/^##@/ { \
		printf "\n\033[1m%s\033[0m\n", substr($$0, 5) \
	}' $(MAKEFILE_LIST)

##@ Setup & Packaging

install: ## Sync dependencies and install plugins in editable mode
ifneq ($(strip $(UV)),)
	$(UV) sync --link-mode=$(UV_LINK_MODE)
	$(MAKE) install-plugins
else ifneq ($(wildcard $(VENV)),)
	$(EXEC)python -m pip install -e ".[dev,testing]"
	$(MAKE) install-plugins
else
	@echo "Notice: uv not found and $(VENV) does not exist; create $(VENV) or install uv."
endif

install-plugins: ## Install all plugins in editable mode
	@for dir in $(PLUGIN_DIRS); do \
		echo "==> Installing plugin $$dir..."; \
		$(PIP_EDIT) "$$dir"; \
	done

build: ## Build root package
	$(call BUILD_CMD,.,)

build-plugins: ## Build all plugin packages into plugins/*/dist
	@for dir in $(PLUGIN_DIRS); do \
		echo "==> Building plugin $$dir..."; \
		$(call BUILD_CMD,"$$dir","$$dir/dist") || exit 1; \
	done

build-all: build build-plugins ## Build root and all plugin packages

clean: ## Remove build artifacts and tool caches
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d \( -name "__pycache__" -o -name "*.egg-info" \) -prune -exec rm -rf {} + 2>/dev/null || true
	find plugins -mindepth 2 -maxdepth 2 -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true

##@ Quality & Static Analysis

check: format-check lint type-check test ## Run format-check, lint, type-check, and test

format: ## Auto-format and autofix lint issues (supports PLUGIN=<name>)
	$(EXEC)ruff format $(TARGET_PATH)
	$(EXEC)ruff check $(TARGET_PATH) --fix

format-check: ## Check code formatting with ruff (supports PLUGIN=<name>)
	$(EXEC)ruff format $(TARGET_PATH) --check

lint: ## Run ruff linter (supports PLUGIN=<name>)
	$(EXEC)ruff check $(TARGET_PATH)

type-check: ## Run mypy static type checker (supports PLUGIN=<name>)
	$(EXEC)mypy $(TARGET_PATH)

ci: check build ## Run full CI pipeline (checks + build)

# Plugin-scoped aliases
check-plugin: format-check-plugin lint-plugin type-check-plugin test-plugin ## Run all checks for plugins (or single PLUGIN=<name>)

format-plugin: ## Format plugins (or single PLUGIN=<name>)
	$(EXEC)ruff format $(PLUGIN_PATH)
	$(EXEC)ruff check $(PLUGIN_PATH) --fix

format-check-plugin: ## Check formatting for plugins (or single PLUGIN=<name>)
	$(EXEC)ruff format $(PLUGIN_PATH) --check

lint-plugin: ## Lint plugins (or single PLUGIN=<name>)
	$(EXEC)ruff check $(PLUGIN_PATH)

type-check-plugin: ## Type-check plugins (or single PLUGIN=<name>)
	$(EXEC)mypy $(PLUGIN_PATH)

##@ Testing

test: test-unit test-e2e test-plugins ## Run unit, e2e, and plugin test suites

test-unit: ## Run unit test suites
	@for dir in $(UNIT_TEST_DIRS); do \
		if [ -d "$$dir" ]; then \
			echo "==> Running unit tests in $$dir..."; \
			$(EXEC)pytest "$$dir" || exit 1; \
		fi; \
	done

test-e2e: ## Run end-to-end tests
	@if [ -d "tests/e2e" ]; then \
		echo "==> Running e2e tests..."; \
		$(EXEC)pytest tests/e2e; \
	fi

test-plugins: ## Run tests across all plugins
	@for dir in $(PLUGIN_TEST_DIRS); do \
		echo "==> Running plugin tests in $$dir..."; \
		$(EXEC)pytest "$$dir" || exit 1; \
	done

test-plugin: ## Run tests for a specific plugin (PLUGIN=<name>)
	$(EXEC)pytest $(PLUGIN_TEST_PATH)

##@ Declusor Labs

include docker/01-skiff/skiff.mk
include docker/02-draftsman/draftsman.mk
include docker/03-dockside/dockside.mk
include docker/04-leviathan/leviathan.mk

LABS := 01 02 03 04

build-labs: $(addprefix build-,$(LABS)) ## Build all 4 challenge Docker images
run-labs:   $(addprefix run-,$(LABS)) ## Start all 4 containers in background
stop-labs:  $(addprefix stop-,$(LABS)) ## Stop all running containers

clean-labs: $(addprefix clean-,$(LABS)) ## Stop and remove all containers and built images
	@echo "[+] Declusor environment completely wiped."

status-labs: ## Display running state and ports of all containers
	@docker ps -a --filter "name=declusor-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"