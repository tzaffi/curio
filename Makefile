.DEFAULT_GOAL := help

UV ?= uv
CURIO := $(UV) run python -m curio

TRANSLATE_SMOKE_RUN ?= latest
TEXTIFY_SMOKE_RUN ?= latest
OPTS ?=
TEXT ?=
export TEXT

.PHONY: help sync test translate-smoke translate-smoke-collect translate-smoke-evaluate translate-smoke-report textify-smoke textify-smoke-collect textify-smoke-evaluate textify-smoke-report lint lint-fix typecheck check curio cli-help translate translate-genius translate-help textify-help build-wheel

help:
	@printf '%s\n' \
		'make sync                     Install or update project dependencies with uv' \
		'make test                     Run pytest with coverage' \
		'make curio ARGS="..."         Run Curio CLI with arbitrary arguments' \
		'make translate                 Run curio translate; pass TEXT="..." and/or OPTS="..."' \
		'make translate-genius          Run curio translate with translator_codex_gpt_55' \
		'make translate-smoke          Run opt-in live Codex CLI translation smoke tests' \
		'make translate-smoke-collect  List opt-in live Codex CLI translation smoke tests' \
		'make translate-smoke-evaluate Run evaluator for TRANSLATE_SMOKE_RUN=latest' \
		'make translate-smoke-report   Publish report for TRANSLATE_SMOKE_RUN=latest' \
		'make textify-smoke            Run opt-in live Codex CLI textify smoke tests' \
		'make textify-smoke-collect    List opt-in live Codex CLI textify smoke tests' \
		'make textify-smoke-evaluate   Run evaluator for TEXTIFY_SMOKE_RUN=latest' \
		'make textify-smoke-report     Publish report for TEXTIFY_SMOKE_RUN=latest' \
		'make lint                     Run Ruff' \
		'make lint-fix                 Run Ruff with autofix enabled' \
		'make typecheck                Run ty' \
		'make check                    Run lint, typecheck, and tests' \
		'make cli-help                 Show the Curio CLI help' \
		'make translate-help           Show the curio translate help' \
		'make textify-help             Show the curio textify help' \
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

textify-smoke:
	CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS=1 $(UV) run pytest -m live_codex_cli_textify -s --no-cov

textify-smoke-collect:
	CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS=1 $(UV) run pytest -m live_codex_cli_textify --collect-only -q --no-cov

textify-smoke-evaluate:
	$(UV) run python tests/textify_smoke_evaluator.py $(TEXTIFY_SMOKE_RUN)

textify-smoke-report:
	$(UV) run python tests/textify_smoke_evaluator.py $(TEXTIFY_SMOKE_RUN) --prepare-only

lint:
	$(UV) run ruff check .

lint-fix:
	$(UV) run ruff check . --fix

typecheck:
	$(UV) run ty check

check: lint typecheck test

curio:
	$(CURIO) $(ARGS)

cli-help:
	$(CURIO) --help

translate:
	@if [ -n "$$TEXT" ]; then \
		printf '%s' "$$TEXT" | $(CURIO) translate $(OPTS); \
	else \
		$(CURIO) translate $(OPTS); \
	fi

translate-genius:
	@if [ -n "$$TEXT" ]; then \
		printf '%s' "$$TEXT" | $(CURIO) translate $(OPTS) --llm-caller translator_codex_gpt_55; \
	else \
		$(CURIO) translate $(OPTS) --llm-caller translator_codex_gpt_55; \
	fi

translate-help:
	$(CURIO) translate --help

textify-help:
	$(CURIO) textify --help

build-wheel:
	$(UV) build --wheel
