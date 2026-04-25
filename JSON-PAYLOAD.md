# Curio JSON Payload

## Purpose

Define the lean v1 persisted JSON payload that `curio` uploads to Google Drive for each accepted evaluation.

This document is normative for:

- the top-level Drive payload shape
- dossier snapshot semantics
- evaluation field semantics
- payload validation rules for a successful accepted evaluation

The machine-readable counterpart to this document is:

- [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json)

This document is not the place to define:

- the Google Sheets workbook model
- detailed translation policy
- LLM provider calling policy
- CLI subcommand flags
- prompt wording
- the exact label-registry contents
- the exact artifact-key derivation algorithm

Those belong in [SCHEMA.md](/Users/zeph/github/tzaffi/curio/SCHEMA.md), [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md), [LLM-CALLER.md](/Users/zeph/github/tzaffi/curio/LLM-CALLER.md), [CLI.md](/Users/zeph/github/tzaffi/curio/CLI.md), registry files, prompt files, and future ADRs.

## Design Principles

The v1 payload should follow these rules:

- One Drive JSON payload represents one persisted accepted evaluation for one artifact.
- The payload combines a deterministic envelope with one exact model-emitted `evaluation` object.
- Python may assemble the deterministic envelope, validate the `evaluation`, and reject invalid outputs.
- Python must not rewrite the meaning of an accepted `evaluation` object after generation.
- `download_row` preserves the exact `iMsgX` downloads-sheet header names.
- `dossier_snapshot` preserves the exact normalized evidence shown to the model, not the raw artifact by itself.
- If text shown to the model was truncated, the payload must say so explicitly.
- If Curio translated non-English source text for evaluation, the translated English text must appear in `dossier_snapshot.evidence_text` as model-visible input.
- Curio uses one prefixed label system in v1:
  - `t:` for topics
  - `e:` for entities
- `evaluation.labels` contains only positive accepted labels.
- `evaluation.proposals` contains only positive proposed labels.
- `evaluation.warnings` is optional operational context for non-fatal issues and should remain compact.

## Top-Level Shape

