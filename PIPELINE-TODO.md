# Curio Pipeline Implementation TODO

## Purpose

Create the planning trail for Curio pipelining.

The first implementation step is not code. The first implementation step is to
write a normative [PIPELINE.md](PIPELINE.md) that specifies how Curio processors,
ledgers, intermediate artifacts, skipped rows, and final evaluation fit together.

Do not implement the pipeline until `PIPELINE.md` exists and has been reviewed.

## Legend

- [x] Done in this planning pass
- [~] Current review boundary / paused for guidance
- [ ] Not started
- [lock] Must not start until the previous step is reviewed and passes `make check`
- [test] Requires `make check`: Ruff, Ty, pytest, 100% coverage
- [live] Requires explicit live opt-in; never part of default `make check`

## Completed

[x] **Checkpoint 0: Capture pipeline planning baseline**

- Reviewed the current pipeline-adjacent docs:
  - [TODO-TEXTIFY.md](TODO-TEXTIFY.md)
  - [TEXTIFY.md](TEXTIFY.md)
  - [TRANSLATE.md](TRANSLATE.md)
  - [JSON-PAYLOAD.md](JSON-PAYLOAD.md)
  - [SCHEMA.md](SCHEMA.md)
- Reviewed the current reusable workflow services:
  - `curio.textify.TextifyService`
  - `curio.translate.TranslationService`
  - `curio.llm_caller.LlmClient`
- Confirmed there is not yet a first-class pipeline module or evaluation service
  module in `src/curio`.
- Captured the requested revised working order:

```text
textify -> translate -> dossier -> evaluate
```

- Clarified that `download` is not a Curio pipeline processor in v1 because
  `iMsgX` already owns download and the `downloads` ledger.
- Clarified that `persist` is not a standalone pipeline processor in v1 because
  every processor owns its own artifact persistence and row recording.
- This TODO update intentionally introduces no code, schemas, fixtures, config
  examples, or implementation docs beyond this planning file.

[x] **Checkpoint 1C: Review boundary accepted for initial implementation**

- Checkpoint 1A created [PIPELINE.md](PIPELINE.md).
- Checkpoint 1B reconciled the adjacent normative docs.
- The initial implementation boundary is intentionally moved forward for
  `textify` and `translate` only.
- `dossier` and `evaluate` remain documented v1 stages, but their processors and
  scheduler integration are deferred until the underlying capabilities exist.
- Processor implementation should use an abstract `Processor` base class. Store
  and artifact boundaries should remain protocols.

## Working Thesis

Curio v1 should treat the pipeline as:

```text
downloads ledger row
  -> textify
  -> translate
  -> dossier
  -> evaluate
```

`downloads ledger row` is an upstream input source, not a Curio-owned processor.
Curio should read it and reference it, but should not mutate or replace it.

Every Curio-owned processor should:

- find the next unhandled input record
- decide eligibility
- record skipped rows for newly handled ineligible inputs
- process eligible inputs
- persist full output artifacts when useful
- append a compact row to the processor-owned tab
- expose `output_source` for downstream processors

Duplicate reruns are different from skipped work. If a completed or skipped row
already exists for the same processor input and processor version, the pipeline
should usually no-op rather than append another skipped row.

## Dossier Snapshot Recommendation

Keep `dossier snapshot` as a real pipeline stage, but rename the mental model
from "artifact dossier extraction" to "dossier assembly/snapshot."

Reasoning:

- Textify and translate produce inputs that evaluation depends on.
- Evaluation needs one immutable, exact, model-visible English-centered evidence
  object.
- Without a dossier snapshot stage, evaluation has to re-derive its input from
  whichever textify or translate rows happen to be current at run time.
- The existing [JSON-PAYLOAD.md](JSON-PAYLOAD.md) contract already says
  `dossier_snapshot` is the exact normalized evidence shown to the model.
- A separate assembly step gives us a stable audit boundary: "this is what the
  evaluator saw."
- It also makes failed or retried evaluations easier to debug because the
  prepared evidence can exist before evaluation succeeds.

This does not mean dossier assembly has to be expensive or LLM-backed. V1 should
prefer a deterministic `DossierProcessor` that gathers the best available
source-language and English blocks, assigns stable block IDs, applies truncation
policy, records warnings, writes one snapshot artifact, and appends one compact
row.

Recommended v1 shape:

```text
textify -> translate -> dossier -> evaluate
```

The old order:

```text
download row -> artifact dossier extraction -> textify -> translate -> evaluate -> persist
```

