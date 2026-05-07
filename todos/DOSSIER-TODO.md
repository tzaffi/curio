# Curio Dossier Implementation TODO

## Purpose

Track the implementation work needed to build the v1 `dossier` stage described
in `DOSSIER.md`.

`DOSSIER.md` is the normative behavior spec. This document is an implementation
plan and may name code files, tests, schemas, and follow-up docs that need to
change.

## Constraints

- Keep `DossierProcessor` deterministic in v1.
- Do not add dossier-side LLM summaries, rankings, labels, or evaluation
  judgments.
- Do not persist raw file bytes or unrestricted duplicate source text in the
  dossier snapshot.
- Do not overwrite or update existing ledger rows or artifacts.
- Keep visible `dossiers` rows compact.
- Preserve warnings and evidence limit settings inside `dossier_snapshot`.

## Target Behavior

- `downloads -> textify -> translate -> dossier -> evaluate`
- `dossiers` ledger columns: `Date`, `X Date`, `iMsgX`, `Status`, `Object`
- `DossierProcessStatus`: `assembled`, `no_evidence`, `failed`
- `assembled` persists a dossier artifact and emits an `output_source`
- `no_evidence` appends a terminal ledger row with blank `Object` and no
  evaluation `output_source`
- `failed` appends a compact failure row with blank `Object`
- evaluation consumes a persisted `dossier_snapshot`, not loose translation or
  textification rows

## Phase 1: Data Contracts

- Add `PipelineStage.DOSSIER = "dossier"`.
- Add `LedgerTab.DOSSIERS = "dossiers"`.
- Add `DossierProcessStatus` with:
  - `ASSEMBLED = "assembled"`
  - `NO_EVIDENCE = "no_evidence"`
  - `FAILED = "failed"`
- Add dossier model types, preferably in a dedicated `curio.dossier` package:
  - `DossierEvidenceLimits`
  - `DossierComponentType`
  - `DossierTextOrigin`
  - `DossierWarningCode`
  - `DossierWarning`
  - `DossierComponent`
  - `DossierEvidenceBlock`
  - `DossierDetails`
  - `DossierSnapshot`
  - `DossierArtifact`
- Implement `to_json` / `from_json` validation for those types using the existing
  style in `curio.textify` and `curio.translate`.
- Enforce v1 invariants in constructors or validation helpers:
  - component and block ids are positive and unique
  - every evidence block references an existing component
  - every component has `evidence_language = "en"`
  - every `component_type` and `text_origin` is from the v1 enum
  - `selected_char_count` matches rendered block text for that component
  - `original_char_count >= selected_char_count`
  - `was_truncated` reflects dossier-side truncation
  - warning objects are compact and structured
  - evidence limits are present in the snapshot
- Add unit tests for all dossier model validation failures and round trips.

## Phase 2: Configuration

- Add `DossierConfig` to `curio.config`.
- Add defaults:
  - `max_components = 20`
  - `max_component_chars = 12_000`
  - `max_total_evidence_chars = 80_000`
- Parse optional `dossier` config blocks from config files.
- Validate that all dossier caps are positive integers.
- Add config tests for defaults, explicit overrides, invalid values, and
  serialization behavior if applicable.

## Phase 3: Store And Artifact Access

- Extend `PipelineStore` with a dossier candidate query that groups prepared
  inputs by root `iMsgX`.
- The dossier candidate should use the root downloads row as the candidate
  `source_ref`.
- The candidate metadata should include compact refs to all immediate prepared
  inputs considered for that root.
- Add store support for reading prior processor records needed by dossier:
  - translated translation rows
  - already-English translation rows
  - failed translation rows
  - converted textification rows that reached translation
  - already-text textification passthroughs that reached translation
  - unsupported, no-text, and failed sibling rows for warnings
- Add artifact resolution helpers for prior processor artifacts.
- Ensure refs preserve enough identity for deterministic ordering:
  - stage
  - tab
  - row number or stable row identity
  - artifact path or URL
  - artifact SHA-256 when known
  - root `iMsgX`
- Enforce append-only idempotency:
  - scheduler/store must not select a root with any existing dossier row
  - attempting to append an already-handled root is an error
  - attempting to overwrite an existing artifact with different content is an
    error
- Update `InMemoryPipelineStore` and local store implementations with tests.

## Phase 4: Dossier Assembly Core

- Implement a deterministic `DossierAssembler` or equivalent pure assembly
  helper independent of persistence.
- Convert usable upstream outcomes into selected components:
  - `translated` contributes English text from translation artifacts
  - `already_english` contributes passthrough English text
  - textified suggested files contribute after translation handling
  - deterministic repo tree or metadata text can contribute as
    `metadata_text`
- Do not emit paired source-language and `_en` evidence blocks.
- Preserve source-language lineage in component metadata and refs.
- Preserve translation warnings as dossier warnings when relevant.
- Build required common `details`:
  - `root_iMsgX`
  - `download_type`
  - `source_count`
  - `usable_component_count`
  - `evidence_block_count`
  - `truncated_component_count`
  - `component_type_counts`
  - `source_language_counts`
- Add compact optional source-specific detail objects for source, repo, and media
  facts.
- Generate `no_evidence` when zero usable evaluator-visible blocks remain.
- Add assembly unit tests for:
  - English direct text
  - non-English translated text
  - textified media with translated text
  - mixed upstream success and failure
  - unsupported-only roots
  - no-text-only roots
  - failed-only roots

## Phase 5: Limits, Ordering, And Truncation

- Implement deterministic prepared-input ordering:
  - upstream row order when available
  - stable ref tie-breakers
  - normalized relative paths for file-like components
  - artifact SHA-256 or another stable identity as final tie-breaker
