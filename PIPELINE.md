# Curio Pipeline

## Purpose

Define the normative v1 Curio pipeline.

This document specifies:

- pipeline order
- processor responsibilities
- processor/store/artifact boundaries
- intermediate tabs and skipped-row semantics
- artifact persistence rules
- dossier assembly
- evaluation input rules
- synchronous v1 scheduling

This document is not the place to define:

- detailed textify behavior
- detailed translation behavior
- detailed evaluation prompt policy
- provider-specific LLM calling behavior
- exact Google API transport mechanics

Those belong in [TEXTIFY.md](TEXTIFY.md), [TRANSLATE.md](TRANSLATE.md),
[JSON-PAYLOAD.md](JSON-PAYLOAD.md), [LLM-CALLER.md](LLM-CALLER.md),
[SCHEMA.md](SCHEMA.md), and prompt files.

## Pipeline Order

Curio v1 begins from the upstream `iMsgX` `downloads` ledger.

`download` is not a Curio pipeline processor. `iMsgX` already owns artifact
download and the append-only `downloads` tab. Curio reads that tab, resolves the
local artifact metadata it needs, and writes Curio-owned state to Curio-owned
tabs.

The v1 Curio pipeline is:

```text
downloads row
  -> textify
  -> translate
  -> dossier
  -> evaluate
```

The stage and CLI slug is `dossier`. The persisted object remains a
`dossier_snapshot` because it is an immutable snapshot of model-visible
evidence.

`persist` is not a standalone pipeline stage. Every processor owns its own
artifact persistence and row recording.

The older shorthand:

```text
download row -> artifact dossier extraction -> textify -> translate -> evaluate -> persist
```

is retired for v1 pipeline planning. Some deterministic extraction still happens
inside source adapters and processors, but the persisted `dossier_snapshot` is
assembled after textify and translation outputs exist.

## Design Principles

- Curio is append-only in v1.
- `downloads` remains the upstream source of truth for ingestion provenance.
- Curio-owned state lives in Curio-owned tabs, not in `downloads`.
- Every processor has a compact row ledger.
- Full text, model payloads, and large details live in artifacts, not Sheets
  cells.
- Skipped work is real work when the input is newly handled and ineligible.
- Duplicate reruns are no-ops, not new skipped rows.
- Model quality failures are retained and scored downstream; they should not
  usually make smoke or pipeline plumbing fail.
- Evaluation consumes a dossier produced by the dossier stage, not loose
  intermediate rows.
- V1 is synchronous and single-process.
- V2 may add leases, concurrency, and stronger storage backends without
  changing processor contracts radically.

## Processor Contract

A processor is one pipeline stage with one owned output tab.

The initial implementation is intentionally limited to the two built processors:

- `textify`
- `translate`

`dossier` and `evaluate` remain normative v1 stages, but their processor
classes, statuses, scheduler integration, and adapters are deferred until those
capabilities exist behind service boundaries.

The target Python processor contract should be an abstract base class close to:

```python
class Processor(ABC):
    stage: str
    ledger_tab: str
    version: str

    def next_candidate(self, store: PipelineStore) -> ProcessCandidate | None: ...
    def eligibility(self, candidate: ProcessCandidate) -> Eligibility: ...
    def process(self, candidate: ProcessCandidate) -> ProcessOutcome: ...
    def persist(
        self,
        candidate: ProcessCandidate,
        outcome: ProcessOutcome,
        artifacts: ArtifactStore,
    ) -> PersistedOutcome: ...
    def record(
        self,
        candidate: ProcessCandidate,
        outcome: PersistedOutcome,
        store: PipelineStore,
    ) -> ProcessRecord: ...
```

An abstract base class is preferred over a processor `Protocol` because
processors will likely share lifecycle checks and scheduler helpers as the
pipeline grows. Store boundaries should remain protocols because local,
in-memory, Google Sheets, and Google Drive adapters should stay duck-typed and
easy to fake in tests.

Method names are intentional:

- `next_candidate()` selects the next work item. It is not named `next()` because
  it is not Python iterator protocol.
- `eligibility()` returns an `Eligibility` value. It is not named
  `is_eligible()` because the result carries status and metadata, not just a
  boolean.