should be retired or reframed. Some deterministic extraction still happens
inside source adapters and processors, but the persisted dossier snapshot should
be assembled after textify and translate.

## First Spec: `PIPELINE.md`

[lock] [x] **Checkpoint 1A: Create normative `PIPELINE.md`**

`PIPELINE.md` should define the v1 pipeline behavior before any pipeline code is
written.

It should include:

- purpose and non-goals
- pipeline order
- relationship to `iMsgX` and the upstream `downloads` tab
- definition of a pipeline processor
- definition of processor input, output, artifact refs, and row refs
- common status vocabulary
- skipped-row semantics
- duplicate/idempotency semantics
- error and retry semantics
- common processor row fields
- per-processor tab ownership
- artifact persistence rules
- dossier snapshot assembly rules
- evaluation input rules
- synchronous v1 scheduler rules
- v2 concurrency notes
- CLI/operator workflow
- testing requirements
- open questions deferred out of v1

`PIPELINE.md` should explicitly choose whether v1 has these tabs:

- `textifications`
- `translations`
- `dossiers`
- `evaluations`

Recommendation: use all four Curio-owned tabs. The `dossiers` tab is
worth it if evaluation can fail, be retried, or be audited independently.

`PIPELINE.md` should explicitly reconcile this TODO with current docs:

- [SCHEMA.md](SCHEMA.md) currently defines only `labels`, `evaluations`, and
  derived `catalog` as Curio-owned tabs.
- [SCHEMA.md](SCHEMA.md) currently says hard skipped/error outcomes do not land
  in `evaluations`.
- This pipeline plan wants processor-owned skipped rows for newly handled
  ineligible inputs.
- [JSON-PAYLOAD.md](JSON-PAYLOAD.md) already treats `dossier_snapshot` as the
  exact model-visible evidence shown to evaluation.

[lock] [x] **Checkpoint 1B: Update existing normative docs after `PIPELINE.md`**

Update only after `PIPELINE.md` exists.

Likely doc updates:

- [SCHEMA.md](SCHEMA.md)
  - Add processor-owned tabs or explain why a tab is intentionally omitted.
  - Define common row fields and per-tab fields.
  - Reconcile skipped-row semantics.
  - Add upstream source refs to `evaluations` if evaluation reads from
    `dossiers`.
- [JSON-PAYLOAD.md](JSON-PAYLOAD.md)
  - Confirm the persisted evaluation payload embeds or links to the exact
    `dossier_snapshot` row/artifact.
  - Clarify whether the dossier snapshot artifact exists before evaluation.
- [TEXTIFY.md](TEXTIFY.md)
  - Clarify how a skipped textify row sets `output_source`.
  - Clarify how converted suggested files become processor outputs.
- [TRANSLATE.md](TRANSLATE.md)
  - Clarify how skipped-English translation rows set `output_source`.
  - Clarify how translated rows expose the English `output_source` consumed by
    dossier assembly.
- [CLI.md](CLI.md)
  - Reserve `curio pipeline` commands.
- [README.md](README.md)
  - Add `PIPELINE.md` to the spec index after it exists.

[lock] [x] **Checkpoint 1C: Review boundary**

- Initial implementation scope accepted for `textify` and `translate` only.
- Open questions for `dossier`, `evaluate`, Google adapters, and live pipeline
  smoke tests remain deferred.
- [test] `make check` passed before moving into implementation.

## Processor Contract Target

The exact code belongs in `PIPELINE.md` and implementation, but the protocol
shape should be close to this abstract base class:

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

Name the candidate-selection method `next_candidate()` rather than `next()` so
it does not look like Python iterator protocol sugar. Name the eligibility
method `eligibility()` because it returns an `Eligibility` value.

`status` maps to visible sheet `Status`. `object_` maps to visible sheet
`Object`; it is blank when `object_ is None`. `output_source` is the source ref
emitted for downstream processors and is intentionally not called `Source`,
because visible row `Source` means "the row/ref this processor consumed."
`metadata` is JSON-only detail and should not become a visible sheet column.

The outcome types should use this naming:

```python
@dataclass(frozen=True, slots=True)
class ProcessorObject:
    payload: Mapping[str, Any]
    mime_type: str = "application/json"


@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    status: str
    object_: ProcessorObject | None
    output_source: ProcessRef | None
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class PersistedOutcome:
    status: str
    object_: ArtifactRef | None
    output_source: ProcessRef | None
    metadata: Mapping[str, Any]
```

