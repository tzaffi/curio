# Curio Schema

## Purpose

Define the lean v1 online workbook shape for `curio`.

This document is normative for:

- the Google Sheets tabs owned by `curio`
- the meaning of each Curio tab
- the intended columns for each tab
- append-only processor-ledger semantics
- the relationship between Google Sheets rows and persisted artifacts
- the role of the derived `catalog` tab

This document is not the place to define:

- the detailed JSON payload contract
- detailed translation policy
- LLM provider calling policy
- CLI subcommand flags
- prompt wording
- pipeline processor contracts
- Codex automation scheduling
- Python module boundaries

Those belong in [PIPELINE.md](/Users/zeph/github/tzaffi/curio/PIPELINE.md), [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md), [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md), [LLM-CALLER.md](/Users/zeph/github/tzaffi/curio/LLM-CALLER.md), [CLI.md](/Users/zeph/github/tzaffi/curio/CLI.md), prompt files, automation docs, and ADRs.

## Design Principles

The v1 schema should follow these rules:

- Google Sheets remains the online operational store in v1.
- Google Drive or a local artifact store stores full processor artifacts.
- `downloads` remains the upstream `iMsgX` append-only ingestion ledger.
- Curio is append-only in v1.
- `Source` is the stable artifact identity in Sheets v1.
- Curio uses one compact append-only ledger per pipeline processor.
- Curio uses one canonical `labels` registry with a lightweight `Kind` field.
- Curio uses one score scale everywhere: float `0.0` to `1.0`.
- Curio does not use aliases, merge state, separate entity tables, or a runs table in v1.
- Curio keeps one compact derived human-facing tab, `catalog`, built from completed accepted evaluations.
- We are optimizing for portability, inspectability, and low operational complexity over relational purity.

## Relationship To `iMsgX`

`curio` sits above `iMsgX` and begins from the `iMsgX` downloads sheet.

The upstream downloads sheet currently has these columns:

- `Date`
- `X Date`
- `iMsgX`
- `Source`
- `Column`
- `Type`
- `Object`

V1 `curio` should treat `downloads` as the authoritative append-only ingestion and provenance log.

Curio-owned state should live in Curio tabs, not by mutating or renaming `downloads` columns.

Every Curio processor row should retain a root reference to the exact
`downloads` tab row that produced it, even when its immediate source is another
Curio processor row. In the current iMsgX sheet, the `iMsgX` cell in the
downloads row is expected to be the operator-facing Google Sheets row URL.

## Sheet Rules

- Header row values must match exactly.
- Sheets validation may be used for simple enums, but Curio must not depend on Sheets for relational integrity.
- No dossier text, large rationales, or generated text artifacts belong in Sheets rows; that detail lives in persisted artifacts.
- Before appending a processor row, Curio should check whether that processor already has a terminal row for the same processor input key.
- Duplicate reruns are no-ops by default. They should not append another skipped row.
- Newly handled ineligible work should append a compact row with a specific status such as `already_text`, `already_english`, `unsupported`, `no_text`, or `no_evidence`.
- Failed attempts may append compact `failed` rows. They must not include stack traces, raw prompts, secrets, or large provider payloads in Sheets.
- `Object` is populated only when the processor creates a Google Drive object.
- History is never rewritten.
- The `catalog` tab is derived and may be rebuilt at any time from `downloads` and completed accepted `evaluations` rows.

## Timestamp Format

Visible timestamp cells in Sheets should use the same UTC text format already used by `iMsgX`:

```text
YYYY-MM-DD HH:MM:SS UTC
```

Example:

```text
2026-04-20 06:15:42 UTC
```

## Persisted Artifact Boundary

Each processor owns a Google Drive folder with the same name as its processor
tab:

```text
textifications/
translations/
dossiers/
```

When a processor creates an object, the row's `Object` cell links to the Google
Drive object created in that processor's folder.

For v1, each object-creating preparation processor row creates one JSON object:

Recommended artifacts include:

- textify response JSON
- translation response JSON
- dossier snapshot JSON
- evaluation payload JSON

Skipped and failed processor rows do not create or link Drive objects.

For each accepted evaluation, Curio should upload one JSON payload to Google Drive.

That payload is the full audit artifact for the evaluation and should contain:

- the exact dossier snapshot used for evaluation
- the model's structured output
- paired English dossier blocks when Curio translated non-English source text for evaluation
- any artifact-type-specific details that do not fit cleanly into Sheets cells

Google Sheets should store only compact summary state plus a pointer to the Drive JSON payload.

The dossier snapshot is also a first-class pipeline artifact. It should be
persisted before evaluation, and the evaluation row should point back to the
`dossiers` row or artifact that was evaluated.

The current Drive-payload contract is defined in [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md) and [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json).

Translation behavior within the payload is defined in [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md). This schema doc does not attempt to redefine it.

## Tabs

V1 uses these Curio-owned processor ledger tabs:

- `textifications`
- `translations`
- `dossiers`
- `evaluations`

The existing `labels` and derived `catalog` tabs remain Curio-owned, but they
are not processor ledgers.

Preparation processor tabs are intentionally lean. Detailed lineage,
processor/model/cost metadata, warnings, and contributing row refs belong in the
created JSON object, not in visible Sheets columns.

### `labels`

The canonical Curio label registry.

Columns:

- `Label`
- `Kind`
- `Parent`
- `Description`

Semantics:

- `Label` is the canonical identity and must always include its kind prefix.
- `Kind` is one of:
  - `topic`
  - `entity`
- label prefixes are:
  - `t:` for topics
  - `e:` for entities
- examples:
  - `t:oracle`
  - `e:oracle`
- `Kind` must agree with the `Label` prefix.
- `Parent` is optional and points to one broader canonical `Label`, using the full prefixed label value.
- `Description` is short operator guidance about intended usage and boundaries.
- Curio does not model aliases in v1.
- If a proposal is really another way to name an existing label, review should map it to the existing canonical `Label` instead of creating alias or merge state.
- `related` edges are out of scope for v1. Only optional single-parent hierarchy is supported.

### `textifications`

The append-only ledger owned by `TextifyProcessor`.

Columns:

- `Date`
- `X Date`
- `iMsgX`
- `Type`
- `Source`
- `Status`
- `Object`

Semantics:

- One row is appended for every `downloads` row.
- `Date`, `X Date`, and `iMsgX` are copied from the upstream downloads row.
- `Type` is copied from `downloads.Type`.
- `Source` is a Google Sheets row URL or stable row ref to the exact downloads
  row consumed.
- `Status` is one of:
  - `converted`
  - `already_text`
  - `unsupported`
  - `no_text`
  - `failed`
- `Object` links to the created textification JSON in the `textifications/`
  Google Drive folder only when `Status = converted`.
- `Object` is blank for `already_text`, `unsupported`, `no_text`, and `failed`.
- Large extracted text, warnings, processor metadata, model metadata, cost, and
  hashes belong in the created JSON object, not in this sheet.

### `translations`

The append-only ledger owned by `TranslateProcessor`.

Columns:

- `Date`
- `X Date`
- `iMsgX`
- `Type`
- `Source`
- `Status`
- `Object`

Semantics:

- One row is appended for every text-bearing source object.
- Already-text downloads reach translation through textification passthrough.
- `Date`, `X Date`, `iMsgX`, and `Type` are copied through from the root
  downloads row.
- `Source` is a Google Sheets row URL or stable row ref to the textification row
  consumed.
- `Status` is one of:
  - `translated`
  - `already_english`
  - `failed`
- `Object` links to the created translation JSON in the `translations/` Google
  Drive folder only when `Status = translated`.
- `Object` is blank for `already_english` and `failed`.
- Full translated text, warnings, processor metadata, model metadata, cost, and
  hashes belong in the created JSON object. Translated text later appears in
  `dossier_snapshot.evidence_text`, not in this sheet.

### `dossiers`

The append-only ledger owned by `DossierProcessor`.

Columns:

- `Date`
- `X Date`
- `iMsgX`
- `Status`
- `Object`

Semantics:

- One row is appended for every upstream `iMsgX` row that reaches dossier
  assembly.
- A dossier groups all prepared source objects sharing that `iMsgX`.
- `Date`, `X Date`, and `iMsgX` are copied from the upstream iMsgX/downloads
  row.