The persisted payload has this structure:

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "evaluated_at": "2026-04-20T06:15:42.381Z",
  "artifact": { "... deterministic provenance and local artifact metadata ..." },
  "dossier_snapshot": { "... exact model-visible normalized evidence ..." },
  "evaluation": { "... exact model-emitted JSON ..." }
}
```

Top-level fields:

- `payload_version`
  Fixed v1 payload contract identifier. In v1 this must be `curio-evaluation-payload.v1`.
- `evaluated_at`
  UTC RFC 3339 timestamp for when Curio persisted the accepted evaluation.
- `artifact`
  Deterministic upstream `downloads` provenance and local artifact-file metadata.
- `dossier_snapshot`
  The exact compact input Curio showed the model.
- `evaluation`
  The exact accepted model output after validation.

## `artifact`

`artifact` is Python-owned deterministic metadata.

Required fields:

- `download_row`
  Exact `iMsgX` downloads-row shape, preserving the original headers:
  - `Date`
  - `X Date`
  - `iMsgX`
  - `Source`
  - `Column`
  - `Type`
  - `Object`
- `local_artifact`
  Local file metadata for the artifact Curio actually processed. This may be `null` only if no local artifact file exists and Curio categorized directly from non-file evidence.

`local_artifact` fields:

- `path`
  Absolute local filesystem path.
- `sha256`
  SHA-256 hash of the exact local bytes Curio processed.
- `size_bytes`
  Byte length of the local file.
- `mime_type`
  Best deterministic MIME type for the local file.

## `dossier_snapshot`

`dossier_snapshot` is the exact normalized evidence Curio showed the model.

It is not:

- the raw file bytes
- a lossy paraphrase produced after the fact
- an unrestricted dump of everything Curio knew

It is:

- the compact typed input assembled before model evaluation
- after deterministic extraction and cleanup
- with explicit truncation metadata whenever Curio shortened long text
- including paired English translation blocks when translation was part of dossier preparation, as defined in [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md)

Required fields:

- `kind`
  One of:
  - `tweet_json`
  - `x_article_json`
  - `html_page`
  - `repo_zip`
  - `image`
  - `video`
  - `animated_gif`
  - `document`
  - `link`
- `assembled_at`
  UTC RFC 3339 timestamp for dossier assembly.
- `title_hint`
  Best deterministic title candidate before model judgment, or `null`.
- `source_language_hint`
  Best deterministic source-language guess before model judgment, or `null`.
- `evidence_text`
  Ordered list of text blocks shown to the model.
- `details`
  Kind-specific deterministic structured details.

Each `evidence_text` entry must contain:

- `block_id`
  Unique positive integer for that block within `dossier_snapshot.evidence_text`.
- `name`
  Stable identifier such as `tweet_text`, `page_main_text`, or `repo_readme`.
- `language`
  Language code for the text stored in this block.
- `translation_of`
  `null` for original blocks, or the `block_id` of the original source block when this block is a translation.
- `text`
  Exact text shown to the model.
- `was_truncated`
  Whether Curio shortened this block's text before evaluation.
- `original_char_count`
  Character count for this block's text before truncation.

When translation occurs under [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md):

- the original source block remains present with `translation_of = null`
- a paired English block is added using the original block name plus `_en`
- the paired English block uses `language = en`
- the paired English block stores the original block's `block_id` in `translation_of`
- absence of a paired translated block means the original block was treated as English

Illustrative translated block pair:

```json
[
  {
    "block_id": 1,
    "name": "tweet_text",
    "language": "ja",
    "translation_of": null,
    "text": "今日は新しいモデルを公開します。",
    "was_truncated": false,
    "original_char_count": 17
  },
  {
    "block_id": 2,
    "name": "tweet_text_en",
    "language": "en",
    "translation_of": 1,
    "text": "Today we are releasing a new model.",
    "was_truncated": false,
    "original_char_count": 34
  }
]
```

## `evaluation`

`evaluation` is the exact model-emitted JSON block.

Python may:

- validate it
- reject it
- store it under the outer payload envelope

Python must not:

- reword the summary
- change accepted labels
- change proposed labels
- change rationales
- change warnings
- otherwise alter the meaning of accepted model judgment

Required fields:

- `title`
  Curio’s accepted artifact title. This may be derived by the model when no exact title exists in the source.
- `creator`
  Human-readable creator/source actor when known, otherwise `null`.
- `source_language`
  Accepted source language code.
- `summary_en`
  English summary of the artifact.
- `importance`
  - `score`
  - `rationale`
- `labels`
  Array of accepted labels, possibly empty.
- `proposals`
  Array of proposed new labels, possibly empty.
- `warnings`
  Array of warning strings, possibly empty.

`importance.score` uses the v1 float scale `0.0` to `1.0`.

`summary_en` remains the compact English judgment output.

Full translated text, when present, belongs in `dossier_snapshot.evidence_text`, not in `evaluation`.

Each `labels` item contains:

- `label`
- `score`
- `rationale`

`label` must be a canonical prefixed label such as `t:open-models` or `e:gemma`.

Each `proposals` item contains:

- `label`
- `kind`
- `parent`
- `description`
- `score`
- `rationale`

Proposal rules:

- `label` must use the same prefixed label convention as accepted labels.
- `kind` must be one of `topic` or `entity`.
- `kind` must agree with the `label` prefix.
- `parent` is optional and, when present, must use the full prefixed canonical label form.
- `description` is the proposed operator-facing description that would populate the `labels.Description` column if approved.

`warnings` is a compact list of non-fatal issues observed during dossier assembly or evaluation.

## Validation Rules

The payload is valid for a successful accepted evaluation only when all of the following are true:

- the payload validates against [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json)
- `artifact.download_row.Source` is non-empty
- `evaluation.title` is non-empty
- `evaluation.summary_en` is non-empty
- `evaluation.importance.score` is a number from `0.0` to `1.0`
- every `evaluation.labels` entry has `score` greater than `0.0` and at most `1.0`
- every `evaluation.proposals` entry has `score` greater than `0.0` and at most `1.0`
- every `evaluation.labels[].label` uses the canonical prefixed format
- every `evaluation.proposals[].label` uses the canonical prefixed format
- every proposal `kind` agrees with the proposal-label prefix
- `dossier_snapshot.evidence_text` exactly matches the evidence shown to the model
- every `dossier_snapshot.evidence_text[].block_id` is unique within the payload
- every translated evidence block uses non-null `translation_of` pointing to an existing source block
- when translation occurred under [TRANSLATE.md](/Users/zeph/github/tzaffi/curio/TRANSLATE.md), each translated source block has a paired English evidence block
- any text shortening is represented by `was_truncated` and `original_char_count`

The payload is the object that `evaluations.JSON URL` points to in Sheets.

## Example Notes

The examples below are grounded in existing local artifacts under `/Users/zeph/Desktop/iMsgX/downloads`.

These example values are exact:

- `Source`
- `Column`
- `Type`
- local file paths
- local SHA-256 hashes
- local byte sizes
- extracted artifact content used in `dossier_snapshot`

Some values are shown as representative rather than exact because the live Google Sheet row was not locally retrievable during drafting:

- `Date`
- `X Date` when it could not be recovered from the artifact itself
- `iMsgX`
- Drive `Object`

The example labels are illustrative because the canonical registry has not yet been finalized.

The translated block pair shown earlier is illustrative and exists only to demonstrate the `_en` dossier convention.

## Example 1: Tweet JSON

Existing local artifact:

- `/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0066-text-tweet-googledeepmind-status-2039735446628925907.json`

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "evaluated_at": "2026-04-20T06:15:42.381Z",
  "artifact": {
    "download_row": {
      "Date": "2026-04-02 16:05:00 UTC",
      "X Date": "2026-04-02 16:03:21 UTC",
      "iMsgX": "https://docs.google.com/spreadsheets/d/1iQhuJc3LSxFYyO99Cs6EWzTOSefEea0uCREK-e1OpSg/edit#gid=<updates_gid>&range=A66:F66",
      "Source": "https://x.com/GoogleDeepMind/status/2039735446628925907",
      "Column": "Text",
      "Type": "Tweet",
      "Object": "https://drive.google.com/file/d/<tweet_json_drive_file_id>/view"
    },
    "local_artifact": {
      "path": "/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0066-text-tweet-googledeepmind-status-2039735446628925907.json",
      "sha256": "f56d13a1cdd7475f9a71677bc7fbd61652fbdd1349096e1c43be23b61b265e12",
      "size_bytes": 3374,
      "mime_type": "application/json"
    }
  },
  "dossier_snapshot": {
    "kind": "tweet_json",
    "assembled_at": "2026-04-20T06:15:38.022Z",
    "title_hint": "Meet Gemma 4",
    "source_language_hint": "en",
    "evidence_text": [
      {
        "block_id": 1,
        "name": "tweet_text",
        "language": "en",
        "translation_of": null,
        "text": "Meet Gemma 4: our new family of open models you can run on your own hardware.\n\nBuilt for advanced reasoning and agentic workflows, we’re releasing them under an Apache 2.0 license. Here’s what’s new 🧵 https://t.co/u19GbEIoLJ",
        "was_truncated": false,
        "original_char_count": 224
      }
    ],
    "details": {
      "source_url": "https://x.com/GoogleDeepMind/status/2039735446628925907",
      "tweet_id": "2039735446628925907",
      "screen_name": "GoogleDeepMind",
      "display_name": "Google DeepMind",
      "created_at": "2026-04-02T16:03:21.000Z",
      "favorite_count": 8794,
      "conversation_count": 370,
      "media_types": ["animated_gif"]
    }
  },
  "evaluation": {
    "title": "Google DeepMind announces Gemma 4 open models",
    "creator": "Google DeepMind",
    "source_language": "en",
    "summary_en": "Google DeepMind announces Gemma 4, a family of Apache 2.0 open models positioned for advanced reasoning and agentic workflows on user-controlled hardware.",
    "importance": {
      "score": 0.86,
      "rationale": "The artifact is a primary-source product announcement for a major open-model release with clear relevance to open models and agentic tooling."
    },
    "labels": [
      {
        "label": "t:open-models",
        "score": 0.98,
        "rationale": "The tweet explicitly announces a new family of open models."
      },
      {
        "label": "t:local-inference",
        "score": 0.72,
        "rationale": "The announcement emphasizes running the models on user-controlled hardware."
      },
      {
        "label": "t:agentic-workflows",
        "score": 0.58,
        "rationale": "The tweet explicitly positions the models for agentic workflows."
      },
      {
        "label": "e:google-deepmind",
        "score": 0.95,
        "rationale": "Google DeepMind is the named publisher and creator of the release."
      },
      {
        "label": "e:gemma",
        "score": 0.97,
        "rationale": "The artifact is directly about the Gemma 4 model family."
      }
    ],
    "proposals": [],
    "warnings": []
  }
}
```

