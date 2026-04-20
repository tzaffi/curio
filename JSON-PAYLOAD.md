# Curio JSON Payload

## Purpose

Define the v1 persisted JSON payload that `curio` uploads to Google Drive for each accepted categorization.

This document is normative for:

- the top-level Drive payload shape
- the boundary between deterministic Python-owned context and model-emitted judgment
- dossier snapshot semantics
- evaluation field semantics
- payload validation rules for a successful categorization

The machine-readable counterpart to this document is:

- [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json)

This document is not the place to define:

- the Google Sheets workbook model
- the curated concept/entity registries
- prompt wording
- the exact artifact-id derivation algorithm

Those belong in [SCHEMA.md](/Users/zeph/github/tzaffi/curio/SCHEMA.md), registry files, prompt files, and future ADRs.

## Design Principles

The v1 payload should follow these rules:

- One Drive JSON payload represents one accepted categorization result for one artifact.
- The payload combines a deterministic envelope with one exact model-emitted `evaluation` object.
- Python may assemble the envelope, validate the `evaluation`, and reject invalid outputs.
- Python must not rewrite the meaning of the accepted `evaluation` object after generation.
- `download_row` preserves the exact `iMsgX` downloads-sheet header names.
- `dossier_snapshot` preserves the exact normalized evidence shown to the model, not the raw artifact by itself.
- If text shown to the model was truncated, the payload must say so explicitly.
- The payload distinguishes between:
  - concepts, which are canonical topical/categorical assignments
  - entities, which are canonical named things such as models, orgs, products, technologies, people, and repos
- `evaluation.concepts` and `evaluation.entities` contain only positive assignments; relevance `0` is omitted.
- Aliases and concept relations are registry-level metadata. They do not appear directly in the payload except through canonical ids and proposal context.

## Top-Level Shape

