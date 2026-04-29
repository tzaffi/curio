# Curio Dossier

## Purpose

Define the normative v1 behavior for the Curio `dossier` pipeline stage.

This document is authoritative for:

- dossier assembly semantics
- dossier ledger rows
- dossier snapshot contents
- evaluator handoff rules
- evidence selection, limits, and truncation metadata

This document is not the place to define:

- detailed textification behavior
- detailed translation behavior
- evaluation prompt policy
- provider-specific LLM calling behavior
- Google Sheets or Google Drive transport mechanics
- implementation task tracking

Those belong in `TEXTIFY.md`, `TRANSLATE.md`, `JSON-PAYLOAD.md`,
`PIPELINE.md`, `SCHEMA.md`, `LLM-CALLER.md`, `CLI.md`, prompt files, and
implementation plans.

## Pipeline Position

The v1 Curio pipeline order is:

```text
downloads row
  -> textify
  -> translate
  -> dossier
  -> evaluate
```

The stage and CLI slug is `dossier`. The persisted model-visible object remains
a `dossier_snapshot` because it is an immutable snapshot of the exact normalized
evidence assembled for evaluation.

`DossierProcessor` is deterministic in v1. It must not call an LLM, summarize,
classify, label, rank, or evaluate content. Any LLM-generated dossier summary is
reserved for a later explicit processor version or separate processor.

## Processor Role

`DossierProcessor` is the audit boundary between preparation and evaluation.

It must:

- group prepared source objects that share the same root `iMsgX` downloads row
- assemble the exact evidence the evaluator will see
- preserve English-centered prepared evidence and translation lineage when
  translation occurred upstream
- persist one dossier snapshot artifact before evaluation runs
- append one compact row to `dossiers` for newly handled work
- emit no evaluation input when no usable evidence exists

It must not:

- read raw file bytes into the snapshot
- duplicate unrestricted full text dumps
- include model rationales
- include evaluation judgments
- mutate `downloads`, `textifications`, `translations`, or `evaluations`

## Inputs

The dossier input is all prepared source objects sharing the same root `iMsgX`
downloads row.

Usable prepared evidence can come from:

- a `translated` translation row and its persisted translation artifact
- an `already_english` translation row and its passthrough source ref
- an `already_text` textification passthrough that later reached translation
- a `converted` textification artifact that later reached translation

Unusable or non-evidence upstream outcomes include:

- `unsupported`
- `no_text`
- `failed`

Those outcomes do not create model-visible evidence blocks by themselves.

Because a dossier may package multiple prepared source objects, the visible
`dossiers` ledger has no `Source` column. The persisted artifact must carry
contributing row refs and artifact refs for every source object considered.

The root `iMsgX` ref must always identify the upstream `downloads` row. When a
single pipeline `source_ref` is required by the processor contract, the dossier
candidate should use the root `iMsgX` downloads ref as its candidate source and
store all immediate prepared inputs in artifact metadata as contributing refs.

## Ledger Contract

The `dossiers` tab is the append-only ledger owned by `DossierProcessor`.

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

`Date`, `X Date`, and `iMsgX` are copied through from the upstream downloads row.

`Object` links to the persisted dossier snapshot JSON only when
`Status = assembled`. It is blank for `no_evidence` and `failed`.

The row must stay compact. Contributing refs, warnings, limits, truncation
details, processor version, hashes, and source-specific metadata belong in the
persisted artifact, not visible ledger columns.

## Status Semantics

`assembled` means at least one usable model-visible evidence block exists for
the root `iMsgX` row and a dossier snapshot artifact was persisted.

`no_evidence` means dossier assembly newly handled the root `iMsgX` row but
found zero usable model-visible evidence blocks. A `no_evidence` row does not
emit an `output_source` to evaluation.

`no_evidence` exists to distinguish "not processed yet" from "processed and
there is intentionally nothing to evaluate." It is a scheduling and audit status,
not a dossier artifact. It prevents repeated attempts for unsupported-only,
no-text-only, or failed-only roots while keeping the visible ledger compact.

`failed` means dossier assembly could not complete because of an unexpected
processor error, invalid upstream artifact, invalid lineage, persistence error,
or another condition that prevented a reliable determination. Failed rows remain
compact and must not contain large payloads or stack traces in Sheets.

