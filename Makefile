.PHONY: all
.PHONY: install
.PHONY: reinstall
.PHONY: lock
.PHONY: format
.PHONY: format-check
.PHONY: lint
.PHONY: type-check
.PHONY: test
.PHONY: check
.PHONY: ci
.PHONY: build
.PHONY: clean

UV ?= uv
UV_LINK_MODE ?= copy

all: check

install:
	$(UV) sync --link-mode=$(UV_LINK_MODE)

reinstall:
	if [ -d ".venv" ]; then rm -rf ".venv"; fi
	$(MAKE) install

lock:
	$(UV) lock

format:
	$(UV) run ruff format .
	$(UV) run ruff check . --fix

format-check:
	$(UV) run ruff format . --check
	$(UV) run ruff check .

lint:
	$(UV) run ruff check .

type-check:
	$(UV) run mypy .

test:
	$(UV) run pytest

check: format-check lint typecheck test

ci: check build

build:
	$(UV) build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/