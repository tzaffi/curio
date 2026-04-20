# Curio Schema

## Purpose

Define the v1 online data model for `curio`.

This document is normative for:

- the Google Sheets workbook shape owned by `curio`
- the meaning of each canonical tab
- column intent for the normalized tables
- idempotency semantics for categorization
- the relationship between Google Sheets rows and Google Drive JSON payloads
- the role of the derived `categories_view` tab

This document is not the place to define:

- the detailed JSON payload contract
- prompt wording
- artifact-dossier extraction logic
- Codex automation scheduling
- Python module boundaries

Those belong in [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md), prompt files, automation docs, and ADRs.

## Design Principles

The v1 schema should follow these rules:

- Google Sheets is the online operational source of truth in v1.
- Google Drive stores per-artifact evaluation JSON for audit and history.
- `downloads` remains the `iMsgX` append-only ingestion ledger.
- `artifacts` is a thin Curio-owned current-state table, not a renamed mirror of `downloads`.
- Curio must distinguish between:
  - concepts such as `open-models` or `self-hosted-inference`
  - entities such as `Gemma`, `inferrs`, `OpenClaw`, or `Google DeepMind`
- Concepts and entities are human-governed. The model may propose new concepts or entities, but it must not create new canonical rows automatically in v1.
- Aliases solve naming variation. They do not replace merge/deprecation mechanics.
- `categories_view` is a derived convenience surface, not the canonical store.
- `overall_importance` and assignment `relevance` are separate concepts and must remain separate in the schema.

## Naming Conventions

- tab names are plural snake_case except the already-chosen `categories_view`
- primary keys are stored in an `id` column
- foreign keys are named `<table_singular>_id`
- Curio-owned timestamp columns use `_at`
- Curio-owned URL columns use `_url`
- status columns use short lowercase text enums

When `curio` intentionally carries an exact upstream header from `downloads`, that header should be preserved verbatim even if it does not match Curio's normal naming style.

## Timestamp Format

All persisted timestamps must use UTC RFC 3339 text with a trailing `Z`.

Example:

```text
2026-04-19T05:31:22.123Z
```

## Version Tracking

Every successful categorization must record the versions that produced it.

V1 tracks these independently:

- `schema_version`
- `prompt_version`
- `vocabulary_version`

`vocabulary_version` covers the current concept/entity registry state, including aliases and concept relations.

An artifact is considered categorized for the current contract only when its latest successful row state matches the versions targeted by the current run.

If any of those versions change later, the artifact is eligible for re-categorization even if it was successfully categorized before.

## Idempotency Rules

`curio` should model one row in `artifacts` per unique upstream artifact.

That row is the current accepted state for that artifact, not an append-only event log.

In v1, the unique upstream artifact identity is anchored by the exact `downloads.Source` value.

The `artifacts` table should carry that join field under the exact header name `Source`.

An artifact counts as successfully categorized when all of the following are true:

- `evaluation_status` is `categorized`
- `categorized_at` is populated
- `latest_run_id` is populated
- `latest_json_url` is populated
- `schema_version`, `prompt_version`, and `vocabulary_version` reflect the accepted evaluation

`artifact_concepts` and `artifact_entities` should store only the current accepted positive assignments for that artifact.

When an artifact is re-categorized, `curio` should replace that artifact's prior `artifact_concepts` and `artifact_entities` rows with the new accepted sets.

No row should be stored in an assignment table for relevance `0`.

`artifact_concepts` should store only direct concept assignments.

If `self-hosted-inference` is narrower than `local-inference`, the broader `local-inference` hit should come from `concept_relations`, not from duplicating both assignments on every artifact by default.

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

V1 `curio` should treat `downloads` as the authoritative ingestion/provenance ledger.

`curio` should not mirror those columns into `artifacts` under renamed Curio-specific names.

V1 should carry only one exact upstream field on `artifacts`: `Source`.

That field exists only as the durable join back to `downloads` and should exactly match `downloads.Source`.

Other upstream provenance such as `Date`, `X Date`, `iMsgX`, `Column`, `Type`, and `Object` should be read from `downloads` directly or surfaced through derived views such as `categories_view`.

## Drive JSON Boundary

For each successful categorization, `curio` should upload one JSON payload to Google Drive.

That payload is the full audit artifact for the accepted evaluation and should contain:

- the artifact dossier used for evaluation
- the model's structured output
- version metadata
- any artifact-type-specific details that do not fit cleanly into normalized Sheets columns

Google Sheets should store the current normalized cross-artifact state plus a pointer to that latest accepted JSON payload.

The full Drive-payload contract is defined in [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md) and [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json).

V1 should not add an `artifact_evaluations` sheet unless history in Drive plus `runs` proves insufficient.