Partial upstream failure is not a dossier failure when at least one usable
evidence block exists. In that case the dossier must use `assembled` and record
compact warnings about failed, unsupported, no-text, or skipped sibling sources
inside `dossier_snapshot.warnings`.

## Snapshot Object

The dossier processor persists a dossier artifact envelope whose central payload
is a `dossier_snapshot` object.

Existing `JSON-PAYLOAD.md`, `TRANSLATE.md`, and
`schemas/evaluation_payload.schema.json` still describe the pre-dossier v1
evaluation payload shape. This document is the normative dossier-stage
refinement for the next v1 pipeline behavior:

- top-level `dossier_snapshot.kind` is removed
- `dossier_snapshot.components[]` is added
- `dossier_snapshot.warnings[]` is added
- `dossier_snapshot.evidence_limits` is added
- `evidence_text[]` entries include `component_id`
- `evidence_text[]` entries do not include `name`, `language`,
  `translation_of`, `was_truncated`, or `original_char_count`

Upstream `translate` artifacts own translation detection and translation
lineage. Dossier snapshots preserve that lineage through component metadata and
refs, not paired source-language/English evidence blocks.

Required dossier snapshot fields:

- `assembled_at`
- `title_hint`
- `source_language_hint`
- `components`
- `evidence_text`
- `details`
- `warnings`
- `evidence_limits`

Target persisted dossier artifact envelope:

```json
{
  "artifact_version": "curio-dossier-artifact.v1",
  "stage": "dossier",
  "ledger": {
    "tab": "dossiers",
    "status": "assembled"
  },
  "processor_version": "curio-dossier.v1",
  "created_at": "2026-04-20T06:15:42.381Z",
  "root_ref": { "...": "ProcessRef" },
  "candidate_source_ref": { "...": "ProcessRef" },
  "download_row": {
    "Date": "2026-04-20 06:15:42 UTC",
    "X Date": "",
    "iMsgX": "https://docs.google.com/spreadsheets/...",
    "Source": "https://example.invalid/source",
    "Column": "X1",
    "Type": "Repo",
    "Object": "https://drive.google.com/..."
  },
  "local_artifact": {
    "path": "/absolute/path/to/artifact.zip",
    "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "size_bytes": 12345,
    "mime_type": "application/zip"
  },
  "contributing_refs": [
    { "...": "ProcessRef" }
  ],
  "contributing_artifact_refs": [
    { "...": "ArtifactRef" }
  ],
  "dossier_snapshot": {
    "...": "DossierSnapshot"
  }
}
```

The persisted processor artifact envelope must preserve:

- processor stage, ledger tab, and processor version
- root `iMsgX` downloads row ref
- candidate source ref
- upstream downloads row metadata
- local artifact metadata when available
- contributing prepared row refs
- contributing artifact refs

Warnings and evidence limits belong inside `dossier_snapshot`, not only in the
outer envelope, because the evaluation payload embeds the snapshot for audit
portability. Implementations may copy warning or limit summaries into artifact
metadata for indexing, but `dossier_snapshot` is the source of truth.

When the evaluator later persists an accepted evaluation payload, the exact
dossier snapshot object must be embedded under `dossier_snapshot`. Evaluation
may also link back to the `dossiers` row or dossier artifact for operational
traceability.

## JSON Shapes

The shapes below define the dossier-stage schema target. The existing
machine-readable evaluation schema must be aligned before evaluation can consume
persisted dossier snapshots.

`DossierSnapshot`:

```json
{
  "assembled_at": "2026-04-20T06:15:42.381Z",
  "title_hint": "Best deterministic title or null",
  "source_language_hint": "Best source-language hint or null",
  "components": [
    { "...": "DossierComponent" }
  ],
  "evidence_text": [
    { "...": "EvidenceBlock" }
  ],
  "details": {
    "...": "DossierDetails"
  },
  "warnings": [
    { "...": "DossierWarning" }
  ],
  "evidence_limits": {
    "max_components": 20,
    "max_component_chars": 12000,
    "max_total_evidence_chars": 80000
  }
}
```

`DossierComponent`:

