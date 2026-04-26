.DEFAULT_GOAL := help

UV ?= uv
CURIO := $(UV) run python -m curio

TRANSLATE_SMOKE_RUN ?= latest

.PHONY: help sync test translate-smoke translate-smoke-collect translate-smoke-evaluate translate-smoke-report lint lint-fix typecheck check cli-help build-wheel

help:
	@printf '%s\n' \
		'make sync                     Install or update project dependencies with uv' \
		'make test                     Run pytest with coverage' \
		'make translate-smoke          Run opt-in live Codex CLI translation smoke tests' \
		'make translate-smoke-collect  List opt-in live Codex CLI translation smoke tests' \
		'make translate-smoke-evaluate Run evaluator for TRANSLATE_SMOKE_RUN=latest' \
		'make translate-smoke-report   Publish report for TRANSLATE_SMOKE_RUN=latest' \
		'make lint                     Run Ruff' \
		'make lint-fix                 Run Ruff with autofix enabled' \
		'make typecheck                Run ty' \
		'make check                    Run lint, typecheck, and tests' \
		'make cli-help                 Show the Curio CLI help' \
		'make build-wheel              Build a wheel for local installation/testing'

sync:
	$(UV) sync

test:
	$(UV) run pytest

translate-smoke:
	CURIO_LIVE_CODEX_CLI_TESTS=1 $(UV) run pytest -m live_codex_cli -s --no-cov

translate-smoke-collect:
	CURIO_LIVE_CODEX_CLI_TESTS=1 $(UV) run pytest -m live_codex_cli --collect-only -q --no-cov

translate-smoke-evaluate:
	$(UV) run python tests/live_smoke_evaluator.py $(TRANSLATE_SMOKE_RUN)

translate-smoke-report:
	$(UV) run python tests/live_smoke_evaluator.py $(TRANSLATE_SMOKE_RUN) --prepare-only

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
