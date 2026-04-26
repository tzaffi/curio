# Translation Smoke Report: 20260426-060103-22de460b22c0

- Source smoke run: `/Users/zeph/github/tzaffi/curio/tmp/translate-smoke/20260426-060103-22de460b22c0`
- Durable report directory: `/Users/zeph/github/tzaffi/curio/reports/translate-smoke/20260426-060103-22de460b22c0`
- Evaluator records: `30`

## Key Artifacts

- `evaluator-output.md`: evaluator scoring matrix and preference notes.
- `evaluator-prompt.md`: exact evaluator prompt template plus payload used for this run.
- `evaluator-payload.json`: normalized evaluator payload with source, translation, usage, and cost.
- `evaluator-input.jsonl`: compact row-oriented evaluator input.
- `translations.md`: human-readable source/translation/cost rollup by case and caller.
- `manifest.json`: smoke run metadata and redacted caller configuration.
- `cases/`: retained source text and expected intent per case.
- `runs/`: retained request, response, translated text, and usage artifacts per case/caller.
- `cli/`: retained CLI default/explicit caller smoke outputs.

## Re-run Commands

```bash
make translate-smoke-evaluate TRANSLATE_SMOKE_RUN=/Users/zeph/github/tzaffi/curio/tmp/translate-smoke/20260426-060103-22de460b22c0
make translate-smoke-report TRANSLATE_SMOKE_RUN=/Users/zeph/github/tzaffi/curio/tmp/translate-smoke/20260426-060103-22de460b22c0
```