## Tables

### `artifacts`

One row per unique artifact known to `curio`.

This is the canonical current-state table for artifacts.

Columns:

- `id`
- `Source`
- `title`
- `creator`
- `source_language`
- `summary_en`
- `overall_importance`
- `evaluation_status`
- `latest_run_id`
- `latest_json_url`
- `schema_version`
- `prompt_version`
- `vocabulary_version`
- `categorized_at`
- `last_error`
- `created_at`
- `updated_at`

Notes:

- `id` is the durable Curio artifact key and must be deterministic from the stable upstream `Source` value, not from Curio row order.
- `Source` is the exact upstream header name from `downloads` and is the v1 join field back to `downloads.Source`.
- `artifacts` deliberately does not copy or rename the rest of the `downloads` provenance columns.
- `title`, `creator`, `source_language`, and `summary_en` are cross-artifact summary fields and may be blank until categorization succeeds.
- `overall_importance` uses the v1 integer scale `0-5`.
- `evaluation_status` is one of:
  - `pending`
  - `categorized`
  - `error`
  - `skipped`
- `latest_json_url` points to the latest accepted Drive JSON payload, not to every prior evaluation.

Constraints:

- primary key on `id`
- unique constraint on `Source`
- `overall_importance` must be an integer from `0` to `5` when populated

### `concepts`

Defines the approved canonical concept vocabulary currently usable by `curio`.

Columns:

- `id`
- `pref_label`
- `definition`
- `scope_note`
- `status`
- `merged_into_concept_id`
- `created_at`
- `updated_at`

Notes:

- `id` should be a stable slug-like machine key.
- `pref_label` is the canonical human-facing concept label.
- `scope_note` is optional operator guidance about boundaries and intended use.
- `status` is one of:
  - `active`
  - `deprecated`
  - `merged`

Constraints:

- primary key on `id`
- unique constraint on `pref_label`
- foreign key `merged_into_concept_id -> concepts(id)` when populated

Implementation notes:

- aliases live in `concept_aliases`, not in this row.
- if a concept is merged, the row stays addressable for audit/history but should point at the surviving concept via `merged_into_concept_id`.

### `concept_aliases`

Stores alternate strings that should resolve to a canonical concept.

Columns:

- `id`
- `concept_id`
- `alias`
- `created_at`
- `updated_at`

Notes:

- aliases capture naming variation such as acronyms, old phrasing, or merged concept names
- aliases solve lexical equivalence, not concept lifecycle by themselves

Constraints:

- primary key on `id`
- foreign key `concept_id -> concepts(id)`
- unique constraint on normalized `alias`

### `concept_relations`

Stores direct concept-to-concept relations.

Columns:

- `id`
- `from_concept_id`
- `relation_type`
- `to_concept_id`
- `created_at`
- `updated_at`

Notes:

- `relation_type` is one of:
  - `broader`
  - `related`
- `broader` records only the direct broader parent
- `narrower` is implied as the inverse of `broader`
- `related` is associative rather than hierarchical

Constraints:

- primary key on `id`
- foreign key `from_concept_id -> concepts(id)`
- foreign key `to_concept_id -> concepts(id)`
- unique constraint on `(from_concept_id, relation_type, to_concept_id)`

### `artifact_concepts`

Stores the current accepted direct concept assignments for artifacts.

Columns:

- `id`
- `artifact_id`
- `concept_id`
- `relevance`
- `rationale`
- `run_id`
- `created_at`
- `updated_at`

Notes:

- store one row only when the concept positively applies to the artifact
- absence of a row means relevance `0`
- `relevance` uses the v1 integer scale `1-3`
- `rationale` should be short and specific enough to justify the assignment
- `run_id` points to the run that produced the current accepted assignment

Constraints:

- primary key on `id`
- foreign key `artifact_id -> artifacts(id)`
- foreign key `concept_id -> concepts(id)`
- foreign key `run_id -> runs(id)`
- unique constraint on `(artifact_id, concept_id)`
- `relevance` must be an integer from `1` to `3`

### `concept_proposals`

Stores model-suggested concepts that are not yet part of the approved canonical concept vocabulary.

Columns:

- `id`
- `artifact_id`
- `proposed_concept_id`
- `pref_label`
- `definition`
- `relevance`
- `rationale`
- `closest_existing_concepts`
- `status`
- `proposed_by_run_id`
- `reviewed_at`
- `created_at`
- `updated_at`

Notes:

- `proposed_concept_id` should be a proposed slug-like machine key
- `relevance` uses the same v1 integer scale `1-3` as accepted artifact-concept assignments
- `closest_existing_concepts` is optional operator-facing context
- `status` is one of:
  - `pending`
  - `accepted`
  - `rejected`