The protocol should not assume Google Sheets directly. Sheets should be one
implementation of a ledger/store boundary.

The current implementation scope includes only `textify` and `translate`
stages/status enums. Add `dossier` and `evaluate` enums and processor classes in
later checkpoints only after those capabilities have concrete service
boundaries.

## Store Protocol Target

`PIPELINE.md` should decide the storage abstraction before implementation.

Recommended concepts:

- `PipelineStore`
  - read upstream candidates
  - find existing records for idempotency
  - append processor rows
  - resolve row refs
- `ArtifactStore`
  - persist processor output JSON
  - persist text artifacts when needed
  - return stable artifact refs, URLs, paths, hashes, and sizes
- `ProcessRef`
  - stage or tab name
  - row number or row id
  - `Source`
  - Google row URL when backed by Sheets
  - optional artifact URL/path/hash
- `ProcessCandidate`
  - source ref
  - root `iMsgX` ref
  - source identity
  - typed metadata needed by the processor
- `ProcessorObject`
  - JSON-ready payload
  - MIME type, defaulting to `application/json`
- `ProcessOutcome`
  - `status`
  - `object_`
  - `output_source`
  - `metadata`
- `PersistedOutcome`
  - `status`
  - persisted `object_` artifact ref
  - `output_source`
  - `metadata`
- `ProcessRecord`
  - compact row written by a processor
  - immediate source ref and root `iMsgX` ref
  - full output is linked, not expanded into Sheets

## Lean Row Semantics

Preparation tabs should be lean operator ledgers. Detailed lineage,
processor/model/cost metadata, warnings, and contributing row refs belong in the
created JSON object.

Recommended visible columns:

- `textifications`: `Date`, `X Date`, `iMsgX`, `Type`, `Source`, `Status`, `Object`
- `translations`: `Date`, `X Date`, `iMsgX`, `Type`, `Source`, `Status`, `Object`
- `dossiers`: `Date`, `X Date`, `iMsgX`, `Status`, `Object`

Use specific status values and no `Reason` column:

- `textifications`: `converted`, `already_text`, `unsupported`, `no_text`, `failed`
- `translations`: `translated`, `already_english`, `failed`
- `dossiers`: `assembled`, `no_evidence`, `failed`

`Object` is populated only when the processor creates a JSON object in the
processor's matching Google Drive folder.

Failed rows should be allowed in processor tabs, but must be compact and must
not contain stack traces, secrets, raw model prompts, or large payloads. Full
debug artifacts can be local-only or explicitly retained under a separate
debug-retention policy.

## Output Source References

Skipped processors still need to expose the correct input for the next step
through `output_source`.

Recommended rule:

- A skipped textify row sets `output_source` to the original downloads
  text/evidence ref.
- A skipped translation row sets `output_source` to the original English
  text ref.
- A completed translation row sets `output_source` to the translated English
  artifact.
- Dossier assembly consumes the best `output_source`, not the processor's raw input
  by accident.

This avoids special-case branching in later processors.

## Synchronous V1 Scheduler

V1 should be synchronous:

- one process
- one processor running at a time
- no leases
- no concurrent row claims
- no background workers
- no parallel LLM calls

`PIPELINE.md` still needs to choose the scheduling style.

Recommended default: artifact-through mode.

```text
choose next downloads row needing evaluation
run textify for that source
run translate for the selected text output
run dossier assembly
run evaluate
stop or continue to next source
```

Also useful: single-stage commands for repair and backfill.

```text
curio pipeline run --limit 10
curio pipeline run-stage textify --limit 10
curio pipeline doctor --source <Source>
```

## V2 Notes

Do not implement these in v1, but preserve design space:

- bounded worker pools
- per-stage rate limits
- per-provider LLM concurrency limits
- leases or claim rows
- stale lease recovery
- partial reprocessing by processor version
- explicit retry queues
- backpressure when a downstream stage is failing
- alternative ledgers beyond Google Sheets

## Implementation Checkpoints

Implementation scope until explicitly widened:

- Build only `textify` and `translate` pipeline infrastructure.
- Keep `download` as upstream input, not a Curio processor.
- Do not implement `dossier`, `evaluate`, `catalog`, Google Drive artifact
  adapters, or live pipeline smoke tests during this pass.
- Implement the real pipeline store against configured Google Sheets. Do not
  make real CLI commands silently substitute local files or fake stores.
- Keep this file named `PIPELINE-TODO.md` and tracked by git. Do not move it
  back to a `TODO-*.md` name ignored by the repository.
