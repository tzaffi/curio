# Upshot: Translation Caller Choice

Use `translator_codex_gpt_54_mini` as the default translation caller.

```json
{
  "translate": {
    "llm_caller": "translator_codex_gpt_54_mini"
  }
}
```

## The Call

| Role | Caller | Model | Result In This Run |
| --- | --- | --- | --- |
| Default | `translator_codex_gpt_54_mini` | `gpt-5.4-mini` | 7/10 preferred outputs at $0.2015 for the 10-case matrix |
| Escalation | `translator_codex_gpt_54` | `gpt-5.4` | 3/10 preferred outputs at $0.6674 for the same matrix |
| Do not default | `translator_codex_gpt_55` | `gpt-5.5` | 0/10 preferred outputs at $1.3945 for the same matrix |

The practical result is simple: `translator_codex_gpt_54_mini` delivered 7 of the 10 preferred translations and 191/200 evaluator points while costing 30% of `translator_codex_gpt_54` and 14% of `translator_codex_gpt_55`.

At this run's usage profile, 100 comparable translations would cost approximately:

| Caller | 100-Item API-Equivalent Cost | Relative To Mini |
| --- | ---: | ---: |
| `translator_codex_gpt_54_mini` | $2.02 | 1.0x |
| `translator_codex_gpt_54` | $6.67 | 3.3x |
| `translator_codex_gpt_55` | $13.95 | 6.9x |

Those costs are API-equivalent estimates computed from retained token usage and the price table in the live smoke harness. The smoke run itself used Codex CLI auth.

## Why Not Always Mini?

The larger `gpt-5.4` caller did earn its keep on three cases:

- `Z-KO-01`: preserved technical tokens exactly, including `64gb` and `90tok/s`.
- `Z-AR-01`: preserved capitalization of English technical terms such as `Inference`, `Enterprise`, `Local Agents`, and `Cloud APIs`.
- `Z-HE-02`: handled graphic Hebrew invective more accurately and fluently.

So the operating policy should not be "mini for everything." It should be "mini by default, escalate when preservation risk is obvious."

## Operating Rule

Start with `translator_codex_gpt_54_mini`.

Escalate to `translator_codex_gpt_54` when:

- exact preservation of mixed technical tokens matters, especially casing and compact units such as `64gb` or `90tok/s`
- Arabic or RTL text contains English technical terms whose capitalization must survive intact
- Hebrew text is graphic, idiomatic, or likely to punish literal rendering
- the downstream workflow values source fidelity more than cost

Do not use `translator_codex_gpt_55` as the default translation caller from this evidence. It was good, but it was never the preferred output and cost 6.9x the mini caller on the same 10-case matrix.

## Evidence

- [Evaluator output](evaluator-output.md)
- [Translation rollup](translations.md)

Summary from the evaluator:

| Caller | Preferred Cases | Total Score | Matrix Cost | Practical Read |
| --- | ---: | ---: | ---: | --- |
| `translator_codex_gpt_54_mini` | 7 | 191/200 | $0.2015 | Best default; usually ties stronger models at much lower cost |
| `translator_codex_gpt_54` | 3 | 198/200 | $0.6674 | Best fallback for token preservation and harder Hebrew |
| `translator_codex_gpt_55` | 0 | 197/200 | $1.3945 | Strong quality, but no observed advantage worth defaulting to |

This is a smoke-test result, not a broad translation benchmark. Re-run the smoke/evaluator workflow when Codex model availability, pricing, or prompt policy changes.