`process()` should do the expensive or semantic work. For LLM-backed stages, it
should call an existing service boundary such as `TextifyService` or
`TranslationService`.

`persist()` should write full artifacts before a compact ledger row is appended.
It should create a Drive object only when `outcome.object_` is present.

`record()` should append exactly one compact row for a newly handled candidate.
The visible row `Object` cell comes from `PersistedOutcome.object_`; it is blank
when `object_ is None`.

`stage` is the workflow and CLI identity, such as `textify`, `translate`,
`dossier`, or `evaluate`. `ledger_tab` is the processor-owned sheet tab and
Drive folder identity, such as `textifications`, `translations`, `dossiers`, or
`evaluations`. `version` identifies behavior that affects idempotency.

## Store Boundaries

Processors must not assume Google Sheets or Google Drive directly.

The implementation should introduce at least two storage boundaries:

- `PipelineStore`
  - reads upstream candidates
  - resolves row refs
  - finds existing processor records for idempotency
  - appends processor rows
- `ArtifactStore`
  - persists processor output JSON
  - persists generated text artifacts when useful
  - returns stable artifact refs, URLs, paths, hashes, sizes, and MIME types

Google Sheets and Google Drive are v1 adapter implementations, not the processor
contract itself. Tests should use in-memory stores and temp-dir artifact stores
before any Google adapter exists.

## Core Data Concepts

### Lineage Invariant

Every pipeline object must preserve two refs:

- `source_ref`
  The immediate row or artifact that created this object.
- `iMsgX`
  The root upstream `iMsgX` `downloads` row from which this object is derived.

These refs are intentionally separate. A translated object should point to the
textification row or prepared text ref that it translated, and it should also
point to the original `downloads` row for the X post, iMessage artifact, or
other upstream source. A dossier object should point to the translation row it
assembled from and to the same original `downloads` row. An evaluation should
point to the dossier row it evaluated and to the same original `downloads` row.

`Source` is not enough by itself. It is a useful human-facing stable artifact
identity, but operators also need exact Google row refs for audit, repair,
replay, and debugging.

The invariant applies to:

- `ProcessCandidate`
- `ProcessOutcome`
- `PersistedOutcome`
- `ProcessRecord`
- persisted processor JSON objects

Python dataclasses should use the field name `imsgx` and serialize it as the
JSON/object key `iMsgX`. This keeps Python naming conventional while preserving
the visible sheet and spec vocabulary.

Visible row `Source` and outcome `output_source` are different concepts:

- Visible row `Source` is the immediate row or ref that this processor consumed.
- Outcome `output_source` is the source ref emitted for downstream processors.

When a processor handles a source without creating an object, `output_source` must
preserve the same `iMsgX` ref and expose the correct downstream source. Usually
that downstream ref is the newly appended skipped processor row; a stage may
explicitly choose the original upstream row only when that is the real source
emitted for downstream processors.

### `ProcessRef`

A stable reference to a pipeline row or upstream row.

Recommended fields:

- `stage`
- `tab`
- `row_number`
- `source`
- `row_url`
- `spreadsheet_id`
- `sheet_id`
- `artifact_url`
- `artifact_path`
- `artifact_sha256`

`row_number` is useful for operator diagnostics. It should not be the only
identity.

For Google Sheets-backed stores, `row_url` should link to the exact tab row when
available. `spreadsheet_id`, `sheet_id`, and `row_number` should be retained so
the ref can still be inspected or reconstructed if a URL format changes.

### `ArtifactRef`

A stable reference to a persisted artifact.

Recommended fields:

- `url`
- `path`
- `sha256`
- `size_bytes`
- `mime_type`
- `kind`
- `source_ref`
- `iMsgX`

Exactly one of `url` or `path` may be enough in some stores, but the model
should support both because local-first and Drive-backed runs both matter.
Persisted artifact contents should carry the same lineage refs; `ArtifactRef`
may mirror them so callers do not need to fetch a large artifact only to answer
"what row created this?"

### `ProcessCandidate`

The typed input to a processor.

Recommended fields:

- `source_ref`
- `imsgx` serialized as `iMsgX`
- `source`
- `artifact_key`
- `metadata`