- When a checkpoint still names out-of-scope future work, the skipped sub-step
  is struck out and marked `(PUNTED)`, then copied to the PUNTED section below.
- Do not mark runnable CLI checkpoints complete while `curio pipeline` commands
  still return the reserved-command stub.

Current implementation state:

- Pure contracts, fake stores, processor wrappers, scheduler helpers, and local
  artifact persistence exist for `textify` and `translate`.
- The `curio pipeline` command group is reserved and exposes the intended
  operator controls, but it does not execute processors yet.
- Candidate selection from configured Google Sheets `iMsgX` / `downloads` data
  is not implemented.
- Non-persisting preview output is specified but not implemented.
- CLI-level integration tests are still missing meaningful execution coverage.

[lock] [x] **Checkpoint 2: Pure pipeline contracts**

- Add `curio.pipeline` package.
- Add frozen slotted dataclasses for:
  - `ProcessRef`
  - `ArtifactRef`
  - `ProcessCandidate`
  - `Eligibility`
  - `ProcessorObject`
  - `ProcessOutcome`
  - `PersistedOutcome`
  - `ProcessRecord`
- Add processor/store/artifact-store protocols.
- Add common status enums.
- Add JSON schemas only if records are persisted as JSON artifacts.
- Keep Google Sheets out of pure models.
- Limit initial stage/status constants to `textify` and `translate`.
- ~~Add `dossier` / `evaluate` stage or status enums.~~ (PUNTED)
- [test] Add model, serialization, and invariant tests.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [x] **Checkpoint 3: In-memory store and scheduler**

- Add an in-memory `PipelineStore` for tests.
- Add an in-memory or temp-dir `ArtifactStore` for tests.
- Implement synchronous scheduling for `textify -> translate` without Google APIs.
- Prove:
  - completed records are not duplicated on rerun
  - skipped rows are appended for newly handled ineligible inputs
  - skipped rows preserve `output_source` for downstream processors
  - failed rows do not block unrelated sources
  - artifact-through mode stops cleanly on no work
  - the scheduler stops after `translate` in the current scope
- ~~Implement dossier/evaluate scheduler stages.~~ (PUNTED)
- [test] Gate: `make check`, 100% coverage passed.

[lock] [x] **Checkpoint 4: Processor adapters for existing workflows**

- Add `TextifyProcessor` around `TextifyService`.
- Add `TranslateProcessor` around `TranslationService`.
- ~~Add `DossierProcessor` as deterministic assembly.~~ (PUNTED)
- ~~Add or specify `EvaluateProcessor`.~~ (PUNTED)
  - ~~If an evaluation service exists by then, wrap it.~~ (PUNTED)
  - ~~If it does not exist, implement or defer evaluation service explicitly
    rather than hiding evaluation logic inside the scheduler.~~ (PUNTED)
- Keep each processor small:
  - selection and references in processor/store code
  - model calls in existing service boundaries
  - artifact writing in artifact-store code
  - row rendering in processor record code
- [test] Use fake services and fake stores first.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [x] **Checkpoint 5A: Local artifact adapter**

- Add local filesystem artifact adapter behind `ArtifactStore`.
- Resolve artifact roots from `PipelineConfig`.
- Write textify artifacts under `textifications/`.
- Write translate artifacts under `translations/`.
- Derive deterministic iMsgX-style filenames from upstream source artifact
  stems.
- Preserve processor version, content hash, source refs, and iMsgX lineage in
  the JSON envelope.
- Reject changed-content overwrites at the same deterministic artifact path.
- ~~Add Google Drive artifact adapter behind `ArtifactStore`.~~ (PUNTED)
- [test] Gate: `make check`, 100% coverage passed.

[lock] [ ] **Checkpoint 5B: Google Sheets pipeline store**

- Add a real Google Sheets-backed store behind `PipelineStore`.
- Extend required pipeline config with the spreadsheet/workbook identity and
  tab names needed to read `iMsgX`, read `downloads`, and append Curio-owned
  processor rows.
- Read the upstream `iMsgX` and `downloads` tabs needed to construct
  `ProcessCandidate` objects.
- Do not mutate `iMsgX` or `downloads`.
- Select `textify` candidates from `downloads` rows in deterministic row order.
- Select `translate` candidates from text or textification outputs in root
  `downloads` order.
- Implement idempotency checks against existing `textifications` and
  `translations` rows.
- Support appending only to Curio-owned `textifications` and `translations`
  tabs; row placement is always first available row.