- There is no `Source` column because a dossier may package multiple source
  objects. Contributing source refs live inside the dossier JSON.
- There is no `Type` column because a dossier may package multiple source
  types.
- `Status` is one of:
  - `assembled`
  - `no_evidence`
  - `failed`
- `Object` links to the created dossier JSON in the `dossiers/` Google Drive
  folder only when `Status = assembled`.
- `Object` is blank for `no_evidence` and `failed`.
- Contributing row refs, warnings, processor metadata, model metadata, cost, and
  hashes belong in the created dossier JSON object, not in this sheet.
- This tab is the audit boundary between preparation and evaluation.

### `evaluations`

The append-only ledger owned by `EvaluateProcessor`.

Recommended columns:

- `Evaluated At`
- `Source`
- `iMsgX Row`
- `iMsgX`
- `Status`
- `Reason`
- `Source Stage`
- `Source Row`
- `Source Ref`
- `Dossier Row`
- `Dossier URL`
- `Output Ref`
- `Output SHA256`
- `Warnings`
- `Processor`
- `Processor Version`
- `LLM Caller`
- `Model`
- `Cost Estimate`
- `Title`
- `Creator`
- `Source Language`
- `Summary EN`
- `Importance`
- `Labels`
- `Proposals`
- `JSON URL`

Semantics:

- `Evaluated At` is the UTC time the evaluation row was written. It intentionally uses the existing evaluation-facing name instead of `Processed At`.
- `Source` is the exact upstream artifact identity from `downloads.Source`.
- `iMsgX Row` and `iMsgX` identify the root upstream `downloads` row for the
  evaluated artifact.
- Input rows come from completed `dossiers` rows.
- `Dossier Row` and `Dossier URL` identify the exact snapshot row or artifact evaluated.
- Completed accepted rows point to a full evaluation payload through `JSON URL`, which is the evaluation-stage synonym for `Output URL`.
- `Title`, `Creator`, `Source Language`, and `Summary EN` are compact accepted summary fields for that evaluation.
- `Summary EN` is the compact English summary field; when Curio translated non-English source text, the full translated text belongs in the Drive JSON payload under `dossier_snapshot.evidence_text`, not in Sheets.
- `Importance` is a float from `0.0` to `1.0`.
- `Labels` stores compact accepted label-score pairs for that evaluation, using canonical prefixed labels.
- `Proposals` stores compact proposed-label entries from that evaluation, also using the prefixed label convention.
- `Warnings` is an optional compact warning field for non-fatal issues observed during evaluation or dossier assembly.
- Skipped and failed rows are operational ledger entries and should keep summary fields blank unless a compact value is meaningful.
- Accepted-with-warning outcomes still land in `evaluations` as completed rows with warning text.

Representation notes:

- `Labels`, `Proposals`, and `Warnings` should stay compact enough for Sheets cells.
- `Warnings` should be short operator-facing text or compact warning codes, not a dump of full diagnostics.
- Full rationale text, full translated dossier text, dossier content, and artifact-specific extraction detail belong in the Drive JSON payload, not in Sheets.
- `catalog` derives only from completed accepted evaluation rows. It ignores skipped and failed evaluation rows.

### `catalog`

The compact derived human-facing tab for normal filtering and search.

This tab is not canonical.

It should contain one row per `Source`, using completed accepted rows from
`evaluations`.

Recommended columns:

- `Date`
- `X Date`
- `iMsgX`
- `Source`
- `Column`
- `Type`
- `Object`
- `Evaluated At`
- `Title`
- `Creator`
- `Source Language`
- `Summary EN`
- `Importance`
- `Labels`
- `Proposals`
- `Warnings`
- `JSON URL`

Semantics:

- upstream provenance columns should retain the exact `downloads` header names
- each row represents the accepted Curio view for that `Source`
- skipped and failed processor rows do not appear here
- this tab is intentionally compact; it is not a one-column-per-label matrix
- normal human filtering and search should happen here

## Open Questions Intentionally Left Outside This Doc

This schema doc does not settle:

- the initial contents of the canonical `labels` registry
- the exact compact encoding used inside the `Labels` and `Proposals` cells
- the follow-on simplification of the JSON payload docs
- whether a future backend should replace Google Sheets if Curio later needs stronger relational behavior
