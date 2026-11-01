# =============================================================================
# Configuration & Tooling Resolution
# =============================================================================
.DEFAULT_GOAL := help

UV           ?= $(shell command -v uv 2>/dev/null)
UV_LINK_MODE ?= copy
VENV         ?= .venv
TARGET       ?= declusor
PLUGIN       ?=

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
# Project Paths
# =============================================================================
PLUGIN_DIRS      := $(patsubst %/pyproject.toml,%,$(wildcard plugins/*/pyproject.toml))
PLUGIN_TEST_DIRS := $(wildcard plugins/*/tests)
UNIT_TEST_DIRS   := $(filter-out %/__pycache__,$(wildcard tests/unit/*))

ifneq ($(strip $(PLUGIN)),)
    ifeq ($(filter plugins/$(PLUGIN),$(PLUGIN_DIRS)),)
        $(error Unknown PLUGIN='$(PLUGIN)'; available plugins: $(notdir $(PLUGIN_DIRS)))
    endif
    ifneq ($(filter declusor all,$(TARGET)),)
        $(error PLUGIN is only valid with TARGET=plugins or TARGET=plugin-assets)
    endif
endif

ifeq ($(TARGET),declusor)
    TARGET_PATH := .
    TEST_PATH := tests
else ifeq ($(TARGET),plugins)
    TARGET_PATH := $(if $(PLUGIN),plugins/$(PLUGIN),plugins)
    TEST_PATH := $(if $(PLUGIN),plugins/$(PLUGIN)/tests,plugins)
else ifeq ($(TARGET),plugin-assets)
    ASSET_PATH := $(if $(PLUGIN),plugins/$(PLUGIN)/assets,plugins)
else ifeq ($(TARGET),all)
else
    $(error Invalid TARGET='$(TARGET)'; use TARGET=declusor, plugins, plugin-assets, or all)
endif

# =============================================================================
# Phony Targets
# =============================================================================
.PHONY: help \
        install format compile test check package clean ci \
        labs-build labs-run labs-stop labs-clean labs-status \
        _install-declusor _install-plugins _format-declusor _format-plugins \
        _format-check-declusor _format-check-plugins _lint-declusor _lint-plugins \
        _lint-assets _type-check-declusor _type-check-plugins _compile-declusor \
        _compile-plugins _compile-assets _test-declusor _test-plugins _test-plugin \
        _check-declusor _check-plugins _check-assets _package-declusor _package-plugins

##@ Help

help: ## Display this help message
	@awk 'BEGIN { \
		FS = ":.*##"; \
		printf "\n\033[1mUsage:\033[0m\n  make \033[36m<target>\033[0m [TARGET=declusor|plugins|plugin-assets|all] [PLUGIN=<name>]\n" \
	} \
	/^[a-zA-Z0-9-]+:.*?##/ { \
		printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 \
	} \
	/^##@/ { \
		printf "\n\033[1m%s\033[0m\n", substr($$0, 5) \
	}' $(MAKEFILE_LIST)
	@printf "\nExamples:\n  make check\n  make check TARGET=plugins PLUGIN=py_socket\n  make check TARGET=plugin-assets\n  make package TARGET=all\n"

##@ Setup & Packaging

install: ## Install the selected TARGET (default: declusor)
ifeq ($(TARGET),declusor)
	$(MAKE) _install-declusor
else ifeq ($(TARGET),plugins)
	$(MAKE) _install-plugins
else ifeq ($(TARGET),all)
	$(MAKE) _install-declusor _install-plugins
else
	$(error TARGET=$(TARGET) does not support install)
endif

_install-declusor:
ifneq ($(strip $(UV)),)
	$(UV) sync --link-mode=$(UV_LINK_MODE)
else ifneq ($(wildcard $(VENV)),)
	$(EXEC)python -m pip install -e ".[dev,testing]"
else
	@echo "Notice: uv not found and $(VENV) does not exist; create $(VENV) or install uv."
endif

_install-plugins:
	@set -e; \
		if [ -n "$(PLUGIN)" ]; then \
			$(PIP_EDIT) "plugins/$(PLUGIN)"; \
		else \
			for dir in $(PLUGIN_DIRS); do \
				echo "==> Installing plugin $$dir..."; \
				$(PIP_EDIT) "$$dir"; \
			done; \
		fi

package: ## Build packages for the selected TARGET
ifeq ($(TARGET),declusor)
	$(MAKE) _package-declusor
else ifeq ($(TARGET),plugins)
	$(MAKE) _package-plugins
else ifeq ($(TARGET),all)
	$(MAKE) _package-declusor _package-plugins
else
	$(error TARGET=$(TARGET) does not support package)
endif

_package-declusor:
	$(call BUILD_CMD,.,)

_package-plugins:
	@set -e; \
		if [ -n "$(PLUGIN)" ]; then \
			echo "==> Building plugin plugins/$(PLUGIN)..."; \
			$(call BUILD_CMD,"plugins/$(PLUGIN)","plugins/$(PLUGIN)/dist"); \
		else \
			for dir in $(PLUGIN_DIRS); do \
				echo "==> Building plugin $$dir..."; \
				$(call BUILD_CMD,"$$dir","$$dir/dist"); \
			done; \
		fi

clean: ## Remove build artifacts and tool caches
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d \( -name "__pycache__" -o -name "*.egg-info" \) -prune -exec rm -rf {} + 2>/dev/null || true
	find plugins -mindepth 2 -maxdepth 2 -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true

##@ Quality & Static Analysis

format: ## Format the selected TARGET
ifeq ($(TARGET),declusor)
	$(MAKE) _format-declusor
else ifeq ($(TARGET),plugins)
	$(MAKE) _format-plugins
else ifeq ($(TARGET),all)
	$(MAKE) format TARGET=declusor
	$(MAKE) format TARGET=plugins
else
	$(error TARGET=$(TARGET) does not support format)
endif

_format-declusor:
	$(EXEC)ruff format .
	$(EXEC)ruff check . --fix

_format-plugins:
	$(EXEC)ruff format $(TARGET_PATH)
	$(EXEC)ruff check $(TARGET_PATH) --fix

_format-check-declusor:
	$(EXEC)ruff format . --check

_format-check-plugins:
	$(EXEC)ruff format $(TARGET_PATH) --check

_lint-declusor:
	$(EXEC)ruff check .

_lint-plugins:
	$(EXEC)ruff check $(TARGET_PATH)

_lint-assets:
	@command -v shellcheck >/dev/null || { echo "shellcheck is required for TARGET=plugin-assets"; exit 1; }
	@set -e; \
		for dir in $(if $(PLUGIN),plugins/$(PLUGIN)/assets,plugins/*/assets); do \
			[ -d "$$dir" ] || continue; \
			find "$$dir" -type f -name '*.sh' -exec shellcheck {} +; \
		done

_type-check-declusor:
	$(EXEC)mypy .

_type-check-plugins:
	$(EXEC)mypy $(TARGET_PATH)

compile: ## Compile Python files for the selected TARGET
ifeq ($(TARGET),declusor)
	$(MAKE) _compile-declusor
else ifeq ($(TARGET),plugins)
	$(MAKE) _compile-plugins
else ifeq ($(TARGET),plugin-assets)
	$(MAKE) _compile-assets
else ifeq ($(TARGET),all)
	$(MAKE) _compile-declusor _compile-plugins _compile-assets
endif

_compile-declusor:
	$(EXEC)python -m compileall -q .

_compile-plugins:
	$(EXEC)python -m compileall -q $(TARGET_PATH)

_compile-assets:
	@set -e; \
		for dir in $(if $(PLUGIN),plugins/$(PLUGIN)/assets,plugins/*/assets); do \
			[ -d "$$dir" ] || continue; \
			find "$$dir" -type f -name '*.py' -exec $(EXEC)python -m py_compile {} +; \
		done

##@ Testing & Verification

test: ## Test the selected TARGET
ifeq ($(TARGET),declusor)
	$(MAKE) _test-declusor
else ifeq ($(TARGET),plugins)
	$(MAKE) _test-plugin
else ifeq ($(TARGET),all)
	$(MAKE) _test-declusor _test-plugins
else
	$(error TARGET=$(TARGET) does not support test)
endif

_test-declusor:
	$(EXEC)pytest tests/unit
	$(EXEC)pytest tests/e2e

_test-plugins:
	@for dir in $(PLUGIN_TEST_DIRS); do \
		echo "==> Running plugin tests in $$dir..."; \
		$(EXEC)pytest "$$dir" || exit 1; \
	done

_test-plugin:
	@if [ -n "$(PLUGIN)" ]; then \
		$(EXEC)pytest "plugins/$(PLUGIN)/tests"; \
	else \
		$(MAKE) _test-plugins; \
	fi

check: ## Run all applicable checks for the selected TARGET
ifeq ($(TARGET),declusor)
	$(MAKE) _check-declusor
else ifeq ($(TARGET),plugins)
	$(MAKE) _check-plugins
else ifeq ($(TARGET),plugin-assets)
	$(MAKE) _check-assets
else ifeq ($(TARGET),all)
	$(MAKE) _check-declusor _check-plugins _check-assets
endif

_check-declusor:
	$(MAKE) _format-check-declusor _lint-declusor _type-check-declusor \
		_compile-declusor _test-declusor TARGET=declusor

_check-plugins:
	$(MAKE) _format-check-plugins _lint-plugins _type-check-plugins \
		_compile-plugins _test-plugin TARGET=plugins PLUGIN="$(PLUGIN)"

_check-assets:
	$(MAKE) _lint-assets _compile-assets TARGET=plugin-assets PLUGIN="$(PLUGIN)"

ci: ## Run the full local CI pipeline
	$(MAKE) check TARGET=all
	$(MAKE) package TARGET=all

##@ Declusor Labs

include docker/01-skiff/skiff.mk
include docker/02-draftsman/draftsman.mk
include docker/03-dockside/dockside.mk
include docker/04-leviathan/leviathan.mk

LABS := 01 02 03 04

labs-build: $(addprefix build-,$(LABS)) ## Build all challenge Docker images
labs-run: $(addprefix run-,$(LABS)) ## Start all lab containers in background
labs-stop: $(addprefix stop-,$(LABS)) ## Stop all running lab containers
labs-clean: $(addprefix clean-,$(LABS)) ## Stop and remove all lab containers and images
	@echo "[+] Declusor environment completely wiped."
labs-status: ## Display running state and ports of all lab containers
	@docker ps -a --filter "name=declusor-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