The `metadata` object should stay compact and typed at the processor boundary.
Large text belongs in artifacts resolved by refs.

### `ProcessorObject`

The object a processor wants persisted.

Target shape:

```python
@dataclass(frozen=True, slots=True)
class ProcessorObject:
    payload: Mapping[str, Any]
    mime_type: str = "application/json"
```

`payload` is the JSON-ready object that will be saved by the artifact store.
Processor/model/cost details, warnings, and contributing row refs belong inside
this payload or `metadata`, not in visible preparation-tab columns.

### `ProcessOutcome`

The result produced by `process()` before persistence.

Target shape:

```python
@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    status: str
    object_: ProcessorObject | None
    output_source: ProcessRef | None
    metadata: Mapping[str, Any]
```

`status` is the Python form of visible sheet `Status`. `object_` is the Python
field for visible sheet `Object`; when it is `None`, the visible `Object` cell
will be blank. `output_source` is the source ref emitted for downstream
processors. `metadata` is JSON/debug detail and is never rendered as a visible
sheet column.

### `PersistedOutcome`

The result after `persist()` has written any created object.

Target shape:

```python
@dataclass(frozen=True, slots=True)
class PersistedOutcome:
    status: str
    object_: ArtifactRef | None
    output_source: ProcessRef | None
    metadata: Mapping[str, Any]
```

`PersistedOutcome.object_` is the artifact ref used to render the visible row
`Object` link. It stays `None` for skipped and failed rows that did not create a
JSON object.

### `Eligibility`

The result of checking whether a processor should run for a candidate.

Recommended fields:

- `eligible`
- `status`
- `metadata`

When `eligible` is false and this is newly handled work, the processor should
record a row with the appropriate specific status, no created object, and a
`output_source` when downstream processors should still consume some prepared
source.

### `ProcessRecord`

The compact row appended by a processor.

Recommended fields:

- common row fields listed below
- visible `Source` ref for what this processor consumed
- root `iMsgX` ref
- visible `Status`
- visible `Object` artifact ref when an object was created

## Identity And Idempotency

V1 idempotency should use a processor input key composed from:

- `Source`
- root `iMsgX`
- upstream downloads row metadata
- immediate source `ProcessRef`
- local artifact hash when available
- processor `stage`
- processor `ledger_tab`
- processor `version`

If a terminal record already exists for the same processor input key, rerun
should no-op by default. It should not append another handled row.

Failed records are append-only attempts. A later retry may append a new terminal
or failed record for the same input key if the operator asks for retry behavior
or if the scheduler policy treats failed rows as retryable.

No global `runs` table is required in v1. Per-row timestamps, processor stages,
processor versions, caller names, and artifact refs are enough.

## Lean Sheet Rows

Preparation processor tabs are operator ledgers, not debug databases. They
should contain only identity, immediate lineage, stage outcome, and the created
Google Drive object link.

Visible row detail belongs in [SCHEMA.md](SCHEMA.md). The intended v1 shape is:

- `textifications`: `Date`, `X Date`, `iMsgX`, `Type`, `Source`, `Status`, `Object`
- `translations`: `Date`, `X Date`, `iMsgX`, `Type`, `Source`, `Status`, `Object`
- `dossiers`: `Date`, `X Date`, `iMsgX`, `Status`, `Object`

Use one specific `Status` column. Do not add visible `Reason`, `Warnings`,
processor, model, cost, row-number, or version columns to these preparation
tabs.

`Object` links to the Google Drive object created by that processor in its own
folder. It is blank when the processor did not create an object.

Detailed lineage, contributing rows, processor/model/cost metadata, warnings,
hashes, and full text belong in the created JSON object.

Timestamps in Sheets should use the existing visible UTC format:

```text
YYYY-MM-DD HH:MM:SS UTC
```

Full artifact JSON should use RFC 3339 timestamps.

## Processor-Owned Tabs

V1 uses these Curio-owned processor tabs:

- `textifications`
- `translations`
- `dossiers`
- `evaluations`

The existing `labels` and derived `catalog` tabs remain, but they are not
processor-owned pipeline ledgers.

### `textifications`

Owned by `TextifyProcessor`.

Input:

- `downloads`

