# Curio Bootstrap

## Purpose

Define the normative v1 bootstrap workflow for creating or refreshing a candidate Curio `labels` registry.

This document is normative for:

- the bootstrap workspace and tab set
- the bootstrap sampling contract
- row-by-row bootstrap evaluation and promotion semantics
- bootstrap outputs
- the handoff from bootstrap output to production `labels`

This document is not the place to define:

- the normal production evaluation workflow
- steady-state proposal review after bootstrap
- the detailed Google Sheets workbook contract
- the persisted Drive JSON payload contract

Those belong in [SCHEMA.md](/Users/zeph/github/tzaffi/curio/SCHEMA.md) and [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md).

## Design Principles

The v1 bootstrap should follow these rules:

- Bootstrap exists to derive or refresh a candidate `labels` registry from a controlled sample.
- Bootstrap is a test-run workflow, not the normal production evaluation workflow.
- Bootstrap sampling is Tweet-anchored, but the resulting `downloads` sample may include Tweet rows and other associated artifact types.
- Bootstrap uses the same `evaluations`, `catalog`, and Drive-payload semantics already defined elsewhere.
- Bootstrap is append-only within a given run workspace.
- Bootstrap requires reproducible sample selection and processing order, but it does not require identical semantic output across reruns.
- New labels become available only after the row that proposed them has been fully persisted.
- Bootstrap never rewrites earlier run-local `evaluations` rows or earlier Drive JSON payloads.
- Bootstrap never auto-replaces production `labels`.

## Relationship To Existing Curio Contracts

Bootstrap does not define a separate sheet model or a separate payload format.

Instead:

- run-local tabs such as `labels-test001`, `evaluations-test001`, and `catalog-test001` use the same tab meanings and column contracts defined in [SCHEMA.md](/Users/zeph/github/tzaffi/curio/SCHEMA.md).
- each accepted bootstrap evaluation writes the same payload shape defined in [JSON-PAYLOAD.md](/Users/zeph/github/tzaffi/curio/JSON-PAYLOAD.md) and [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json)
- `Proposals` remains an audit field in `evaluations-test001`; promotion into `labels-test001` does not rewrite the stored row

## Bootstrap Workspace

Bootstrap runs in the same workbook as production, but in isolated run-local tabs named from a run slug provided at the start of the run.

If the run slug is `test001`, the workspace consists of:

- `iMsgX-test001`
- `downloads-test001`
- `labels-test001`
- `evaluations-test001`
- `catalog-test001`

If the next run slug is `test002`, the corresponding workspace is:

- `iMsgX-test002`
- `downloads-test002`
- `labels-test002`
- `evaluations-test002`
- `catalog-test002`

For readability, the examples below use `test001`, but the bootstrap rules apply to whatever run slug was chosen for that run.

Bootstrap initial state is an explicit run setup choice.

Supported v1 starting states:

- fresh bootstrap:
  - `labels-test001` contains the required header row and no data rows
  - `evaluations-test001` starts empty
  - `catalog-test001` starts empty
- seeded bootstrap:
  - `labels-test001` is initialized from an existing labels registry, typically production `labels`
  - `evaluations-test001` and `catalog-test001` may be initialized from a chosen baseline or left empty, depending on the purpose of the run

In all cases:

- there is no bootstrap proposals queue or review tab in v1
- the starting state must be explicit before the run begins
- production tabs are not modified by the bootstrap run

## Sampling Contract

Bootstrap sampling begins from the production `iMsgX` tab.

Bootstrap first selects `50` random Tweet entries from `iMsgX`.

Those selected Tweet entries define the bootstrap sample set.

`downloads-test001` is then built from all production `downloads` rows associated with that sampled `iMsgX` set.

Sampling rules:

- the default sample size is exactly `50`
- selection is random but reproducible from an explicit RNG seed
- the same eligible `iMsgX` corpus and the same seed must produce the same selected Tweet set
- once the sample is chosen, processing order is the original row order from production `downloads`, not random order

Bootstrap test tabs must reflect the selected sample:

- `iMsgX-test001` contains the sampled Tweet entries
- `downloads-test001` contains all associated `downloads` rows for that sampled `iMsgX` set, ordered by their original production row order