## Example 2: HTML Page

Existing local artifact:

- `/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0125-x1-htmlpage-providers-inferrs.html`

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "evaluated_at": "2026-04-20T06:17:08.144Z",
  "artifact": {
    "download_row": {
      "Date": "2026-04-10 02:11:19 UTC",
      "X Date": "2026-04-10 01:58:44 UTC",
      "iMsgX": "https://docs.google.com/spreadsheets/d/1iQhuJc3LSxFYyO99Cs6EWzTOSefEea0uCREK-e1OpSg/edit#gid=<updates_gid>&range=A125:F125",
      "Source": "https://docs.openclaw.ai/providers/inferrs",
      "Column": "X1",
      "Type": "HTMLPage",
      "Object": "https://drive.google.com/file/d/<html_drive_file_id>/view"
    },
    "local_artifact": {
      "path": "/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0125-x1-htmlpage-providers-inferrs.html",
      "sha256": "752100fdc97c87f9e0b22f07beac9dcca4c36b660e4dc522bedb6d10d6cb25b7",
      "size_bytes": 4185906,
      "mime_type": "text/html"
    }
  },
  "dossier_snapshot": {
    "kind": "html_page",
    "assembled_at": "2026-04-20T06:16:59.518Z",
    "title_hint": "inferrs - OpenClaw",
    "source_language_hint": "en",
    "evidence_text": [
      {
        "block_id": 1,
        "name": "page_main_text",
        "language": "en",
        "translation_of": null,
        "text": "inferrs - OpenClaw Skip to main content OpenClaw home page English Search... ⌘ K GitHub Releases Discord Search... Navigation Providers inferrs Get started Install Channels Agents Tools & Plugins Models Platforms Gateway & Ops Reference Help Overview Provider Directory Model Provider Quickstart Concepts and configuration Models CLI Model Providers Model Failover Providers Alibaba Model Studio Amazon Bedrock Amazon Bedrock Mantle Anthropic Arcee AI Chutes Claude Max API Proxy Cloudflare AI Gateway ComfyUI Deepgram DeepSeek fal Fireworks GitHub Copilot GLM (Zhipu) Google (Gemini) Groq Hugging Face (Inference) inferrs Kilocode LiteLLM LM Studio MiniMax Mistral Moonshot AI NVIDIA Ollama OpenAI OpenCode OpenCode Go OpenRouter Perplexity Qianfan Qwen Runway SGLang StepFun Synthetic Together AI Venice AI Vercel AI Gateway vLLM Volcengine (Doubao) Vydra xAI Xiaomi MiMo Z.AI On this page inferrs Getting started Full config example Advanced Troubleshooting See also Providers inferrs inferrs can serve local models behind an OpenAI-compatible /v1 API. OpenClaw works with inferrs through the generic openai-completions path. inferrs is currently best treated as a custom self-hosted Ope",
        "was_truncated": true,
        "original_char_count": 5495
      }
    ],
    "details": {
      "canonical_url": "https://docs.openclaw.ai/providers/inferrs",
      "page_title": "inferrs - OpenClaw",
      "text_char_count": 5495
    }
  },
  "evaluation": {
    "title": "OpenClaw provider guide for inferrs",
    "creator": "OpenClaw",
    "source_language": "en",
    "summary_en": "The page explains how to use inferrs as an OpenAI-compatible backend inside OpenClaw, including configuration examples, compatibility caveats, and operational guidance for self-hosted model serving.",
    "importance": {
      "score": 0.64,
      "rationale": "The artifact is practical integration documentation with clear relevance to local model serving and provider configuration, but it is not a major strategic announcement."
    },
    "labels": [
      {
        "label": "t:self-hosted-inference",
        "score": 0.96,
        "rationale": "The page is centered on serving models behind a self-hosted OpenAI-compatible API."
      },
      {
        "label": "t:provider-integration",
        "score": 0.93,
        "rationale": "The core purpose of the page is configuring an inferrs provider entry inside OpenClaw."
      },
      {
        "label": "e:inferrs",
        "score": 0.98,
        "rationale": "The page specifically documents how to use inferrs."
      },
      {
        "label": "e:openclaw",
        "score": 0.67,
        "rationale": "OpenClaw is the host system into which inferrs is being integrated."
      }
    ],
    "proposals": [],
    "warnings": [
      "page_main_text was truncated before evaluation."
    ]
  }
}
```

## Example 3: Repo ZIP

Existing local artifact:

- `/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0079-x2-repo-txbabaxyz-polyrec.zip`

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "evaluated_at": "2026-04-20T06:19:33.006Z",
  "artifact": {
    "download_row": {
      "Date": "2026-01-31 12:42:10 UTC",
      "X Date": "2026-01-31 12:38:00 UTC",
      "iMsgX": "https://docs.google.com/spreadsheets/d/1iQhuJc3LSxFYyO99Cs6EWzTOSefEea0uCREK-e1OpSg/edit#gid=<updates_gid>&range=A79:F79",
      "Source": "https://github.com/txbabaxyz/polyrec",
      "Column": "X2",
      "Type": "Repo",
      "Object": "https://drive.google.com/file/d/<repo_zip_drive_file_id>/view"
    },
    "local_artifact": {
      "path": "/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0079-x2-repo-txbabaxyz-polyrec.zip",
      "sha256": "6d8882f1203700d23ec6f303439cc9e516539a8de378759c62058366f04f310a",
      "size_bytes": 25614,
      "mime_type": "application/zip"
    }
  },
  "dossier_snapshot": {
    "kind": "repo_zip",
    "assembled_at": "2026-04-20T06:19:25.612Z",
    "title_hint": "Polymarket BTC Dashboard (polyrec)",
    "source_language_hint": "en",
    "evidence_text": [
      {
        "block_id": 1,
        "name": "repo_readme",
        "language": "en",
        "translation_of": null,
        "text": "# Polymarket BTC Dashboard (polyrec)\n\nReal-time terminal dashboard for Polymarket BTC 15-minute UP/DOWN prediction markets. Aggregates price feeds from Chainlink oracle, Binance, and Polymarket orderbook data. Includes backtesting tools for trading strategy research.\n\n## Features\n\n- **Real-time Dashboard** (`dash.py`) - Terminal UI showing:\n  - Chainlink BTC/USD oracle price (via Polymarket RTDS)\n  - Binance BTCUSDT 1s kline price and volume\n  - Polymarket orderbook depth for UP/DOWN markets\n  - Technical indicators: returns, ATR, VWAP, volume spikes\n  - Automatic CSV logging per 15-minute market\n\n- **Backtesting Tools**:\n  - `replicate_balance.py` - Balance replication strategy simulator\n  - `fade_impulse_backtest.py` - Impulse fade strategy backtester\n  - `visualize_fade_impulse.py` - Strategy visualization\n\n## Requirements\n\n- Python 3.10+\n- Node.js (for Chainlink feed) ...",
        "was_truncated": true,
        "original_char_count": 4793
      }
    ],
    "details": {
      "repo_url": "https://github.com/txbabaxyz/polyrec",
      "owner": "txbabaxyz",
      "repo_name": "polyrec",
      "top_level_entries": [
        "LICENSE",
        "README.md",
        "dash.py",
        "fade_impulse_backtest.py",
        "replicate_balance.py",
        "requirements.txt",
        "visualize_fade_impulse.py"
      ],
      "manifest_files": ["requirements.txt"],
      "readme_present": true
    }
  },
  "evaluation": {
    "title": "Polymarket BTC dashboard and backtesting toolkit",
    "creator": "txbabaxyz",
    "source_language": "en",
    "summary_en": "The repository packages a real-time Polymarket BTC market dashboard together with backtesting and visualization scripts for market-data-driven trading research.",
    "importance": {
      "score": 0.61,
      "rationale": "The repo is a concrete specialized tool for Polymarket market monitoring and strategy research, but it appears narrower in scope than a broadly reusable infrastructure project."
    },
    "labels": [
      {
        "label": "t:prediction-markets",
        "score": 0.97,
        "rationale": "The repository is explicitly built around Polymarket BTC UP/DOWN prediction markets."
      },
      {
        "label": "t:trading-infrastructure",
        "score": 0.64,
        "rationale": "The repository includes a live dashboard, logging, and backtesting utilities for trading-related workflows."
      },
      {
        "label": "e:polymarket",
        "score": 0.96,
        "rationale": "Polymarket is the core market venue and data source the repository is built around."
      },
      {
        "label": "e:binance",
        "score": 0.54,
        "rationale": "Binance is a named upstream market-data input used by the dashboard."
      },
      {
        "label": "e:chainlink",
        "score": 0.53,
        "rationale": "Chainlink oracle data is an explicit input to the system."
      }
    ],
    "proposals": [
      {
        "label": "t:market-microstructure-tooling",
        "kind": "topic",
        "parent": "t:trading-infrastructure",
        "description": "Tools focused on real-time orderbook, spread, imbalance, and execution-oriented market-data analysis.",
        "score": 0.57,
        "rationale": "The repo emphasizes orderbook depth, imbalance, microprice, and short-horizon market analytics rather than only generic trading commentary."
      }
    ],
    "warnings": [
      "repo_readme was truncated before evaluation."
    ]
  }
}
```