```json
{
  "component_id": 1,
  "name": "repo_readme",
  "component_type": "repo_readme",
  "evidence_language": "en",
  "source_language": "ja",
  "source_ref": { "...": "ProcessRef" },
  "artifact_ref": { "...": "ArtifactRef or null" },
  "text_origin": "translated",
  "selected_char_count": 8120,
  "original_char_count": 10421,
  "was_truncated": false,
  "metadata": {
    "path": "README.md"
  }
}
```

`EvidenceBlock`:

```json
{
  "block_id": 1,
  "component_id": 1,
  "text": "Exact evaluator-visible English evidence text."
}
```

`DossierWarning`:

```json
{
  "code": "component_truncated",
  "message": "Component repo_readme was truncated to fit dossier limits.",
  "component_id": 1,
  "source_ref": { "...": "ProcessRef or null" }
}
```

`DossierDetails`:

```json
{
  "root_iMsgX": "https://docs.google.com/spreadsheets/...",
  "download_type": "Repo",
  "source_count": 3,
  "usable_component_count": 2,
  "evidence_block_count": 2,
  "truncated_component_count": 1,
  "component_type_counts": {
    "repo_readme": 1,
    "repo_manifest": 1
  },
  "source_language_counts": {
    "en": 1,
    "ja": 1
  },
  "source": {
    "...": "compact source-specific facts"
  },
  "repo": {
    "...": "compact repo-specific facts when applicable"
  },
  "media": {
    "...": "compact media-specific facts when applicable"
  }
}
```

`ProcessRef` and `ArtifactRef` follow the common processor-boundary shapes in
`PIPELINE.md`. A dossier component ref must be JSON-serializable and compact. A
ref should include stable identity fields when known, such as `stage`, `tab`,
`row_number`, `row_url`, `spreadsheet_id`, `sheet_id`, `artifact_url`,
`artifact_path`, `artifact_sha256`, and root `iMsgX`. Ref fields that are not
known may be omitted or set to `null`; refs must not contain large payload text.

## Read-Only Schema Alignment

`JSON-PAYLOAD.md`, `TRANSLATE.md`, and
`schemas/evaluation_payload.schema.json` are read-only inputs for this dossier
spec, but they must eventually be aligned with this target shape.

Required schema changes:

- remove `dossierSnapshot.properties.kind`
- remove `kind` from `dossierSnapshot.required`
- add `components`, `warnings`, and `evidence_limits` to
  `dossierSnapshot.required`
- replace the old `textEvidence` definition with `EvidenceBlock`, requiring only
  `block_id`, `component_id`, and `text`
- remove `translation_of` validation and its English-language conditional from
  dossier evidence blocks
- add `DossierComponent`, `DossierWarning`, and `EvidenceLimits` definitions
- require `component_type` and `text_origin` enum validation on components
- require `evidence_language = "en"` for every component in v1
- keep evaluation payload embedding the exact `dossier_snapshot` object produced
  by the dossier stage

Required prose-doc alignment:

- `JSON-PAYLOAD.md` should describe the component-backed dossier snapshot shape
  instead of the legacy paired-block shape
- `TRANSLATE.md` should state that translation artifacts preserve source and
  translated text, while dossier v1 consumes only the prepared English-centered
  evaluation text
- `SCHEMA.md` and `PIPELINE.md` should treat `dossiers.Object` as the assembled
  snapshot artifact link and should not require large warning or limit fields in
  visible Sheets columns

## Components

`components` is the ordered catalog of selected source units that dossier
assembly considered usable enough to expose to evaluation.

Each component must contain:

- `component_id`
- `name`
- `evidence_language`
- `source_language`
- `component_type`
- `source_ref`
- `artifact_ref`
- `text_origin`
- `selected_char_count`
- `original_char_count`
- `was_truncated`
- `metadata`

`component_id` values must be positive integers unique within the snapshot.
Every `evidence_text[].component_id` must point to one component in this array.

`name` is the stable component name used by corresponding evidence blocks, such
as `tweet_text`, `page_main_text`, `repo_readme`, `scan_md`, or
`scripts_install_sh`.

`evidence_language` records the evaluation language of the text selected for
this component. V1 dossiers are English-centered, so this must be exactly `en`
for every assembled component. If a later policy allows non-English evaluation
evidence, that policy must update this field's allowed values and evaluation
rules.

