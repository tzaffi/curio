.DEFAULT_GOAL := help

UV ?= uv
CURIO := $(UV) run python -m curio

.PHONY: help sync test lint lint-fix typecheck check cli-help build-wheel

help:
	@printf '%s\n' \
		'make sync        Install or update project dependencies with uv' \
		'make test        Run pytest with coverage' \
		'make lint        Run Ruff' \
		'make lint-fix    Run Ruff with autofix enabled' \
		'make typecheck   Run ty' \
		'make check       Run lint, typecheck, and tests' \
		'make cli-help    Show the Curio CLI help' \
		'make build-wheel Build a wheel for local installation/testing'

sync:
	$(UV) sync

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

lint-fix:
	$(UV) run ruff check . --fix

typecheck:
	$(UV) run ty check

check: lint typecheck test

cli-help:
	$(CURIO) --help

build-wheel:
	$(UV) build --wheel