The persisted payload has this structure:

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "generated_at": "2026-04-20T06:15:42.381Z",
  "artifact": { "... deterministic provenance and local artifact metadata ..." },
  "run": { "... deterministic run/version context ..." },
  "dossier_snapshot": { "... exact model-visible normalized evidence ..." },
  "evaluation": { "... exact model-emitted JSON ..." }
}
```

Top-level fields:

- `payload_version`
  Fixed v1 payload contract identifier. In v1 this must be `curio-evaluation-payload.v1`.
- `generated_at`
  UTC RFC 3339 timestamp for when Curio persisted the payload.
- `artifact`
  Deterministic artifact identity, upstream `downloads` provenance, and local artifact-file metadata.
- `run`
  Deterministic run metadata and version trio.
- `dossier_snapshot`
  The exact compact input Curio showed the model.
- `evaluation`
  The exact accepted model output after validation.

## `artifact`

`artifact` is Python-owned deterministic metadata.

Required fields:

- `id`
  Stable artifact key. This must equal the `artifacts.id` value in Sheets.
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

## `run`

`run` is Python-owned deterministic metadata.

Required fields:

- `id`
  Stable run identifier. This must equal the `runs.id` value in Sheets.
- `trigger_mode`
  One of `manual` or `automation`.
- `schema_version`
- `prompt_version`
- `vocabulary_version`

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

- `name`
  Stable identifier such as `tweet_text`, `page_main_text`, or `repo_readme`.
- `text`
  Exact text shown to the model.
- `was_truncated`
  Whether Curio shortened the original text before evaluation.
- `original_char_count`
  Character count before truncation.

## `evaluation`

`evaluation` is the exact model-emitted JSON block.

Python may:

- validate it
- reject it
- store it under the outer payload envelope

Python must not:

- reword the summary
- change concept assignments
- change entity assignments
- change rationales
- add or remove proposals
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
- `translation`
  Translation metadata:
  - `was_required`
  - `translated_excerpt_en`
- `overall_importance`
  - `score`
  - `rationale`
- `concepts`
  Array of accepted direct concept assignments only.
- `concept_proposals`
  Array of proposed new concepts, possibly empty.
- `entities`
  Array of accepted entity mentions only.
- `entity_proposals`
  Array of proposed new entities, possibly empty.

`overall_importance.score` uses the v1 `0-5` scale.

Each `concepts` item contains:

- `concept_id`
- `relevance`
- `rationale`

`relevance` uses the v1 `1-3` scale.

`evaluation.concepts` should contain only direct concept assignments, not broader-concept closure implied by the concept graph.

Each `concept_proposals` item contains:

- `proposed_concept_id`
- `pref_label`
- `definition`
- `relevance`
- `rationale`
- `closest_existing_concepts`

Each `entities` item contains:

- `entity_id`
- `relevance`
- `rationale`

Each `entity_proposals` item contains:

- `proposed_entity_id`
- `canonical_name`
- `entity_type`
- `relevance`
- `rationale`
- `closest_existing_entities`

## Validation And Categorization Rules

The payload is valid for a successful accepted categorization only when all of the following are true:

- the payload validates against [schemas/evaluation_payload.schema.json](/Users/zeph/github/tzaffi/curio/schemas/evaluation_payload.schema.json)
- `artifact.download_row.Source` is non-empty
- `artifact.id` is non-empty
- `evaluation.title` is non-empty
- `evaluation.summary_en` is non-empty
- `evaluation.overall_importance.score` is an integer from `0` to `5`
- every `evaluation.concepts` entry has `relevance` from `1` to `3`
- every `evaluation.concept_proposals` entry has `relevance` from `1` to `3`
- every `evaluation.entities` entry has `relevance` from `1` to `3`
- every `evaluation.entity_proposals` entry has `relevance` from `1` to `3`
- `dossier_snapshot.evidence_text` exactly matches the evidence shown to the model
- any text shortening is represented by `was_truncated` and `original_char_count`

The payload is the object that `artifacts.latest_json_url` points to in Sheets.

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

The example concept ids and entity ids are illustrative because the canonical registries have not yet been finalized.

## Example 1: Tweet JSON

Existing local artifact:

- `/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0066-text-tweet-googledeepmind-status-2039735446628925907.json`

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "generated_at": "2026-04-20T06:15:42.381Z",
  "artifact": {
    "id": "artifact_googledeepmind_2039735446628925907",
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
  "run": {
    "id": "run_2026_04_20_001",
    "trigger_mode": "manual",
    "schema_version": "v1",
    "prompt_version": "v1",
    "vocabulary_version": "v0"
  },
  "dossier_snapshot": {
    "kind": "tweet_json",
    "assembled_at": "2026-04-20T06:15:38.022Z",
    "title_hint": "Meet Gemma 4",
    "source_language_hint": "en",
    "evidence_text": [
      {
        "name": "tweet_text",
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
    "translation": {
      "was_required": false,
      "translated_excerpt_en": null
    },
    "overall_importance": {
      "score": 4,
      "rationale": "The artifact is a primary-source product announcement for a major open-model release with clear relevance to open models and agentic tooling."
    },
    "concepts": [
      {
        "concept_id": "open-models",
        "relevance": 3,
        "rationale": "The tweet explicitly announces a new family of open models."
      },
      {
        "concept_id": "local-inference",
        "relevance": 2,
        "rationale": "The announcement emphasizes running the models on user-controlled hardware."
      },
      {
        "concept_id": "agentic-workflows",
        "relevance": 2,
        "rationale": "The tweet explicitly positions the models for agentic workflows."
      }
    ],
    "concept_proposals": [],
    "entities": [
      {
        "entity_id": "google-deepmind",
        "relevance": 3,
        "rationale": "Google DeepMind is the named publisher and creator of the release."
      },
      {
        "entity_id": "gemma",
        "relevance": 3,
        "rationale": "The artifact is directly about the Gemma 4 model family."
      }
    ],
    "entity_proposals": []
  }
}
```

## Example 2: HTML Page

Existing local artifact:

- `/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0125-x1-htmlpage-providers-inferrs.html`

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "generated_at": "2026-04-20T06:17:08.144Z",
  "artifact": {
    "id": "artifact_docs_openclaw_ai_providers_inferrs",
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
  "run": {
    "id": "run_2026_04_20_001",
    "trigger_mode": "manual",
    "schema_version": "v1",
    "prompt_version": "v1",
    "vocabulary_version": "v0"
  },
  "dossier_snapshot": {
    "kind": "html_page",
    "assembled_at": "2026-04-20T06:16:59.518Z",
    "title_hint": "inferrs - OpenClaw",
    "source_language_hint": "en",
    "evidence_text": [
      {
        "name": "page_main_text",
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
    "translation": {
      "was_required": false,
      "translated_excerpt_en": null
    },
    "overall_importance": {
      "score": 3,
      "rationale": "The artifact is practical integration documentation with clear relevance to local model serving and provider configuration, but it is not a major strategic announcement."
    },
    "concepts": [
      {
        "concept_id": "self-hosted-inference",
        "relevance": 3,
        "rationale": "The page is centered on serving models behind a self-hosted OpenAI-compatible API."
      },
      {
        "concept_id": "provider-integration",
        "relevance": 3,
        "rationale": "The core purpose of the page is configuring an inferrs provider entry inside OpenClaw."
      }
    ],
    "concept_proposals": [],
    "entities": [
      {
        "entity_id": "inferrs",
        "relevance": 3,
        "rationale": "The page specifically documents how to use inferrs."
      },
      {
        "entity_id": "openclaw",
        "relevance": 2,
        "rationale": "OpenClaw is the host system into which inferrs is being integrated."
      }
    ],
    "entity_proposals": []
  }
}
```

## Example 3: Repo ZIP

Existing local artifact:

- `/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0079-x2-repo-txbabaxyz-polyrec.zip`

```json
{
  "payload_version": "curio-evaluation-payload.v1",
  "generated_at": "2026-04-20T06:19:33.006Z",
  "artifact": {
    "id": "artifact_github_txbabaxyz_polyrec",
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
  "run": {
    "id": "run_2026_04_20_001",
    "trigger_mode": "manual",
    "schema_version": "v1",
    "prompt_version": "v1",
    "vocabulary_version": "v0"
  },
  "dossier_snapshot": {
    "kind": "repo_zip",
    "assembled_at": "2026-04-20T06:19:25.612Z",
    "title_hint": "Polymarket BTC Dashboard (polyrec)",
    "source_language_hint": "en",
    "evidence_text": [
      {
        "name": "repo_readme",
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
    "translation": {
      "was_required": false,
      "translated_excerpt_en": null
    },
    "overall_importance": {
      "score": 3,
      "rationale": "The repo is a concrete specialized tool for Polymarket market monitoring and strategy research, but it appears narrower in scope than a broadly reusable infrastructure project."
    },
    "concepts": [
      {
        "concept_id": "prediction-markets",
        "relevance": 3,
        "rationale": "The repository is explicitly built around Polymarket BTC UP/DOWN prediction markets."
      },
      {
        "concept_id": "trading-infrastructure",
        "relevance": 2,
        "rationale": "The repository includes a live dashboard, logging, and backtesting utilities for trading-related workflows."
      }
    ],
    "concept_proposals": [
      {
        "proposed_concept_id": "market-microstructure-tooling",
        "pref_label": "Market Microstructure Tooling",
        "definition": "Tools focused on real-time orderbook, spread, imbalance, and execution-oriented market-data analysis.",
        "relevance": 2,
        "rationale": "The repo emphasizes orderbook depth, imbalance, microprice, and short-horizon market analytics rather than only generic trading commentary.",
        "closest_existing_concepts": ["trading-infrastructure"]
      }
    ],
    "entities": [
      {
        "entity_id": "polymarket",
        "relevance": 3,
        "rationale": "Polymarket is the core market venue and data source the repository is built around."
      },
      {
        "entity_id": "binance",
        "relevance": 2,
        "rationale": "Binance is a named upstream market-data input used by the dashboard."
      },
      {
        "entity_id": "chainlink",
        "relevance": 2,
        "rationale": "Chainlink oracle data is an explicit input to the system."
      }
    ],
    "entity_proposals": []
  }
}
```
