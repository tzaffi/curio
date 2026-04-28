## Evaluator Summary

Scoring below uses 10-point sub-scores for cost, text fidelity, structure, filenames, and instruction following; total is `/50`.

Overall, `textifier_codex_gpt_54_mini` is the best default for Checkpoint 8G. It is far cheaper than the other two callers, handles skips and unsupported media correctly, preserves most simple OCR cases, and succeeds on the large PDF where `textifier_codex_gpt_53_codex` fails. Its main weaknesses are symbol-level OCR on the Spanish social post, lowercasing shell snippets, and some noisy/invented terminal details.

`textifier_codex_gpt_53_codex` is the strongest on several image OCR cases where exact source text matters, especially the Spanish social post and dense LLM table, but it fails the large scientific PDF by returning `no_text_found`, which is a hard regression for ranking. It is also materially more expensive than mini.

`textifier_codex_gpt_55` is usually strong and gives the richest PDF extraction, but its cost is disproportionate. It also invents or misreads a few critical details, including the social-post `/V1/CHAT` marker and some terminal/file-list details. It should not be preferred as the default unless large-PDF completeness is weighted much higher than cost.

## Evaluator Output Matrix

| Case ID | Caller | Cost | Text Fidelity | Structure | Filenames | Instruction Following | Total | Preferred? | Warnings / Failures | Evaluator Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| C-IMG-TXT-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Exact plain text and path. |
| C-IMG-TXT-01 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | No | None | Exact, but over 2x cost. |
| C-IMG-TXT-01 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | No | None | Exact but much too costly. |
| C-IMG-CODE-01 | textifier_codex_gpt_54_mini | 10 | 8 | 9 | 10 | 9 | 46 | No | None | Preserves code; visible filename in body is uppercased as `FOO.PY`. |
| C-IMG-CODE-01 | textifier_codex_gpt_53_codex | 8 | 9 | 9 | 10 | 9 | 45 | Yes | Unnecessary uncertainty warning | Drops `FILE: foo.py` body line but suggested path is correct; best fidelity on code casing. |
| C-IMG-CODE-01 | textifier_codex_gpt_55 | 4 | 8 | 9 | 10 | 9 | 40 | No | None | Same uppercase filename issue as mini at far higher cost. |
| C-IMG-CODE-02 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Exact text and inferred filename. |
| C-IMG-CODE-02 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | No | None | Exact but higher cost. |
| C-IMG-CODE-02 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | No | None | Exact but expensive. |
| C-IMG-MULTI-01 | textifier_codex_gpt_54_mini | 10 | 8 | 10 | 10 | 9 | 47 | Yes | None | Correct 3-way split and paths; lowercases visible `ECHO`. |
| C-IMG-MULTI-01 | textifier_codex_gpt_53_codex | 8 | 8 | 9 | 10 | 8 | 43 | No | None | Correct split; output format says `txt` rather than shell, and lowercases `ECHO`. |
| C-IMG-MULTI-01 | textifier_codex_gpt_55 | 4 | 8 | 9 | 10 | 8 | 39 | No | None | Correct split but expensive and uses `txt` output format. |
| C-IMG-POST-01 | textifier_codex_gpt_54_mini | 10 | 6 | 9 | 10 | 8 | 43 | No | Good warning | Preserves Spanish text, but critical `/V1/CHAT` becomes `´V1/CHAT`. |
| C-IMG-POST-01 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | Yes | None | Exact handle, timestamp, URL, source language, and `/V1/CHAT`. |
| C-IMG-POST-01 | textifier_codex_gpt_55 | 4 | 5 | 9 | 10 | 7 | 35 | No | Missing warning | Inserts an emoji before `V1/CHAT`, losing the required slash marker. |
| C-PDF-DOC-01 | textifier_codex_gpt_54_mini | 9 | 9 | 10 | 10 | 10 | 48 | Yes | None | Strong extraction; makes `Run make check` a bullet, acceptable. |
| C-PDF-DOC-01 | textifier_codex_gpt_53_codex | 7 | 10 | 10 | 10 | 10 | 47 | No | None | Excellent but twice the cost. |
| C-PDF-DOC-01 | textifier_codex_gpt_55 | 2 | 10 | 10 | 10 | 10 | 42 | No | None | Excellent, but cost is extreme for a simple one-page PDF. |
| C-PDF-TABLE-01 | textifier_codex_gpt_54_mini | 9 | 10 | 10 | 10 | 10 | 49 | Yes | None | Exact table structure and values at lowest cost. |
| C-PDF-TABLE-01 | textifier_codex_gpt_53_codex | 7 | 10 | 10 | 10 | 10 | 47 | No | None | Exact but higher cost. |
| C-PDF-TABLE-01 | textifier_codex_gpt_55 | 2 | 10 | 10 | 10 | 10 | 42 | No | None | Exact but very expensive. |
| C-IMG-RECEIPT-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Exact dense receipt text. |
| C-IMG-RECEIPT-01 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | No | None | Exact but higher cost. |
| C-IMG-RECEIPT-01 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | No | None | Exact but expensive. |
| C-IMG-NO-TEXT-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Correct `no_text_found`, no invented description. |
| C-IMG-NO-TEXT-01 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | No | Good compact warning | Correct. |
| C-IMG-NO-TEXT-01 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | No | Good compact warning | Correct but costly. |
| R-IMG-DASH-01 | textifier_codex_gpt_54_mini | 10 | 9 | 10 | 10 | 10 | 49 | Yes | Good crop warnings | Captures required metrics and visible structure at lowest cost. |
| R-IMG-DASH-01 | textifier_codex_gpt_53_codex | 8 | 9 | 10 | 10 | 10 | 47 | No | Good crop warnings | Similar quality, higher cost. |
| R-IMG-DASH-01 | textifier_codex_gpt_55 | 4 | 9 | 10 | 10 | 10 | 43 | No | Good crop warnings | Good output, unjustified cost. |
| R-IMG-LLM-TABLE-01 | textifier_codex_gpt_54_mini | 10 | 8 | 9 | 10 | 9 | 46 | No | Good warning | Strong, but misses some framing and metadata; less complete than 5.3. |
| R-IMG-LLM-TABLE-01 | textifier_codex_gpt_53_codex | 8 | 9 | 10 | 10 | 10 | 47 | Yes | Good warnings | Best balance: dense table preserved, important framing included, correct handle. |
| R-IMG-LLM-TABLE-01 | textifier_codex_gpt_55 | 4 | 8 | 10 | 10 | 9 | 41 | No | Good warnings | Rich table, but misreads `@gkisokay` as `@qkisokay` and changes KV-cache detail. |
| R-IMG-INFOGRAPHIC-01 | textifier_codex_gpt_54_mini | 10 | 9 | 10 | 10 | 10 | 49 | Yes | Good small-text warnings | Captures commands, providers, gateways, and sections well at lowest cost. |
| R-IMG-INFOGRAPHIC-01 | textifier_codex_gpt_53_codex | 8 | 9 | 10 | 10 | 10 | 47 | No | Good warnings | Similar quality, higher cost. |
| R-IMG-INFOGRAPHIC-01 | textifier_codex_gpt_55 | 4 | 9 | 10 | 10 | 10 | 43 | No | Adequate warning | Similar quality, higher cost. |
| R-IMG-PAPER-PAGE-01 | textifier_codex_gpt_54_mini | 10 | 8 | 9 | 10 | 9 | 46 | No | Good warning | Captures essentials; some suspect text like `textually hints` and `Slice Async`. |
| R-IMG-PAPER-PAGE-01 | textifier_codex_gpt_53_codex | 8 | 9 | 10 | 10 | 10 | 47 | No | Good warnings | Very complete, but has likely OCR error `Same Async Framework`. |
| R-IMG-PAPER-PAGE-01 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | Yes | Good warnings | Best fidelity and structure for this page despite cost. |
| R-IMG-CHARTS-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Exact required chart values and clean Markdown tables. |
| R-IMG-CHARTS-01 | textifier_codex_gpt_53_codex | 8 | 9 | 10 | 10 | 9 | 46 | No | Mild warning | Main values correct; `SpreadSheetBench` capitalization differs. |
| R-IMG-CHARTS-01 | textifier_codex_gpt_55 | 4 | 9 | 10 | 10 | 9 | 42 | No | Mild warning | Main values correct; same capitalization issue and higher cost. |
| R-IMG-TERMINAL-01 | textifier_codex_gpt_54_mini | 10 | 7 | 8 | 10 | 8 | 43 | Yes | Good uncertainty warning | Keeps `ls -alht` and many filenames; wrong `total 2034` and several file/type errors. |
| R-IMG-TERMINAL-01 | textifier_codex_gpt_53_codex | 8 | 6 | 8 | 10 | 7 | 39 | No | Good warnings | Loses `-t` in `ls -alht`, misreads prompt and several filenames. |
| R-IMG-TERMINAL-01 | textifier_codex_gpt_55 | 4 | 7 | 8 | 10 | 8 | 37 | No | Good warnings | Preserves `-alht` and `total 2304`, but many file/type OCR errors at high cost. |
| R-IMG-ASCII-DIAGRAM-01 | textifier_codex_gpt_54_mini | 10 | 8 | 9 | 10 | 9 | 46 | Yes | Good warnings | Preserves full boxed layout and result values; some glyph/spacing artifacts. |
| R-IMG-ASCII-DIAGRAM-01 | textifier_codex_gpt_53_codex | 8 | 9 | 8 | 10 | 9 | 44 | No | Good warnings | Text fidelity strong but layout simplified more than requested. |
| R-IMG-ASCII-DIAGRAM-01 | textifier_codex_gpt_55 | 4 | 8 | 10 | 10 | 9 | 41 | No | Understates glyph uncertainty | Nice layout, but invents `Risk⚡` where source likely differs. |
| R-IMG-COMPARISON-TABLE-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Exact structured table and filename. |
| R-IMG-COMPARISON-TABLE-01 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | No | None | Exact but higher cost. |
| R-IMG-COMPARISON-TABLE-01 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | No | None | Exact but expensive. |
| R-IMG-NO-TEXT-REAL-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Yes | None | Correct no-text result with no invented visual description. |
| R-IMG-NO-TEXT-REAL-01 | textifier_codex_gpt_53_codex | 8 | 10 | 10 | 10 | 10 | 48 | No | Good compact warning | Correct. |
| R-IMG-NO-TEXT-REAL-01 | textifier_codex_gpt_55 | 4 | 10 | 10 | 10 | 10 | 44 | No | None | Correct but costly. |
| C-IMG-DIR-TREE-01 | textifier_codex_gpt_54_mini | 10 | 7 | 9 | 10 | 10 | 46 | Yes | Good warnings | Correct exactly-three split and paths; terminal OCR is noisy but no section bleed in suggested files. |
| C-IMG-DIR-TREE-01 | textifier_codex_gpt_53_codex | 8 | 7 | 9 | 10 | 10 | 44 | No | Good warnings | Correct split and paths; many terminal and paper OCR errors. |
| C-IMG-DIR-TREE-01 | textifier_codex_gpt_55 | 4 | 7 | 9 | 10 | 10 | 40 | No | Good warnings | Correct split and paths; terminal OCR noisy and cost high. |
| R-PDF-PAPER-01 | textifier_codex_gpt_54_mini | 9 | 7 | 8 | 10 | 8 | 42 | No | Excessive app-stream warnings plus useful truncation warning | Succeeds and captures key title/abstract/sections, but truncates later content. |
| R-PDF-PAPER-01 | textifier_codex_gpt_53_codex | 7 | 0 | 0 | 0 | 1 | 8 | No | Hard failure: `no_text_found` | Fails expected `converted` status despite spending substantial cost. |
| R-PDF-PAPER-01 | textifier_codex_gpt_55 | 2 | 9 | 9 | 10 | 9 | 39 | Yes | Good PDF-scope warning plus one app-stream warning | Most complete large-PDF extraction; cost is very high. |
| R-HTML-ARXIV-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-HTML-ARXIV-01 | textifier_codex_gpt_53_codex | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-HTML-ARXIV-01 | textifier_codex_gpt_55 | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-HTML-GITHUB-README-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-HTML-GITHUB-README-01 | textifier_codex_gpt_53_codex | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-HTML-GITHUB-README-01 | textifier_codex_gpt_55 | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-JSON-XARTICLE-CODE-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-JSON-XARTICLE-CODE-01 | textifier_codex_gpt_53_codex | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-JSON-XARTICLE-CODE-01 | textifier_codex_gpt_55 | 10 | 10 | 10 | 10 | 10 | 50 | Tie | Correct skip warning | Correct deterministic text-media skip with no usage. |
| R-ZIP-REPO-01 | textifier_codex_gpt_54_mini | 10 | 10 | 10 | 10 | 9 | 49 | Tie | Duplicate warning | Correct unsupported-media rejection, but warning is duplicated. |
| R-ZIP-REPO-01 | textifier_codex_gpt_53_codex | 10 | 10 | 10 | 10 | 9 | 49 | Tie | Duplicate warning | Correct unsupported-media rejection, but warning is duplicated. |
| R-ZIP-REPO-01 | textifier_codex_gpt_55 | 10 | 10 | 10 | 10 | 9 | 49 | Tie | Duplicate warning | Correct unsupported-media rejection, but warning is duplicated. |

## Final Recommendation

Use `textifier_codex_gpt_54_mini` as the primary Checkpoint 8G textify model. It wins most cases on total utility because its OCR and structure quality are usually close to the larger callers while its cost is much lower. It also handles deterministic text-media skips and unsupported archives correctly.

Keep `textifier_codex_gpt_55` as a targeted fallback for long, high-value PDFs where completeness matters enough to justify the cost. Do not use `textifier_codex_gpt_53_codex` as the default because the large-PDF `no_text_found` failure is too severe, despite strong performance on several image cases.

Fix priorities for the pipeline/model prompt:

1. Preserve exact visible symbols in code-like text, especially `/`, case, and command flags.
2. Avoid normalizing shell/code casing unless explicitly requested.
3. Improve terminal listing OCR or mark low-confidence rows more granularly.
4. Deduplicate repeated unsupported-media warnings.
5. Suppress internal/app-server lag warnings from user-facing warnings unless they affect extraction quality.