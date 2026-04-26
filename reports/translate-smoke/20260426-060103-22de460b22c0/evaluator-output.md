## Evaluator Summary

Overall quality is high: all rows are usable, with no major omissions, added political context, or safety-style sanitization. `translator_codex_gpt_54_mini` is most often preferred because it matches the stronger models on fidelity while costing substantially less; `translator_codex_gpt_54` and `translator_codex_gpt_55` sometimes produce slightly more natural phrasing, but usually not enough to overcome cost. Main risks are small preservation drift in technical tokens such as `64gb`/`90tok/s`, minor over-normalization of quoted Spanish endpoint wording, and occasional awkward literal Hebrew phrasing.

## Evaluator Output Matrix

| Case ID | Caller | Cost | Adequacy | Fluency | Preservation | Instruction Following | Total | Preferred? | Warnings / Failures | Evaluator Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| Z-CN-01 | translator_codex_gpt_54_mini | 0.0202629 | 5 | 4 | 5 | 5 | 19 | yes | None | Accurate and complete; slightly awkward in “all memory and skills do not pile up,” but preserves all required artifacts. |
| Z-CN-01 | translator_codex_gpt_54 | 0.068749 | 5 | 4 | 5 | 5 | 19 | no | None | Very good, with minor awkwardness around “Swift-written 3M small client.” Higher cost loses tie. |
| Z-CN-01 | translator_codex_gpt_55 | 0.143411 | 5 | 5 | 5 | 5 | 20 | no | None | Best English polish, but the quality gain is small relative to much higher cost; not selected over the cheaper strong output. |
| Z-CN-02 | translator_codex_gpt_54_mini | 0.022211099999999998 | 5 | 5 | 5 | 5 | 20 | yes | None | Clear, complete, and preserves commands, tool names, counts, and final “Link:” placeholder. Lowest cost among top-quality outputs. |
| Z-CN-02 | translator_codex_gpt_54 | 0.069503 | 5 | 5 | 5 | 5 | 20 | no | None | Equally strong translation; cost loses tie. |
| Z-CN-02 | translator_codex_gpt_55 | 0.145241 | 5 | 5 | 5 | 5 | 20 | no | None | Equally strong translation; cost loses tie. |
| Z-EN-01 | translator_codex_gpt_54_mini | 0.02055915 | 5 | 5 | 5 | 5 | 20 | yes | None | Correct English pass-through with `translation_required=false`; preserves tone and all named entities exactly. |
| Z-EN-01 | translator_codex_gpt_54 | 0.0640955 | 5 | 5 | 5 | 5 | 20 | no | None | Correct pass-through; cost loses tie. |
| Z-EN-01 | translator_codex_gpt_55 | 0.134756 | 5 | 5 | 5 | 5 | 20 | no | None | Correct pass-through; cost loses tie. |
| Z-KO-01 | translator_codex_gpt_54_mini | 0.02075565 | 5 | 5 | 4 | 5 | 19 | no | Minor token normalization | Changes `64gb` to `64GB` and `90tok/s` to `90 tok/s`; meaning is intact but preservation is weaker. |
| Z-KO-01 | translator_codex_gpt_54 | 0.0653055 | 5 | 5 | 5 | 5 | 20 | yes | None | Best preservation of required mixed English tokens, including `64gb` and `90tok/s`, with natural English. |
| Z-KO-01 | translator_codex_gpt_55 | 0.136276 | 5 | 5 | 5 | 5 | 20 | no | None | Equally accurate and preserves required tokens; higher cost loses tie to gpt_54. |
| Z-AR-01 | translator_codex_gpt_54_mini | 0.019293900000000003 | 5 | 5 | 4 | 5 | 19 | no | Minor capitalization drift | Accurate and idiomatic, but lowercases required English terms like `Inference`, `Enterprise`, `Local Agents`, and `Cloud APIs`. |
| Z-AR-01 | translator_codex_gpt_54 | 0.065283 | 5 | 5 | 5 | 5 | 20 | yes | None | Preserves technical terms and capitalization best while retaining colloquial force. |
| Z-AR-01 | translator_codex_gpt_55 | 0.136651 | 5 | 5 | 4 | 5 | 19 | no | Minor capitalization drift | Strong translation, but changes `Inference` to lowercase `inference` and `Enterprise` to lowercase in one sentence. |
| Z-HE-01 | translator_codex_gpt_54_mini | 0.020563650000000003 | 5 | 5 | 5 | 5 | 20 | yes | None | Accurate, natural, and preserves political language without additions or softening. Lowest cost among top outputs. |
| Z-HE-01 | translator_codex_gpt_54 | 0.0642155 | 5 | 5 | 5 | 5 | 20 | no | None | Accurate and natural; cost loses tie. |
| Z-HE-01 | translator_codex_gpt_55 | 0.134876 | 5 | 5 | 5 | 5 | 20 | no | None | Accurate and natural; cost loses tie. |
| Z-HE-02 | translator_codex_gpt_54_mini | 0.019477650000000003 | 3 | 3 | 4 | 5 | 15 | no | Literal mistranslation | “The station of death” mistranslates “stench/smell of death”; “while I am writhing” is likely wrong speaker/subject handling. |
| Z-HE-02 | translator_codex_gpt_54 | 0.0658655 | 5 | 5 | 5 | 5 | 20 | yes | None | Best balance of accuracy, graphic tone, profanity, and fluent English without sanitization. |
| Z-HE-02 | translator_codex_gpt_55 | 0.14833 | 5 | 5 | 5 | 5 | 20 | no | None | Also strong; punctuation slightly normalizes line style and cost is higher, so it loses tie. |
| C-JA-01 | translator_codex_gpt_54_mini | 0.018947400000000003 | 5 | 5 | 5 | 5 | 20 | yes | None | Concise, accurate, and preserves all release metadata, emoji, hashtag, and URL. Lowest cost. |
| C-JA-01 | translator_codex_gpt_54 | 0.070801 | 5 | 5 | 5 | 5 | 20 | no | None | Equally good; cost loses tie. |
| C-JA-01 | translator_codex_gpt_55 | 0.134581 | 5 | 5 | 5 | 5 | 20 | no | None | Equally good; cost loses tie. |
| C-HI-01 | translator_codex_gpt_54_mini | 0.018970650000000002 | 5 | 5 | 5 | 5 | 20 | yes | None | Fully captures imperative intent and preserves PR number, command, and filename; backticks are acceptable artifact protection. |
| C-HI-01 | translator_codex_gpt_54 | 0.0641605 | 5 | 5 | 5 | 5 | 20 | no | Warning acceptable | Accurate; `mixed-language` warning is reasonable but not needed. Cost loses tie. |
| C-HI-01 | translator_codex_gpt_55 | 0.134766 | 5 | 5 | 5 | 4 | 19 | no | Over-warning | Translation is accurate, but `mixed-language ambiguity` overstates a straightforward Hinglish sentence. |
| C-ES-01 | translator_codex_gpt_54_mini | 0.02047815 | 5 | 5 | 4 | 5 | 19 | yes | Quote content translated | Good translation, but quoted sentence is translated rather than preserving the exact quoted Spanish text listed in requirements. Lowest cost among similar outputs. |
| C-ES-01 | translator_codex_gpt_54 | 0.0694665 | 5 | 5 | 4 | 5 | 19 | no | Quote content translated | Accurate and fluent, but does not preserve the exact Spanish quote; cost loses tie. |
| C-ES-01 | translator_codex_gpt_55 | 0.14566 | 5 | 5 | 4 | 5 | 19 | no | Quote content translated | Accurate and fluent, but does not preserve the exact Spanish quote; highest cost. |

