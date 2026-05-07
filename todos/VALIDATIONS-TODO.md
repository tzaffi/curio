# TODO Validations

## Preamble

Observed failure:

```bash
make textify-genius \
  DOWNLOADS="/Users/zeph/github/tzaffi/curio" \
  ARTIFACT="/Users/zeph/github/tzaffi/curio/tests/fixtures/textify_smoke/real/r-img-ascii-diagram-01.png" \
  OPTS="--stats"
```

Result:

```text
markdown output must not be wrapped in a single code fence
make: *** [textify-genius] Error 1
```

Initial read: this validation was probably too strict. The model returned recoverable Markdown formatting, and Curio could have unwrapped the single outer code fence, preserved the content, and emitted a warning instead of failing the run.

## STATUS

Legend: `[x]` done, `[ ]` pending.

- [x] Step 1: Investigate validation strictness
  - [x] Textify validation inventory completed.
  - [x] Translate validation inventory completed.
  - [x] Validation failures classified by fatality and repairability.
  - [x] Warning/repair preference evaluated.
  - [x] Safety boundaries preserved for request IDs, source identity, unsafe paths, missing user-visible content, and unmappable outputs.
- [x] Step 2: Implement validation fixes
  - [x] Added deterministic textify repair for a single outer Markdown code fence on non-code Markdown outputs.
  - [x] Added a source warning when that repair is applied.
  - [x] Clarified the textify prompt contract to avoid whole-output Markdown fences.
  - [x] Evaluated a shared validation-result abstraction; kept repair local because only one narrow validator path needed it.
  - [x] Added focused textify validation/service tests for repair, warning emission, and unsafe-path fatal behavior.
  - [x] Evaluated translate downgrade cases; none were safe enough to relax without risking block mapping or translation semantics.
  - [x] Confirmed existing CLI tests cover warning output without requiring `--stats`.
  - [x] Run `make check` (`UV=/Users/zeph/.local/bin/uv make check`).

Validation policy outcome:

- Fatal: request ID mismatches, non-succeeded/missing LLM output, schema shape failures, source name mismatches, unsafe suggested paths, inconsistent converted/non-converted file payloads, empty repaired content, translate duplicate/missing/extra/reordered block IDs, block-name mismatches, English-confidence/`translation_required` contradictions, and translated-text nullability errors.
- Recoverable with warning: textify Markdown output for non-code artifacts wrapped in one outer fenced block.
- Safe as-is with warning: provider/runtime warnings and model warnings that already satisfy schema and do not affect response mapping.
- Ambiguous: broader schema repair and translate semantic downgrades. These remain hard failures until the prompt/schema contract defines a deterministic repair.

## 1. Investigate Validation Strictness

Audit response validation in both workflows:

- `textify`: inventory failures from model-output schema validation, source identity checks, status/suggested-file consistency, suggested path validation, output format checks, code-fence checks, warning shape checks, language/page-count checks, and response model construction.
- `translate`: inventory failures from model-output schema validation, request ID checks, block ID duplication/missing/extra/order checks, block name checks, English confidence classification, `translation_required` consistency, translated-text nullability, warning shape checks, and response model construction.
- For each validation failure, classify it as:
  - fatal and unrecoverable
  - recoverable by deterministic repair plus warning
  - safe to accept as-is with warning
  - ambiguous and requiring a clearer prompt/schema contract
- Specifically evaluate whether response validation should generally prefer warnings/repairs over hard failures, with hard failures reserved for cases where Curio cannot safely build a coherent response.
- Preserve safety boundaries: do not silently accept wrong request IDs, unsafe suggested paths, missing required user-visible content, or outputs that cannot be mapped back to the request.

## 2. Implement Validation Fixes

After the investigation, implement the chosen validation policy.

Candidate fixes to consider:

- Add deterministic repair for a single outer Markdown code fence in `textify` non-code outputs, with a warning recorded on the source or response.
- Clarify textify prompts so Markdown output is not wrapped in one code fence unless the source is code, logs, or terminal output.
- Add a shared validation-result pattern if multiple validators need to return repaired values plus warnings instead of only raising exceptions.
- Update `textify` tests for repaired code-fence output, warning emission, and still-fatal unsafe outputs.
- Add analogous `translate` tests for any downgraded or repaired validation cases.
- Confirm CLI warning output remains visible without requiring `--stats`.
- Run `make check` after implementation.