`source_language` records the best available language code for the original
source text before translation. It is nullable when Curio has no reliable hint
or detection result. For translated content, `source_language` is the detected
or hinted source language, such as `ja` or `fr`, while `evidence_language` is
`en`. For already-English content, `source_language` may be `en`, an English
variant such as `en-US`, or `null` when upstream translation did not provide a
reliable code.

`component_type` is a compact component category. V1 values are:

- `source_text`
- `html_main_text`
- `textified_file`
- `repo_readme`
- `repo_manifest`
- `repo_tree`
- `repo_file`
- `metadata_text`

`source_text` covers direct text evidence from the root source, such as tweet
text, X article text, or plain downloaded text. `metadata_text` is reserved for
small deterministic text generated from source metadata, such as a file tree
listing; it must not contain LLM-generated summaries.

`source_ref` points to the immediate prepared row or ref that produced the
component. For translated text, this is the contributing translation row or
artifact ref, not the original downloads row.

`artifact_ref` points to the persisted artifact that contains the component
source when one exists. It is `null` only for passthrough text refs that have no
separate artifact.

`text_origin` records where the evaluator-visible text came from:

- `already_english`
- `translated`
- `textified_then_already_english`
- `textified_then_translated`
- `deterministic_extraction`

`already_english` means upstream translation classified the selected text as
English and no translation artifact supplied replacement text. `translated`
means the evaluator-visible text came from an upstream translation artifact.
The `textified_*` values apply when the text first came from a textification
artifact. `deterministic_extraction` is for evidence Curio derived without an
LLM, such as a bounded repo tree component.

`selected_char_count` is the character count included in `evidence_text` for
this component after dossier limits.

`original_char_count` is the character count before dossier truncation.

`was_truncated` is true when any evidence block for this component was shortened
by dossier limits.

`metadata` is compact deterministic metadata needed to understand this
component, such as suggested text path, repo file path, MIME type, detected
language, or translation response block id. It must not contain large duplicate
text.

## Evidence Text

`evidence_text` is the ordered list of text blocks shown to the evaluator.

Each block must contain:

- `block_id`
- `component_id`
- `text`

`block_id` values must be positive integers unique within the snapshot.

`component_id` must point to a component in `components`. All blocks produced
from the same source component share the same `component_id`.

`text` is the exact text shown to the evaluator after any configured dossier
truncation.

Evidence blocks intentionally do not repeat component metadata such as `name`,
`evidence_language`, `source_language`, `was_truncated`, or
`original_char_count`. That audit metadata lives in `components[]`. The block
exists to preserve evaluator-visible order and exact text.

## Deterministic Ordering

Ordering is part of dossier behavior because component caps and total character
caps can change which evidence reaches evaluation.

V1 ordering must be deterministic and stable for the same prepared inputs:

- prepared source objects are ordered by upstream row order when available
- ties are broken by stable refs, such as `stage`, `tab`, `row_number`,
  artifact path, artifact SHA-256, or another deterministic identity field
- file-like components inside one artifact are ordered by normalized relative
  path unless the source artifact has a stronger deterministic order
- `component_id` values are assigned after component selection in final component
  order
- `block_id` values are assigned after block rendering in final evaluator-visible
  order
- component and total evidence limits keep the earliest components and text under
  that deterministic order

The spec does not assign semantic meaning to earlier or later components beyond
reproducibility and cap behavior.

## Translation Lineage

Translation happens before dossier assembly.

For every source text block that reached the `translate` stage, dossier
assembly consumes the prepared English-centered output:

- `translated` rows contribute the translated English text from the translation
  artifact
- `already_english` rows contribute the original text exposed by the translation
  passthrough ref
- failed translation rows do not contribute model-visible evidence

`evidence_text` should not contain adjacent source-language and `_en` paired
blocks in v1. The evaluator-visible block is the prepared text that evaluation
should read. For translated content, the component uses
`evidence_language = en` and preserves the original language in
`source_language`.

Original source-language text, detected language, confidence estimates,
translation request/response metadata, token usage, cost, and provider warnings
remain auditable through contributing translation refs and artifact metadata.
The dossier may copy compact language hints or warnings into `details` or
artifact metadata, but it must not duplicate unrestricted source-language text
only to model translation lineage inside `evidence_text`.