## Per-Case Preference Notes

- Z-CN-01: `translator_codex_gpt_54_mini` won on practical value: its fidelity and preservation match the stronger outputs closely, and cost breaks the near-tie.
- Z-CN-02: `translator_codex_gpt_54_mini` tied on quality with both larger callers and won by lower cost.
- Z-EN-01: All three correctly passed English through unchanged with `translation_required=false`; cost decided the tie for `translator_codex_gpt_54_mini`.
- Z-KO-01: `translator_codex_gpt_54` won because it preserved required technical tokens exactly, unlike mini’s `64GB` and `90 tok/s`; cost did not decide the top choice.
- Z-AR-01: `translator_codex_gpt_54` won by preserving English technical term capitalization better than the others; cost did not decide the top choice.
- Z-HE-01: All three were faithful and appropriately neutral; `translator_codex_gpt_54_mini` won by lower cost.
- Z-HE-02: `translator_codex_gpt_54` won for accurate graphic Hebrew rendering and preserved profanity without sanitization; gpt_55 was close but higher cost, while mini had real mistranslations.
- C-JA-01: All three preserved the release metadata and produced concise English; `translator_codex_gpt_54_mini` won by lower cost.
- C-HI-01: All three translated the imperative correctly, but `translator_codex_gpt_54_mini` avoided unnecessary ambiguity warning and had the lowest cost.
- C-ES-01: All three translated the quoted Spanish instead of preserving it exactly, so quality was essentially tied; `translator_codex_gpt_54_mini` won by lower cost.