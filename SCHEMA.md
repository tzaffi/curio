# Curio Schema

## Purpose

Define the lean v1 online workbook shape for `curio`.

This document is normative for:

- the Google Sheets tabs owned by `curio`
- the meaning of each Curio tab
- the intended columns for each tab
- append-only evaluation semantics
- the relationship between Google Sheets rows and Google Drive JSON payloads
- the role of the derived `catalog` tab

This document is not the place to define:

- the detailed JSON payload contract
- prompt wording
- artifact-dossier extraction logic
- Codex automation scheduling
- Python module boundaries

Those belong in [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md), prompt files, automation docs, and ADRs.

## Design Principles

The v1 schema should follow these rules:

- Google Sheets remains the online operational store in v1.
- Google Drive stores the full per-evaluation JSON payload.
- `downloads` remains the upstream `iMsgX` append-only ingestion ledger.
- Curio is append-only in v1.
- `Source` is the stable artifact identity in Sheets v1.
- Curio uses one canonical `labels` registry with a lightweight `Kind` field.
- Curio uses one score scale everywhere: float `0.0` to `1.0`.
- Curio does not use aliases, merge state, separate entity tables, or a runs table in v1.
- Curio keeps one compact derived human-facing tab, `catalog`.
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

## Sheet Rules

- Header row values must match exactly.
- Sheets validation may be used for simple enums, but Curio must not depend on Sheets for relational integrity.
- No dossier text or large rationales belong in Sheets rows; that detail lives in Drive JSON.
- Before evaluating a downloads row, Curio should check whether `evaluations` already contains a row for that exact `Source`.
- If a row already exists for that `Source`, Curio should skip the evaluation, append no new row, and print a terminal message that includes the `Source` and the downloads sheet row number being skipped.
- History is never rewritten.
- The `catalog` tab is derived and may be rebuilt at any time from `downloads` and `evaluations`.

## Timestamp Format

Visible timestamp cells in Sheets should use the same UTC text format already used by `iMsgX`:

```text
YYYY-MM-DD HH:MM:SS UTC
```

Example:

```text
2026-04-20 06:15:42 UTC
```

## Drive JSON Boundary

For each accepted evaluation, Curio should upload one JSON payload to Google Drive.

That payload is the full audit artifact for the evaluation and should contain:

- the dossier used for evaluation
- the model's structured output
- paired English dossier blocks when Curio translated non-English source text for evaluation
- any artifact-type-specific details that do not fit cleanly into Sheets cells

Google Sheets should store only compact summary state plus a pointer to the Drive JSON payload.

The current Drive-payload contract is defined in [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md) and [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json).

Translation behavior within the payload is defined in [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md). This schema doc does not attempt to redefine it.

## Tabs

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

### `evaluations`

The append-only operational log of persisted accepted Curio evaluations.

Columns:

- `Evaluated At`
- `Source`
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

- `Evaluated At` is the UTC time the evaluation row was written.
- `Source` is the exact upstream artifact identity from `downloads.Source`.
- `Title`, `Creator`, `Source Language`, and `Summary EN` are compact accepted summary fields for that evaluation.
- `Summary EN` is the compact English summary field; when Curio translated non-English source text, the full translated text belongs in the Drive JSON payload under `dossier_snapshot.evidence_text`, not in Sheets.
- `Importance` is a float from `0.0` to `1.0`.
- `Labels` stores compact accepted label-score pairs for that evaluation, using canonical prefixed labels.
- `Proposals` stores compact proposed-label entries from that evaluation, also using the prefixed label convention.
- `Warnings` is an optional compact warning field for non-fatal issues observed during evaluation or dossier assembly.
- `JSON URL` points to the full Drive payload when one exists.
- Curio appends a new row only when it produces a persistable accepted evaluation for that `Source`.
- Duplicate-source skipping is a preflight no-op, not a new `evaluations` row.
- Hard `skipped` and hard `error` outcomes do not land in Sheets.
- Accepted-with-warning outcomes still land in `evaluations`.

Representation notes:

- `Labels`, `Proposals`, and `Warnings` should stay compact enough for Sheets cells.
- `Warnings` should be short operator-facing text or compact warning codes, not a dump of full diagnostics.
- Full rationale text, full translated dossier text, dossier content, and artifact-specific extraction detail belong in the Drive JSON payload, not in Sheets.

### `catalog`

The compact derived human-facing tab for normal filtering and search.

This tab is not canonical.

It should contain one row per `Source`, using the persisted row from `evaluations`.

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
- each row represents the persisted Curio view for that `Source`
- this tab is intentionally compact; it is not a one-column-per-label matrix
- normal human filtering and search should happen here

## Open Questions Intentionally Left Outside This Doc

This schema doc does not settle:

- the initial contents of the canonical `labels` registry
- the exact compact encoding used inside the `Labels` and `Proposals` cells
- the follow-on simplification of the JSON payload docs
- whether a future backend should replace Google Sheets if Curio later needs stronger relational behavior