## Textification Representation

When textification converted non-text media, each suggested text file contributes
one or more prepared evidence blocks after translation handling.

The component name should derive from the safe suggested path:

- `scan.md` -> `scan_md`
- `scripts/install.sh` -> `scripts_install_sh`

The original media metadata remains in local artifact metadata and
`details`. Raw media bytes must not appear in the dossier snapshot.

When textification skipped text media as already text, dossier assembly must
consume the passthrough text ref. It must not create duplicate evidence blocks
from both the skipped textification row and the original source.

## Evidence Limits

V1 dossier evidence limits are configurable. Defaults:

- `max_components = 20`
- `max_component_chars = 12_000`
- `max_total_evidence_chars = 80_000`

A component is the source unit selected by dossier assembly before it is
rendered as one or more evaluator-visible blocks. Components are represented in
the snapshot by `components[]`; each `evidence_text` block links back through
`component_id`.

Examples of components:

- one tweet body
- one X article body
- one HTML page main-text extraction
- one textified suggested file
- one repo README
- one repo manifest
- one deterministic repo tree summary
- one selected small source/config file from a repo

Most components produce one `evidence_text` block. If a component is
deterministically split into multiple evaluator-visible blocks, all blocks from
that component share the same `component_id`.

`max_components` limits how many distinct `component_id` values can appear in
one dossier.

`max_component_chars` limits the text shown for one component after translation
has already processed the full normalized source text for that component. If a
component renders as multiple `evidence_text` blocks, their combined text must
fit within this component cap.

`max_total_evidence_chars` limits the total text shown across all
`evidence_text` blocks in the snapshot.

When a component is shortened:

- set `was_truncated = true`
- preserve `original_char_count`
- add a compact warning naming the component
- keep truncation deterministic

When component count or total evidence limits exclude otherwise usable
components, the dossier must add a compact warning with the number of omitted
components. V1 does not require preserving per-omitted-component metadata.

Configured limits must be stored in `dossier_snapshot.evidence_limits` so later
evaluation audits can reconstruct the evidence policy used.

## Oversized Artifacts And Repos

Oversized artifacts, especially repository zips, must use deterministic
selection and truncation in v1.

For a repo zip, dossier assembly should prefer deterministic components such as:

- README or equivalent primary documentation
- package or dependency manifests
- top-level file tree or selected directory tree summaries
- small entrypoint or configuration files when deterministically selected

The snapshot should keep structured repo facts in `details`, such as repo URL,
owner, repo name, top-level entries, manifest files, README presence, and counts
for truncated components. Omitted components due to caps only require compact
warnings in v1.

The dossier must not generate a prose repo summary with an LLM in v1. If a later
version adds generated repo summaries, that behavior must have a distinct
processor version or explicit upstream processor so evaluation knows it consumed
model-generated intermediate evidence.

## Details

`details` contains compact deterministic structured data that helps the
evaluator and auditor understand the artifact without adding duplicate large
text.

Required common fields:

- `root_iMsgX`
- `download_type`
- `source_count`
- `usable_component_count`
- `evidence_block_count`
- `truncated_component_count`
- `component_type_counts`
- `source_language_counts`

Optional source-specific objects may be included when applicable:

- tweet or X article identifiers, author handles, timestamps, and media types
- canonical URL, page title, and extracted text character count for HTML pages
- repo URL, owner, repo name, top-level entries, manifest files, and README
  presence for repo zips
- media MIME type, page count, or detected language hints for textified media

`details` must not contain raw file bytes, unrestricted full text duplicates,
model rationales, or evaluation decisions.

## Warnings

Dossier warnings are compact operational facts about evidence preparation.

Warnings should be added for:

- partial upstream failures when evidence is still assembled
- unsupported or no-text sibling sources ignored by partial assembly
- truncated evidence components
- omitted components due to configured limits
- missing optional metadata that affects auditability but not assembly

Each warning must contain:

- `code`
- `message`
- `component_id`
- `source_ref`

V1 warning code values:

- `partial_upstream_failure`
- `unsupported_source`
- `no_text_source`
- `invalid_upstream_artifact`
- `component_truncated`
- `component_omitted_due_to_limits`
- `missing_optional_metadata`