- Support selectors over upstream input rows and source identity:
  - `--row`
  - `--from-row`
  - `--to-row`
  - `--source`
  - `--start`
  - `--end`
- Treat row selectors only as upstream input filters. They must never select
  output row positions.
- Unit tests must not touch live Google Sheets. Use fake Google Sheets
  transports/clients for non-integration tests.
- Real CLI commands must use the configured Google Sheets store and must fail
  clearly when config/auth/sheet access is missing.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [x] **Checkpoint 6A: Reserved CLI surface**

- Add `curio pipeline` command group.
- Add reserved commands:
  - `curio pipeline run`
  - `curio pipeline run-stage`
  - `curio pipeline doctor`
- Remove confusing source-runner spellings:
  - no `curio pipeline run-source`
  - no `curio pipeline run --source`
- Limit visible stages to `textify` and `translate`.
- Append-capable commands include only:
  - `--limit`
  - `--persist`, which is required before rows or artifacts may be written
- Inspection-only commands may include:
  - `--json`
  - `--config`
  - `--source` for `run-stage` and `doctor`, not full `run`
  - `--start`
  - `--end`
  - `--row`
  - `--from-row`
  - `--to-row`
- Pipeline Makefile help/run targets are implemented for the reserved command
  surface.
- `USAGE.md` includes standalone `textify`/`translate` examples and the
  reserved pipeline command examples for limit-based appends, required
  `--persist`, and inspection-only date, row, and source controls.
- Row controls are inspection-only input filters over upstream iMsgX `downloads`
  rows. Processor-owned tabs remain append-only and write to the first
  available row.
- Commands still fail clearly as reserved; they do not run processors yet.
- ~~CLI should run dossier/evaluate stages.~~ (PUNTED)
- [test] Gate for reserved command group: `make check`, 100% coverage passed.

[lock] [ ] **Checkpoint 6B: Preview planner and renderer**

- Implement non-persisting preview mode for targeted selectors.
- Preview commands must not:
  - append rows
  - write artifacts
  - call LLM providers
  - mutate Google Sheets or Drive
- Render compact human output with:
  - stage
  - upstream downloads row
  - source
  - immediate input ref
  - planned processor action
  - reason
- Render JSON output only for non-mutating previews and diagnostics.
- Reject `--persist` when any targeted row/date/source selector is present.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [ ] **Checkpoint 6C: Executable `run-stage`**

- Implement `curio pipeline run-stage textify --persist`.
- Implement `curio pipeline run-stage translate --persist`.
- Parse config and construct:
  - Google Sheets pipeline store
  - local artifact store
  - selected processor
  - existing service boundary and configured LLM caller
- Use `--limit`, defaulting to `10`, to append only the next available stage
  candidates.
- Require `--persist` for next-available append sweeps.
- Append processor rows to the first available row in the processor-owned tab.
- Never use CLI row options as output row positions.
- Stop at the requested limit or first unrecoverable runtime failure.
- Real commands must not use fake stores, fake services, or offline fixture
  substitutes. Fakes belong only in tests.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [ ] **Checkpoint 6D: Executable full `run`**

- Implement `curio pipeline run --persist` as the full current-scope pipeline.
- `run` means artifact-through execution for all in-scope processors:
  `downloads -> textify -> translate`.
- `run` must not accept `--source`; source-targeted work belongs under
  `run-stage` preview/diagnostics.
- Use `--limit`, defaulting to `10`, to process the next available root
  downloads items through in-scope processors.
- Do not add dossier/evaluate execution in this checkpoint.
- ~~CLI should run dossier/evaluate stages.~~ (PUNTED)
- [test] Gate: `make check`, 100% coverage passed.

[lock] [x] **Checkpoint 7A: Offline scheduler integration**

- Build offline fixtures representing scheduler/service behavior for:
  - already-text downloads row
  - image needing textify
  - non-English text needing translation
  - English text skipping translation
  - unsupported media skipping textify
  - ~~unsupported media skipping evaluation~~ (PUNTED)
  - failed provider call
- Reused checked-in real-world `textify` smoke fixtures for the image, text,
  unsupported archive, and failed-provider fixture inputs.
- Run the in-scope pipeline through fake stores and fake LLM/service clients.
- Verified expected in-memory rows and artifact refs.
- Verified translate consumes textify `output_source`, not stale upstream text.
- ~~Verify evaluation consumes the dossier snapshot, not stale intermediate text.~~
  (PUNTED)
- Verified no live Google Sheets or Drive adapters are touched by the default
  integration test.
