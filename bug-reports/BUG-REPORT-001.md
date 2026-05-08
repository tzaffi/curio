# BUG-REPORT-001: `p-t-n-t` Retries the Same Failed Textify Row

Status: Fixed in local workspace
Reported: 2026-05-07
Observed command: `make p-t-n-t LIMIT=500`

## Summary

`make p-t-n-t LIMIT=500` repeatedly selected the same textify candidate after a failure and appended duplicate `failed` rows to the Google Sheet. The observed stuck candidate was downloads row `1107`, a `Link` in column `X3`:

```text
https://www.skool.com/ai-profit-lab-7462/about
```

The repeated failure was:

```text
ValueError: textify candidate metadata requires path or source_ref.artifact_path
(downloads_dir=/Users/zeph/Desktop/iMsgX/downloads,
 expected_artifact_prefix=imsgx-r0574-x3-link-,
 downloads_row=1107,
 column=X3,
 type=Link,
 object=https://www.skool.com/ai-profit-lab-7462/about)
```

This violates the pipeline decision that an automated sweep should record a failure and move to the next candidate, not retry the same failed input and bloat the processor sheet.

## Impact

- A single bad downloads row can consume the remaining `LIMIT` budget.
- The `textifications` sheet gets duplicate `failed` rows for the same downloads row.
- Later candidates are starved until the command is interrupted or reaches `LIMIT`.
- The following translate stage in `p-t-n-t` is delayed and may run against a polluted processor ledger.

## Expected Behavior

For automated `--persist` sweeps:

- `failed` is a terminal processor row for candidate selection.
- The next iteration should skip the failed downloads input and continue scanning later candidates.
- Explicit retries should require a targeted/manual retry path, not happen in the default sweep.

## What Happened

`p-t-n-t` runs:

- `curio pipeline run-stage textify ... --persist`
- then `curio pipeline run-stage translate ... --persist`

The textify stage loop treats both `recorded` and `failed` as progress, so it continues after a failure. That part is intentional for "record failure and keep going" behavior.

The candidate should have become ineligible after the first failed row was staged, because `GoogleSheetsPipelineStore._next_textify_candidate()` skips downloads rows that have any matching textification row. A match requires both:

- the textification row `Source` to match the downloads row ref
- the textification row `iMsgX` to match the downloads row `iMsgX` ref

The pasted sheet data suggests the failed rows did not actually match the candidate they were meant to mark handled:

- The failure metadata says the selected candidate expected prefix `imsgx-r0574-x3-link-`, meaning the selected downloads row's iMsgX row was `574`.
- The pasted `textifications` rows for the failure point at iMsgX row `547` while the `Source` points at downloads row `1107`.

That mixed identity is enough to explain the loop: the stage appended a row with `Source=downloads!1107` but the wrong `iMsgX`, so candidate matching did not see row `1107` as handled and returned it again.

## Primary Root Cause

`GoogleSheetsPipelineStore._record_values()` reconstructs Date, X Date, iMsgX, and Type for textification rows by calling `_download_for_ref(record.source_ref)`.

`_download_for_ref()` currently accepts either the non-unique visible source URL or the exact downloads row URL:

```python
if _visible_source_matches_ref(row.source, ref) or _visible_source_matches_ref(self._row_url(...), ref):
    return row
```

Because downloads can contain the same external URL more than once, an earlier row with the same `row.source` can be returned before the exact downloads row is reached. The record then writes metadata from the wrong downloads row while preserving the current candidate's `Source` row URL.

That creates a processor row that looks like:

```text
iMsgX=<some older duplicate row>
Source=<current downloads row>
Status=failed
```

`_matching_processor_row()` later requires both fields to match, so this malformed row does not suppress the current candidate. The scheduler sees `failed` as progress and tries again.

Relevant pre-fix code path:

- `Makefile`: `p-t-n-t` runs textify stage before translate stage.
- `src/curio/pipeline/scheduler.py`: `failed` is a progressing run status, and `run_stage()` continues while statuses are progressing.
- `src/curio/pipeline/processors.py`: textify raises when no local path exists.
- `src/curio/pipeline/google_sheets.py`: textify candidate selection skips only when a matching processor row exists.
- `src/curio/pipeline/google_sheets.py`: matching requires both `Source` and `iMsgX`.
- `src/curio/pipeline/google_sheets.py`: downloads lookup selected an earlier duplicate by source URL before the fix.

## Immediate Failure Cause for Row 1107

The row itself failed because it was a `Link` candidate with no local artifact path:

- `Object` was the Skool URL, not an absolute local file path.
- No matching local file was found under `/Users/zeph/Desktop/iMsgX/downloads`.
- The expected local prefix was `imsgx-r0574-x3-link-`.
- `TextifySource` requires an absolute local path, so `_textify_request_from_candidate()` raised before calling the textify service.

This should still be recorded once and skipped. The missing artifact explains the first failure; it does not justify repeated retries.

## Recommended Fixes

1. Fix `_download_for_ref()` to prefer exact row identity before source URL matching.

   Use `ref.row_number`/`ref.row_url` for downloads refs first. Only fall back to `row.source` matching when the ref has no row identity. This prevents duplicate external URLs from corrupting the recorded `iMsgX`.

2. Add a regression test for duplicate source URLs.

   Construct two downloads rows with the same `Source` URL but different iMsgX refs. Mark the first as already handled, then make the second fail for missing artifact. Assert:

   - the staged failed row uses the second row's iMsgX
   - the next textify candidate is not the second row again
   - `run_stage(..., limit=2)` returns `failed` then `no_candidate` or moves to a later unrelated row, not `failed` then `failed` for the same row

3. Add a scheduler-level repeated-candidate guard.

   Even with the store fixed, `run_stage()` should not allow the same candidate identity to be processed repeatedly in one sweep. If the same `(stage, source_ref, iMsgX)` appears twice in one `run_stage()` call, abort before appending another processor row and report an invariant violation.

4. Make missing-artifact `Link` behavior deterministic.

   Decide whether `Link` rows without local artifacts should be:

   - `already_text`, using the URL as the text payload so translate can URL-only skip it, or
   - `unsupported`, with a clear warning such as `link has no downloaded artifact for textify`

   Either option is better than a generic `ValueError` in normal batch operation. If Skool pages are expected to be textified as web pages, the download stage must create an HTML/text artifact before textify sees the row.

5. Align failed-row semantics in tests and store APIs.

   Current store behavior intentionally ignores `failed` in `existing_record()`, but candidate selection is supposed to skip any processor row, including `failed`. Keep that distinction only if it is deliberate and covered by explicit tests. Otherwise, make terminal candidate selection semantics consistent across stores.

## Suggested Test Names

- `test_google_sheets_store_records_failed_duplicate_source_with_exact_imsgx`
- `test_google_sheets_run_stage_does_not_retry_failed_duplicate_source_candidate`
- `test_textify_link_without_artifact_records_deterministic_non_retry_status`
- `test_run_stage_aborts_on_repeated_candidate_identity`

## Implemented Fixes

- Downloads and processor row lookups now prefer exact row identity before falling back to visible source matching.
- `failed` rows are treated as terminal existing records for store lookup.
- `run_stage()` and `run_artifact_through()` now abort before processing the same candidate identity twice in one run.
- Missing-artifact `Link` inputs now record deterministic `already_text` with the URL as downstream text source.
- Regression coverage was added for duplicate source URLs, failed-row terminal semantics, missing-link behavior, and repeated-candidate guarding.

## Open Questions

- Should failed rows be retryable through an explicit selector, for example `--row 1107 --retry-failed`, rather than default `--persist` sweeps?
- Are the pasted iMsgX row `547` failed rows from the same run as the `imsgx-r0574` error, or are they an older duplicate-source run? The code path above explains either case, but the exact affected duplicate row should be confirmed in the live sheet.