- Assign `component_id` after component selection.
- Assign `block_id` after final evaluator-visible block rendering.
- Apply limits in order:
  - `max_components`
  - `max_component_chars`
  - `max_total_evidence_chars`
- When truncating a component:
  - set `was_truncated = true`
  - preserve `original_char_count`
  - set `selected_char_count`
  - add `component_truncated` warning
- When caps omit otherwise usable components:
  - add `component_omitted_due_to_limits` warning
  - do not preserve per-omitted-component metadata in v1
- Add oversized tests:
  - component-level truncation
  - total evidence truncation
  - component count omission
  - stable repeated output for identical inputs
  - repo component selection under caps

## Phase 6: Processor Integration

- Add `DossierProcessor`.
- Set:
  - `stage = PipelineStage.DOSSIER.value`
  - `ledger_tab = LedgerTab.DOSSIERS.value`
  - `version = "curio-dossier-processor.v1"`
- `next_candidate` must ask the store for the next unhandled dossier root.
- `eligibility` should usually return eligible; no-evidence is determined by
  assembly, not pre-filtering.
- `process` should:
  - resolve contributing refs and artifacts
  - call the deterministic assembler
  - return `assembled` with a `ProcessorObject` when evidence exists
  - return `no_evidence` with no object and no output source when no evidence
    exists
- `persist` should:
  - persist only assembled dossier artifacts
  - return an artifact-backed output source for downstream evaluation
  - preserve no output source for `no_evidence`
- `record` should append compact `dossiers` rows.
- Add processor tests covering assembled, no-evidence, partial warnings, failure,
  artifact persistence, and append-only behavior.

## Phase 7: Scheduler And CLI

- Add `dossier` to supported pipeline stages.
- Add `dossier` to the scheduler stage-to-ledger mapping.
- Ensure `run_processor_once`, `run_stage`, and `run_artifact_through` can run
  dossier without special casing beyond candidate grouping.
- Allow `curio pipeline run-stage dossier`.
- Update CLI help tests and pipeline scheduler tests.
- Add or update Make targets only after existing build-owner constraints allow
  changes outside this TODO.

## Phase 8: Evaluation Handoff

- Change evaluation candidate selection so evaluation reads only completed
  `dossiers` outputs.
- Ensure evaluation rejects:
  - loose textification rows
  - loose translation rows
  - `no_evidence` dossier rows
  - missing or invalid dossier artifacts
- Ensure accepted evaluation payloads embed the exact persisted
  `dossier_snapshot`.
- Add offline tests proving evaluation consumed the persisted dossier snapshot,
  not reconstructed intermediate rows.
- Add a regression test where upstream rows change after dossier assembly and
  evaluation still uses the persisted snapshot.

## Phase 9: Schemas And Read-Only Doc Alignment

These changes touch files currently treated as read-only inputs by the dossier
spec work. Implement them only when ownership constraints allow it.

- Update `schemas/evaluation_payload.schema.json`:
  - remove top-level `dossier_snapshot.kind`
  - add required `components`
  - add required `warnings`
  - add required `evidence_limits`
  - replace legacy text evidence shape with `block_id`, `component_id`, `text`
  - remove `translation_of` validation
  - add component, warning, and evidence-limit definitions
  - enforce `component_type`, `text_origin`, and `evidence_language = "en"`
- Consider adding a standalone dossier artifact schema:
  - `schemas/dossier_artifact.schema.json`
  - or `schemas/dossier_snapshot.schema.json`
- Update schema tests in `tests/test_schemas.py`.
- Align prose docs when allowed:
  - `JSON-PAYLOAD.md`
  - `TRANSLATE.md`
  - `SCHEMA.md`
  - `PIPELINE.md`
  - `CLI.md` if CLI behavior changes

## Phase 10: Acceptance Scenario Tests

- English text source produces one English block and `assembled`.
- Non-English source produces one English block from the upstream translation
  artifact and preserves source-language lineage through refs and metadata.
- Textified media contributes suggested-file evidence blocks and uses translated
  English text when upstream translation was required.
- Mixed upstream outcomes assemble partial evidence with structured warnings.
- Unsupported-only roots produce `no_evidence`.
- No-text-only roots produce `no_evidence`.
- Failed-only roots produce `no_evidence` when the failure is upstream and no
  usable evidence exists.
- Invalid upstream artifacts produce `failed`.
- Oversized repo input keeps deterministic selected components within caps.
- Truncated components preserve `original_char_count`, set `was_truncated`, and
  add warnings.
- Omitted components due to caps add compact warnings without per-omitted
  metadata.
- Dossier artifact preserves root `iMsgX`, source refs, contributing refs,
  artifact refs, local artifact metadata, details, warnings, and limits.
- Evaluation consumes a persisted dossier snapshot and embeds it unchanged in the
  accepted evaluation payload.

## Phase 11: Smoke And Operational Checks

- Add a local dossier smoke fixture set once the offline implementation is
  stable.
- Add a pipeline smoke run that exercises:
  - textify
  - translate
  - dossier
  - evaluation handoff
- Add diagnostic output for `pipeline run-stage dossier` that reports:
  - selected root `iMsgX`
  - status
  - component count
  - evidence block count
  - warning count
  - artifact path or URL when assembled
- Keep diagnostics compact; large evidence text must stay in artifacts.

## Open Decisions

- Whether dossier models should live in `curio.dossier` or under
  `curio.pipeline`.
- Whether a standalone dossier snapshot schema is required immediately or can be
  deferred until evaluation schema alignment.
- Exact local artifact filename convention for dossier artifacts.
- Exact repo component selection policy beyond the initial deterministic
  preference order in `DOSSIER.md`.
- Whether evaluation warnings should copy dossier warning messages or only link
  to the embedded dossier snapshot warnings.
