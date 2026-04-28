# Upshot: Textify Caller Choice

Use `textifier_codex_gpt_54_mini` as the default textify caller.

```json
{
  "textify": {
    "llm_caller": "textifier_codex_gpt_54_mini"
  }
}
```

## The Call

| Role | Caller | Model | Result In This Run |
| --- | --- | --- | --- |
| Default | `textifier_codex_gpt_54_mini` | `gpt-5.4-mini` | 15 preferred outputs, $1.1986 total API-equivalent cost |
| Escalation | `textifier_codex_gpt_55` | `gpt-5.5` | best large-PDF extraction, $7.5767 total API-equivalent cost |
| Do not default | `textifier_codex_gpt_53_codex` | `gpt-5.3-codex` | strong on some images, but failed the large PDF with `no_text_found` |

The practical result is that `textifier_codex_gpt_54_mini` was preferred most
often and cost 60% of `textifier_codex_gpt_53_codex` and 16% of
`textifier_codex_gpt_55` on the same 24-case matrix.

Cost totals from the retained run:

| Caller | Evaluator Records | Matrix Cost | Relative To Mini |
| --- | ---: | ---: | ---: |
| `textifier_codex_gpt_54_mini` | 24 | $1.1986 | 1.0x |
| `textifier_codex_gpt_53_codex` | 24 | $1.9887 | 1.7x |
| `textifier_codex_gpt_55` | 24 | $7.5767 | 6.3x |

Those costs are API-equivalent estimates computed from retained Codex CLI token
usage and the price table in the live smoke harness.

## Operating Rule

Start with `textifier_codex_gpt_54_mini`.

Escalate to `textifier_codex_gpt_55` when:

- the artifact is a long, high-value PDF
- missing later sections, tables, figure captions, or references would be costly
- operator review can justify a much higher extraction cost

Do not use `textifier_codex_gpt_53_codex` as the default textifier from this
evidence. It performed well on several image OCR cases, especially the Spanish
social post and dense local-LLM table, but the large-PDF `no_text_found` result
is too severe for default pipeline use.

## Known Risks

- Exact symbol preservation still needs work, especially `/`, case, shell flags,
  and code-like text.
- Terminal listings remain noisy across callers.
- `textifier_codex_gpt_54_mini` sometimes lowercases shell snippets.
- `textifier_codex_gpt_55` is better on the long PDF but too expensive for the
  default path.
- The evaluator observed duplicate unsupported-media warnings in this retained
  run; Curio now keeps that warning only on `response.source.warnings`.

## Evidence

- [Evaluator output](evaluator-output.md)
- [Evaluator input](evaluator-input.jsonl)
- [Evaluator payload](evaluator-payload.json)
- [Evaluator prompt](evaluator-prompt.md)
- [Live run manifest](manifest.json)

This is a smoke-test result, not a broad OCR benchmark. Re-run the matrix when
Codex model availability, pricing, prompt policy, or media preparation changes.