## Canonical Label Form

Bootstrap promotion uses one canonical label form:

- labels must retain the existing kind prefix: `t:` for topics and `e:` for entities
- the label body after the prefix must be normalized to lowercase kebab-case
- example canonical labels:
  - `t:open-models`
  - `e:anthropic`

If a proposal includes `parent`, that parent value must also be canonicalized before promotion lookup.

Canonicalization is used only for promotion and dedupe.

Bootstrap must not rewrite the `evaluation.proposals` array stored in the persisted row or Drive payload.

## Bootstrap Algorithm

Bootstrap runs one sampled `downloads-test001` row at a time.

For each row in `downloads-test001`, Curio must:

1. Read the current `labels-test001` registry.
2. Assemble the dossier and evaluate the row against that current registry.
3. Persist the accepted evaluation to `evaluations-test001`.
4. Persist the corresponding Drive JSON payload using the normal Curio payload contract.
5. Rebuild or update `catalog-test001` using the normal Curio derived-tab semantics.
6. Read that row's emitted `evaluation.proposals` exactly as persisted.
7. Canonicalize each proposal's `label`, and canonicalize `parent` when present.
8. Dedupe proposals against the existing `labels-test001` registry using canonical `(label, kind, parent)`.
9. Append each new canonical proposal immediately to `labels-test001`.

Promotion rules:

- promotion happens only after the row has already been persisted
- row `N` is evaluated against the registry state that existed before row `N` began
- labels promoted from row `N` are available starting at row `N+1`
- later promotions must not change earlier `Proposals` cells, earlier `evaluations-test001` rows, or earlier Drive JSON payloads

Bootstrap stop rule:

- bootstrap stops after the fixed selected sample of `50` rows has been processed once

## Outputs

A completed bootstrap run produces:

- a candidate seed registry in `labels-test001`
- an append-only accepted evaluation history in `evaluations-test001`
- a derived `catalog-test001`
- one Drive JSON payload per accepted evaluation, using the normal Curio payload contract

The bootstrap output is the full resulting `labels-test001` registry, not an intermediate proposals queue.

## Handoff To Production

Bootstrap handoff is manual and whole-set.

That means:

- an operator reviews the completed `labels-test001` registry as a candidate seed registry
- production `labels` changes only if the operator deliberately promotes that resulting registry into production
- bootstrap does not auto-replace production `labels`
- bootstrap does not incrementally merge labels into production during the run

Future steady-state proposal review and production registry growth are intentionally out of scope for this document.

## Invariants

The bootstrap workflow must preserve all of the following:

- explicit initial registry state
- no initial proposals queue
- reproducible sample selection
- reproducible processing order
- append-only evaluation history
- immediate availability of promoted labels for the next row only
- no rewriting of earlier rows or earlier payloads after later promotions
- no production `labels` mutation without explicit manual handoff

## Glossary

- `bootstrap run`
  One isolated run-local workspace such as `test001` that processes one fixed sampled Tweet-anchored set and its associated `downloads` rows.
- `run slug`
  The operator-provided suffix for one bootstrap run, such as `test001` or `test002`, used to name that run's isolated tabs.
- `seed registry`
  The candidate label registry produced by bootstrap, represented by the completed run-local `labels` tab before manual production handoff.
- `promotion`
  The act of taking a proposal emitted by a persisted bootstrap evaluation, canonicalizing and deduping it, and appending it to `labels-test001`.
- `handoff`
  The deliberate manual promotion of the completed bootstrap registry into production `labels`.
- `canonical label`
  A prefixed label whose body has been normalized to lowercase kebab-case and is used for bootstrap lookup and dedupe.

## Acceptance Scenarios

The bootstrap spec is satisfied only if all of the following are true:

- the same seed and the same eligible `iMsgX` corpus produce the same sampled Tweet set
- the same sampled Tweet set produces the same derived `downloads-test001` row set and the same processing order
- a proposal first emitted on row `N` is available to row `N+1`
- a promoted label does not erase or rewrite row `N`'s stored `Proposals`
- rerunning bootstrap against the same sampled corpus is not required to produce identical semantic output, because the model is non-deterministic
- production `labels` changes only through manual whole-set handoff
