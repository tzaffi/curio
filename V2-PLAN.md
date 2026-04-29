# Curio V2 Plan

## Purpose

Collect future work that should not block the current `textify` and `translate`
pipeline implementation.

This document is the home for V2 design space that would otherwise be scattered
through [PIPELINE.md](PIPELINE.md) and [PIPELINE-TODO.md](PIPELINE-TODO.md).
V1 docs may reference this file, but should not keep duplicate long-form V2
plans.

## V2 Boundary

V2 work must not be started until the V1 `textify` / `translate` pipeline can:

- read configured Google Sheets `iMsgX` and `downloads` tabs
- run non-mutating previews
- run `pipeline run-stage textify|translate --persist`
- run full current-scope `pipeline run --persist`
- pass CLI-level non-live integration coverage
- keep default `make check` free of live Google Sheets, Google Drive, and live
  provider calls

## Google API Consolidation

Curio and iMsgX should eventually share the same Google API plumbing, but Curio
should not import iMsgX internals directly as a shortcut.

iMsgX currently has useful, battle-tested patterns:

- direct Google REST calls rather than `gspread` or `googleapiclient`
- OAuth desktop-app authorization
- macOS Keychain storage for authorized-user credentials
- scope-aware credential reuse and refresh
- exact sheet header validation
- append-only Sheets writes with `valueInputOption=RAW`
- `read_sheet_gid` support for exact row URLs
- Drive file search/upload helpers with app properties

Those patterns should shape Curio's V1 Google store. Extraction should wait
until Curio has its own working Google-backed pipeline store and tests, so the
shared API is extracted from two real call sites rather than guessed from one.

### Extraction Candidates

Good shared candidates:

- `KeychainLocator`
- Google OAuth config shape:
  - OAuth desktop client JSON path
  - authorized-user Keychain service/account
- OAuth credential loading:
  - read stored credentials from Keychain
  - verify stored scopes cover requested scopes
  - refresh expired credentials
  - run local OAuth server when consent is needed
  - store refreshed/new credentials back to Keychain
- Google REST session construction
- Sheets helpers:
  - A1 range quoting
  - values read
  - values append
  - values update
  - spreadsheet metadata / sheet gid lookup
  - uniform HTTP error messages
- Drive helpers:
  - file search by name/app properties
  - multipart upload
  - stable `DriveFile` response model
  - uniform HTTP error messages

Do not extract:

- iMsgX X/Twitter resolution logic
- iMsgX download candidate logic
- iMsgX row schemas
- Curio processor, scheduler, or ledger semantics
- Curio textify/translate/dossier/evaluation models

### Refactor Steps

1. Finish Curio's V1 Google Sheets-backed `PipelineStore` locally.

   It should intentionally mirror iMsgX operational semantics: direct REST,
   OAuth desktop auth, Keychain-backed token reuse, exact header validation,
   append-only rows, and `RAW` value writes.

2. Add Curio Google config.

   Curio should have an explicit Google auth block, probably parallel to iMsgX:

   ```json
   {
     "google": {
       "oauth_client_credentials_path": "/absolute/path/to/google-oauth-client.json",
       "authorized_user_keychain": {
         "service": "curio-google-authorized-user",
         "account": "YOUR_MACOS_USERNAME"
       }
     }
   }
   ```

   Pipeline config should continue to hold pipeline-specific sheet IDs and tab
   names.

3. Align tests in both projects.

   Before extraction, both iMsgX and Curio should have fake-transport tests for:

   - scope mismatch triggering OAuth
   - expired credentials refreshing
   - stored credentials being reused
   - access-denied and timeout guidance
   - Sheets read/append/update URL construction
   - `RAW` append semantics
   - sheet gid lookup
   - Drive search/upload helpers if Drive is included in the extraction

4. Extract a small shared package or shared module.

   The dependency direction should be:

   ```text
   iMsgX -> shared-google
   Curio -> shared-google
   ```

   Avoid `Curio -> iMsgX` and avoid `iMsgX -> Curio`.

5. Migrate iMsgX and Curio one at a time.

   Keep behavior unchanged. The migration should be mostly import-path and
   config-adapter work, not semantic changes.

6. Add opt-in live Google smoke tests.

   Live tests must remain outside default `make check`. They should require
   explicit environment variables and should target isolated tabs or an isolated
   workbook unless the command is intentionally exercising production data.

## Google Drive Artifact Adapter

Curio V1 may use a local artifact store while processor rows are written to
Google Sheets. A later pass can add a Google Drive-backed `ArtifactStore`.

The Drive adapter should reuse the shared Google auth/session layer once it
exists. It should preserve Curio's deterministic artifact naming and lineage
envelope rules:

- processor version in JSON envelope
- source refs in JSON envelope
- iMsgX lineage in JSON envelope
- content hash metadata
- safe idempotent reuse when the deterministic object already exists with the
  same content
- failure before row append when artifact persistence fails

## Pipeline Runtime V2

V1 is synchronous and single-process. V2 may add concurrency, leases, and more
operator controls only after V1 append/idempotency behavior is reliable.

Potential V2 runtime features:

- bounded worker pools
- per-stage concurrency controls
- per-provider LLM rate limits
- per-provider LLM concurrency limits
- claim rows or leases
- stale lease recovery
- explicit retry queues
- retry by processor version
- retry one source
- retry one stage
- backpressure when a downstream stage is failing
- partial reprocessing by processor version
- stronger local diagnostics for append/persist split failures
- alternative ledgers beyond Google Sheets

These features should not change the core processor contract unless there is a
specific failure in the V1 abstraction. Prefer adding scheduler/store adapters
around the existing processor contract before changing processor methods.

## Storage Backends

Google Sheets remains the online operational store for V1. V2 may explore
stronger storage backends if Curio needs stricter relational behavior,
transactions, or queryability.

Options to evaluate later:

- SQLite as a local mirror/cache with Google Sheets sync
- SQLite or Postgres as the primary operational ledger
- Google Sheets as a derived/operator view
- append-only event log plus materialized views

Do not introduce a second primary store until the failure modes are concrete.

## Testing Rules

V2 testing must preserve the V1 safety boundary:

- default `make check` must not require network
- default `make check` must not require Google auth
- default `make check` must not mutate live Google Sheets or Drive
- fake transports should cover all normal Google API request construction
- live Google tests must be explicit opt-in
- production commands must not silently use fake stores or local fixture stores