- This does not yet prove the real CLI can run the pipeline.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [ ] **Checkpoint 7B: CLI integration coverage**

- Add CLI-level tests for the executable pipeline commands.
- Invoke `curio pipeline run-stage textify` and `curio pipeline run-stage
  translate` through the CLI runner.
- Invoke `curio pipeline run` through the CLI runner once full current-scope
  execution exists.
- Non-integration tests must not touch live Google Sheets, Google Drive, or live
  providers. Use fake transports/clients at the boundary.
- Real integration/smoke/e2e tests may touch Google Sheets only when explicitly
  opted in.
- Verify persisted local artifact files and appended processor rows through the
  configured store boundary.
- Verify previews print meaningful plans and persist nothing.
- Verify `--persist` gates all mutating sweeps.
- Verify no live Google Sheets or Drive adapters are touched by default tests.
- [test] Gate: `make check`, 100% coverage passed.

[lock] [ ] **Checkpoint 8: Live smoke planning**

- ~~Add opt-in live pipeline smoke harness only after offline integration is
  solid.~~ (PUNTED)
- ~~Live pipeline smoke tests must be skipped by default.~~ (PUNTED)
- ~~Retained outputs should follow the existing textify/translate smoke-report
  pattern.~~ (PUNTED)
- ~~[live] Do not run live pipeline smoke tests without explicit opt-in.~~
  (PUNTED)

## PUNTED

These items remain part of the longer Curio pipeline plan but are explicitly out
of scope while this implementation pass is limited to `textify` and `translate`.

- Add `dossier` / `evaluate` stage or status enums.
- Implement dossier/evaluate scheduler stages.
- Add `DossierProcessor` as deterministic assembly.
- Add or specify `EvaluateProcessor`.
- Wrap an evaluation service if one exists.
- Implement or defer evaluation service explicitly if one does not exist.
- Add Google Drive artifact adapter behind `ArtifactStore`.
- Support unsupported media skipping evaluation.
- Verify evaluation consumes the dossier snapshot, not stale intermediate text.
- Add opt-in live pipeline smoke harness.
- Require live pipeline smoke tests to be skipped by default.
- Retain live pipeline smoke outputs using the existing smoke-report pattern.
- Keep live pipeline smoke tests behind explicit opt-in.
- Run dossier/evaluate from the pipeline CLI.

## Working Decisions Replacing Open Questions For Zeph

Zeph is unavailable during this implementation pass. These decisions are
accepted working defaults so implementation can proceed without blocking. They
can be revised later before punted stages are implemented.

1. Should v1 definitely add a `dossiers` tab?

   Working decision: yes later, but PUNTED for this pass. It remains the audit
   boundary between preparation and evaluation once dossier/evaluate work starts.

2. Should v1 run artifact-through by default or stage-by-stage?

   Working decision: artifact-through by default for the current scope:
   `downloads -> textify -> translate`. Also keep single-stage commands for
   repair/backfill.

3. Should duplicate reruns append skipped rows?

   Working decision: no. Append skipped rows for newly handled ineligible
   inputs; no-op when a processor record already proves the input was handled.

4. Should failed attempts be appended to processor tabs?

   Working decision: yes, compactly. Otherwise failed work disappears and reruns
   become harder to reason about.

5. What is the v1 artifact store for intermediate textify/translate/dossier
   outputs?

   Working decision: support local filesystem first behind `ArtifactStore` for
   `textify` and `translate`. Dossier artifacts and Google Drive are PUNTED.

6. What is the stable identity for idempotency?

   Working decision: use `Source` plus upstream downloads row metadata and input
   artifact hash when available. Row number alone is useful for diagnostics but
   must not be the only identity.

7. Should the processor selection and eligibility methods use noun-returning
   names?

   Decision: yes. Use `next_candidate()` for selection and `eligibility()` for
   the method that returns an `Eligibility`.

8. Should evaluation be implemented as a standalone service before the pipeline?

   Working decision: yes later, but PUNTED. The scheduler must not become the
   place where evaluation prompt/model/validation logic lives.

9. Should processor rows include per-call cost and usage summaries?

   Decision: no visible preparation-tab columns. LLM-backed processors should
   put processor/model/cost details in the created JSON object or debug
   metadata, not in `textifications`, `translations`, or `dossiers` rows.

10. Should `catalog` derive from `evaluations` only or from the whole pipeline?

    Working decision: keep `catalog` evaluation-centered later, but PUNTED for
    this pass. Intermediate tabs are operational ledgers; `catalog` is the
    human-facing accepted result.
