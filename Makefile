.PHONY: all
.PHONY: install
.PHONY: format
.PHONY: format-check
.PHONY: lint
.PHONY: typecheck
.PHONY: test
.PHONY: check
.PHONY: ci
.PHONY: build
.PHONY: clean

UV ?= uv

all: check

install:
	$(UV) sync

format:
	$(UV) run ruff format .
	$(UV) run ruff check . --fix

format-check:
	$(UV) run ruff format . --check
	$(UV) run ruff check .

lint:
	$(UV) run ruff check .

typecheck:
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