Completed output:

- source-language text artifacts from non-text media
- textify response artifact

Skipped output:

- `output_source` to deterministic text evidence from the downloads row or local
  artifact

Visible columns:

- `Date`
- `X Date`
- `iMsgX`
- `Type`
- `Source`
- `Status`
- `Object`

Visible status values:

- `converted`
- `already_text`
- `unsupported`
- `no_text`
- `failed`

### `translations`

Owned by `TranslateProcessor`.

Input:

- best text output from `textifications`, or an `output_source` deterministic text ref

Completed output:

- English translated text artifacts when translation was required
- translation response artifact

Skipped output:

- `output_source` to original text when it was confidently English

Visible columns:

- `Date`
- `X Date`
- `iMsgX`
- `Type`
- `Source`
- `Status`
- `Object`

Visible status values:

- `translated`
- `already_english`
- `failed`

### `dossiers`

Owned by `DossierProcessor`.

This processor should be deterministic in v1.

Input:

- all prepared source objects sharing the same upstream `iMsgX`

Completed output:

- one persisted dossier snapshot artifact
- compact row pointing to that artifact

Skipped output:

- no `output_source` to evaluation unless a later policy explicitly allows
  evaluation without model-visible evidence

Visible columns:

- `Date`
- `X Date`
- `iMsgX`
- `Status`
- `Object`

Visible status values:

- `assembled`
- `no_evidence`
- `failed`

### `evaluations`

Owned by `EvaluateProcessor`.

Input:

- a completed `dossiers` row

Completed output:

- persisted evaluation payload JSON
- compact accepted evaluation summary

Skipped output:

- compact skipped row when a newly handled dossier cannot or should not be
  evaluated

Common stage reasons:

- `accepted`
- `no_english_evidence`
- `policy_skip`
- `invalid_model_output`
- `provider_error`

Stage-specific compact fields should preserve the existing evaluation summary
surface where possible:

- `Title`
- `Creator`
- `Source Language`
- `Summary EN`
- `Importance`
- `Labels`
- `Proposals`
- `JSON URL`

`catalog` should derive only from completed accepted evaluation rows. Skipped and
failed evaluation rows are operational ledger entries, not catalog entries.

## Output Source Refs

Processors that handle a source without creating an object still expose the
correct downstream input through `output_source`.

Rules:

- `already_text` textification sets `output_source` to the original text
  evidence
- `already_english` translation sets `output_source` to the original
  English text
- `translated` translation sets `output_source` to translated English text
- dossier assembly consumes the best available text refs and produces a new
  dossier snapshot
- evaluation consumes the dossier snapshot only

This keeps downstream processors from special-casing every upstream skip reason.

## Dossier Snapshot Assembly

`DossierProcessor` is the audit boundary between preparation and evaluation.

It must assemble exactly the evidence the evaluator will see.

The snapshot should include:

- `source_ref` to the translation row or prepared text ref it consumed
- `iMsgX` to the original upstream `downloads` row
- upstream downloads row metadata
- local artifact metadata
- source-language text blocks
- paired English blocks when translation occurred
- deterministic details needed for audit
- truncation metadata when evidence was shortened
- compact warnings from preparation

It must not include:

- raw file bytes
- unrestricted duplicate text dumps
- model rationales
- evaluation judgment

The snapshot artifact should be persisted before evaluation. Evaluation payloads
may embed the exact snapshot object, link back to the `dossiers` row or
artifact, or both. V1 should prefer both: embed enough for audit portability and
record the row/artifact ref for operational traceability.

## Evaluation Input

Evaluation should consume an English-centered dossier snapshot.

The persisted dossier may retain both original source-language evidence and
English paired blocks. The evaluator prompt should use the English blocks when
available, while retaining source references and warnings for context.

Evaluation must not re-run textify, translation, or dossier assembly implicitly.
If upstream preparation changes, Curio should create new upstream processor rows
and a new dossier snapshot before evaluation is retried.

## Artifact Persistence

Each in-scope preparation processor owns an artifact folder with the same name
as its processor tab. The initial implementation uses a local filesystem
`ArtifactStore`; Google Drive remains an adapter behind the same boundary for a
later pass. Curio must not hard-code a machine-specific artifact location.
Runtime config must provide the upstream iMsgX downloads directory:

```json
{
  "pipeline": {
    "downloads_dir": "~/Desktop/iMsgX/downloads",
    "artifact_root": null
  }
}
```

`downloads_dir` is required. `artifact_root` is optional. When `artifact_root`
is omitted or null, the effective artifact root is `downloads_dir.parent`, so
Curio writes sibling directories beside iMsgX `downloads`. `~` expands through
the host environment, and relative paths resolve relative to the config file
directory.

```text
textifications/
translations/
```

Each object-creating preparation row creates one JSON object in the relevant
folder:

- textify response JSON
- translation response JSON

Persist the JSON object before appending the processor row. The row's `Object`
cell links to that object, either by local path or Drive URL depending on the
artifact store. Skipped and failed preparation rows do not create or link
artifact objects.

Every persisted artifact should include a small lineage envelope
with `source_ref`, `iMsgX`, `source`, processor `stage`, `ledger_tab`, and
processor `version`. Large artifacts should not force operators to reconstruct
lineage only from filenames or surrounding Sheets rows.

If artifact persistence succeeds but row append fails, rerun should be able to
recover by detecting the deterministic artifact name or hash and appending the
missing compact row.

Sheets rows should store compact refs and summaries only.

## Scheduler

V1 scheduler behavior is synchronous:

- one process
- one processor at a time
- no leases
- no concurrent claims
- no background workers
- no parallel LLM calls

Default scheduling mode is artifact-through:

```text
choose next downloads row that does not have a completed or skipped terminal evaluation
run textify for that source
run translate for the selected text output
run dossier assembly
run evaluate
repeat until limit or no work
```

The initial implemented scheduler is limited to:

```text
downloads candidate
  -> textify
  -> translate
```

It rejects unsupported stages such as `dossier` and `evaluate` until those
processors are intentionally added.

Single-stage commands should also exist for repair and backfill:

```text
curio pipeline run-stage textify --limit 10
curio pipeline run-stage translate --limit 10
curio pipeline run-stage dossier --limit 10  # later
curio pipeline run-stage evaluate --limit 10  # later
```

## CLI Shape

Reserve a `pipeline` command group.

Likely commands:

```text
curio pipeline run
curio pipeline run-stage STAGE
curio pipeline run-source SOURCE
curio pipeline doctor SOURCE
```

Likely shared flags:

- `--config PATH`
- `--limit N`
- `--dry-run`
- `--json`
- `--source SOURCE`
- `--from-row N`
- `--llm-caller NAME`

`--llm-caller` should apply only to LLM-backed processors in the selected run.

The existing reserved `curate` command may later become an alias or user-facing
wrapper for `pipeline run`, but the lower-level `pipeline` group should exist
for repair, backfill, and debugging.

## Error And Retry Policy

Errors should be classified before recording:

- configuration errors
- missing input artifacts
- provider auth errors
- provider timeout/errors
- invalid provider output
- artifact persistence errors
- ledger append errors

If a processor cannot even identify or append a failed row because the ledger is
unavailable, the command should fail loudly and leave local diagnostics.

If a row append succeeds with `failed`, later retry behavior should be explicit:

- retry all retryable failures
- retry one source
- retry one stage
- retry after processor version change

V1 does not need exponential backoff queues or leases.

## V2 Design Space

V2 may add:

- bounded worker pools
- per-stage concurrency
- per-provider LLM rate limits
- claim rows or leases
- stale lease recovery
- retry queues
- backpressure when downstream stages fail
- alternative ledgers beyond Google Sheets

Those features are out of scope for v1.

## Testing Requirements

Pipeline implementation must be test-first and offline by default.

Required tests:

- pure model and serialization tests
- idempotency tests
- skipped-row tests
- `output_source` tests
- failed-row tests
- artifact persistence/recovery tests
- in-memory artifact-through scheduler tests
- single-stage scheduler tests
- CLI dry-run tests
- fake Google adapter tests before any live Google calls

Default `make check` must not require:

- network
- Google auth
- Codex auth
- live LLM calls
- real Google Sheets or Drive

Live pipeline smoke tests, if added later, must be opt-in.