`component_id` is the affected component id, or `null` when the warning is not
component-specific. `source_ref` is the affected upstream ref, or `null` when no
single ref applies.

Warnings must not become visible `dossiers` ledger columns. They belong in
`dossier_snapshot.warnings` so the warning context travels with the exact
evidence consumed by evaluation. The evaluator may also copy compact dossier
warning messages into evaluation warnings when that is useful, but the dossier
snapshot remains the source of truth for preparation warnings.

## Validation Invariants

An assembled dossier snapshot must satisfy these invariants:

- `components` contains at least one item
- `evidence_text` contains at least one item
- every `component_id` is a positive integer unique within `components`
- every `block_id` is a positive integer unique within `evidence_text`
- every `evidence_text[].component_id` points to exactly one component
- every component has `evidence_language = "en"` in v1
- every component has a `component_type` and `text_origin` from the v1 enums
- `selected_char_count` equals the total character count of all rendered blocks
  for that component
- `original_char_count >= selected_char_count`
- `was_truncated` is true exactly when dossier limits shortened that component
- `evidence_text` contains no raw file bytes, model rationales, or evaluation
  judgments
- `evidence_limits` records the actual configured caps used for assembly
- `warnings` contains only compact structured warnings

`no_evidence` rows do not have a dossier snapshot and therefore do not satisfy
the assembled snapshot invariants.

## Evaluation Handoff

Evaluation must consume a completed `dossiers` row or its persisted artifact.

Evaluation must not:

- re-run textify
- re-run translation
- re-run dossier assembly
- reconstruct evidence from loose intermediate rows
- evaluate a `no_evidence` dossier row

If upstream preparation changes, Curio must produce new upstream processor rows
and a new dossier snapshot before evaluation is retried.

## Append-Only Idempotency

V1 idempotency is intentionally lazy and append-only.

The dossier processor must never update or overwrite an existing `dossiers` row
or artifact. A root `iMsgX` is pending only when the scheduler/store finds no
existing dossier row for that root. Once a root has an `assembled`,
`no_evidence`, or `failed` dossier row, later scheduler passes should not select
that same root as new dossier work unless an explicit future reprocessing policy
creates a new upstream identity.

If implementation reaches a path where it would need to overwrite an existing
row or artifact, that is an error. It must abort rather than mutate prior
records.

## Current Implementation Gaps

The current implementation supports only `textify` and `translate` pipeline
stages.

Missing before dossier execution can be enabled:

- `dossier` stage and `dossiers` ledger enum values
- `DossierProcessStatus`
- `DossierProcessor`
- processor exports from `curio.pipeline`
- scheduler support for `dossier`
- CLI acceptance for `curio pipeline run-stage dossier`
- store methods for grouping prepared inputs by root `iMsgX`
- artifact resolution methods for reading prior processor artifacts
- standalone dossier snapshot schema or dedicated schema validation path
- schema alignment so `dossier_snapshot` removes top-level `kind`, includes
  `components[]`, `warnings[]`, and `evidence_limits`, `components[]` uses
  `component_type`, `evidence_text[]` includes `component_id`, and the legacy
  `translation_of` pairing assumption is dropped
- config fields for dossier evidence limits
- offline tests proving evaluation consumes a persisted dossier snapshot rather
  than loose intermediate rows

These gaps describe the current state. They are not an implementation task list
for this document.

## Acceptance Scenarios

- An English text source produces one English evidence block and an `assembled`
  dossier.
- A non-English source produces an English evidence block from the upstream
  translation artifact, with source-language lineage preserved through refs and
  metadata.
- Textified media contributes suggested-file evidence blocks, using translated
  English text when upstream translation was required.
- Mixed upstream outcomes assemble partial usable evidence with compact
  warnings.
- Unsupported-only, no-text-only, or failed-only roots produce `no_evidence`
  when no usable evidence block exists.
- An oversized repo keeps deterministic selected components within configured
  limits and records truncation metadata plus compact omission warnings when
  caps exclude otherwise usable components.
- The persisted dossier artifact preserves source refs, root `iMsgX`,
  contributing records, local artifact metadata, deterministic details, evidence
  limits, and warnings.