Constraints:

- primary key on `id`
- foreign key `artifact_id -> artifacts(id)`
- foreign key `proposed_by_run_id -> runs(id)`
- `relevance` must be an integer from `1` to `3`

### `entities`

Defines canonical named entities currently usable by `curio`.

Columns:

- `id`
- `canonical_name`
- `entity_type`
- `status`
- `merged_into_entity_id`
- `created_at`
- `updated_at`

Notes:

- `entity_type` is one of:
  - `person`
  - `organization`
  - `model`
  - `product`
  - `technology`
  - `repo`
  - `other`
- `status` is one of:
  - `active`
  - `deprecated`
  - `merged`

Constraints:

- primary key on `id`
- unique constraint on `(canonical_name, entity_type)`
- foreign key `merged_into_entity_id -> entities(id)` when populated

### `entity_aliases`

Stores alternate strings that should resolve to a canonical entity.

Columns:

- `id`
- `entity_id`
- `alias`
- `created_at`
- `updated_at`

Constraints:

- primary key on `id`
- foreign key `entity_id -> entities(id)`
- unique constraint on normalized `alias`

### `artifact_entities`

Stores the current accepted entity mentions for artifacts.

Columns:

- `id`
- `artifact_id`
- `entity_id`
- `relevance`
- `rationale`
- `run_id`
- `created_at`
- `updated_at`

Notes:

- store one row only when the entity is materially about the artifact, not for every incidental mention
- `relevance` uses the v1 integer scale `1-3`

Constraints:

- primary key on `id`
- foreign key `artifact_id -> artifacts(id)`
- foreign key `entity_id -> entities(id)`
- foreign key `run_id -> runs(id)`
- unique constraint on `(artifact_id, entity_id)`
- `relevance` must be an integer from `1` to `3`

### `entity_proposals`

Stores model-suggested entities that are not yet part of the canonical entity registry.

Columns:

- `id`
- `artifact_id`
- `proposed_entity_id`
- `canonical_name`
- `entity_type`
- `relevance`
- `rationale`
- `closest_existing_entities`
- `status`
- `proposed_by_run_id`
- `reviewed_at`
- `created_at`
- `updated_at`

Notes:

- `status` is one of:
  - `pending`
  - `accepted`
  - `rejected`

Constraints:

- primary key on `id`
- foreign key `artifact_id -> artifacts(id)`
- foreign key `proposed_by_run_id -> runs(id)`
- `relevance` must be an integer from `1` to `3`

### `runs`

Stores batch-level execution metadata for Curio processing runs.

Columns:

- `id`
- `trigger_mode`
- `started_at`
- `completed_at`
- `status`
- `requested_batch_size`
- `processed_artifact_count`
- `categorized_artifact_count`
- `error_artifact_count`
- `schema_version`
- `prompt_version`
- `vocabulary_version`
- `notes`
- `created_at`
- `updated_at`

Notes:

- `trigger_mode` is one of:
  - `manual`
  - `automation`
- `status` is one of:
  - `running`
  - `succeeded`
  - `partial`
  - `failed`

Constraints:

- primary key on `id`
- `requested_batch_size`, `processed_artifact_count`, `categorized_artifact_count`, and `error_artifact_count` must be non-negative integers

### `categories_view`

Derived wide sheet for human scanning, sorting, and filtering.

This tab is not canonical.

It should be rebuilt from `downloads`, `artifacts`, `concepts`, `artifact_concepts`, `entities`, and `artifact_entities`.

Recommended fixed columns:

- `Date`
- `X Date`
- `iMsgX`
- `Source`
- `Column`
- `Type`
- `Object`
- `artifact_id`
- `evaluation_status`
- `categorized_at`
- `title`
- `creator`
- `source_language`
- `summary_en`
- `overall_importance`
- `entities`
- `latest_json_url`
- `latest_run_id`

`entities` should be a compact human-readable list of canonical entity names or ids for the artifact.

After the fixed columns, `categories_view` should add one column per active concept `id`.

Cell semantics for dynamic concept columns:

- blank means the concept does not directly apply
- `1`, `2`, or `3` means the accepted direct concept relevance

Implementation notes:

- upstream provenance columns in this view should retain the exact `downloads` header names
- dynamic concept columns should be generated in a stable order, preferably the row order of active concepts in `concepts`
- `categories_view` is concept-centric in v1; entity state is summarized in the fixed `entities` column rather than exploded into one column per entity

## Open Questions Intentionally Left Outside This Doc

This schema doc does not settle:

- the initial concept registry contents
- the initial entity registry contents
- the exact artifact-key derivation algorithm
- the initial automation batch size
- whether Curio needs a second derived view focused on entity-centric browsing
