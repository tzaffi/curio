# Labeling Schemes and Retrieval Architecture

## Current Status

This document is retained as a starting-point discussion artifact. The normative
Curio KB decision is now [KB.md](/Users/zeph/github/tzaffi/curio/specs/KB.md).

The main correction is that labels are not the KB. They are lightweight facets
for browsing, routing, filtering, and reranking. Curio still needs labels, but
the downstream KB also needs chunks, atomic claims, entity mentions, temporal
metadata, retrieval events, derived summaries, and rebuildable graph overlays.

## Executive Summary

Curio should avoid building a heavyweight ontology, taxonomy engine, or graph-ranking system during the initial implementation phase.

Instead, Curio should adopt a hybrid architecture:

- deterministic infrastructure for ingestion, storage, retrieval, and ranking
- frontier-model-driven reasoning for semantic grouping, synthesis, aggregation, and ranking of concepts

The core idea is:

> Use local infrastructure to reliably retrieve the _right evidence_.
> Use frontier models (via Codex/OpenAI) to reason over that evidence.

This approach maximizes:

- development velocity
- flexibility
- retrieval quality
- adaptability to evolving domains

while minimizing:

- ontology maintenance
- brittle clustering pipelines
- over-engineered graph systems
- premature optimization

The recommended implementation strategy is:

1. Build a deterministic ingestion and retrieval substrate
2. Generate lightweight metadata using an LLM
3. Store embeddings + metadata locally
4. Expose deterministic retrieval tools to Codex
5. Let Codex orchestrate retrieval and perform synthesis

This should be achievable in roughly 1–3 days of focused implementation work.

---

# Goals

Curio should support:

- tweet-centric knowledge ingestion
- related media ingestion:
  - articles
  - PDFs
  - repos
  - images
  - videos/transcripts
- semantic retrieval
- recency-aware retrieval
- synthesis over multiple artifacts
- top-N aggregation queries
- comparison queries
- citation-aware answers

Example queries:

- "Should I use Hermes, OpenClaw, or a combination?"
- "What are the top 10 trading strategies in my KB?"
- "What changed recently regarding local-agent routing?"

The system should prioritize:

- flexibility over rigid schemas
- explainability over magic
- iterative evolution over premature architecture

---

# Research Findings

## Key Insight

Modern frontier models are substantially better at:

- semantic grouping
- synonym merging
- fuzzy categorization
- synthesis
- ranking concepts

than handcrafted ontologies or embedding-clustering pipelines for small-to-medium curated corpora.

This changes the architecture tradeoffs.

Historically:

- ontology-first systems were necessary
- deterministic categorization pipelines were favored

Today:

- embeddings + lightweight metadata + frontier synthesis is often superior
- especially for:
  - small corpora
  - rapidly evolving domains
  - exploratory research workflows

---

## What Should Remain Deterministic

The following should remain deterministic and infrastructure-driven:

- ingestion
- object persistence
- extraction
- chunking
- embedding generation
- vector search
- keyword search
- reranking
- recency weighting
- importance weighting
- context packing
- citation tracking

These are infrastructure responsibilities.

---

## What Should Be LLM-Driven

The following should be delegated to frontier models:

- summaries
- tags
- entities
- importance estimates
- query classification
- query planning
- semantic grouping
- strategy deduplication
- top-N synthesis
- comparison synthesis
- conflict resolution

These are reasoning responsibilities.

---

## Why Not Build a Full Ontology?

A full ontology/taxonomy system would require:

- canonical label management
- label deduplication
- clustering pipelines
- graph maintenance
- ranking algorithms
- ontology migrations
- synonym resolution infrastructure

This would significantly increase:

- implementation complexity
- maintenance burden
- brittleness
- iteration cost

while likely underperforming frontier models for the current corpus size.

This may become worthwhile later if:

- the corpus grows dramatically
- reproducibility becomes critical
- structured analytics become necessary
- agentic workflows require stable symbolic concepts

This is considered a future optimization.

---

# Suggested Design

# High-Level Architecture

```text
User
  ↓
Curio
  ↓
Codex / Frontier Model
  ↓
Deterministic Retrieval Tools
  ↓
Local KB Infrastructure
```

Core principle:

> Codex acts as planner + synthesizer.
> Curio tools act as deterministic executors.

---

# Ingestion Pipeline

## Overview

Each tweet should become an "artifact bundle".

Example:

```text
Tweet
 ├── tweet text
 ├── author/date/url
 ├── linked article
 ├── linked PDF
 ├── linked repo
 ├── linked images
 └── linked video/transcript
```

---

## Ingestion Steps

### 1. Fetch + Normalize

Deterministic.

Responsibilities:

- download source artifacts
- preserve provenance
- normalize metadata
- generate stable IDs

Persist:

- URLs
- timestamps
- author/source info
- local cache paths

---

### 2. Text Extraction

Mostly deterministic.

Examples:

- article → markdown/plain text
- PDF → extracted text/OCR
- repo → README + selected files
- image → OCR/captioning
- video → transcript

Persist:

- extracted text
- extraction method
- extraction quality/confidence

---

### 3. Chunking

Deterministic.

Chunk:

- tweets
- article sections
- PDF sections
- repo files/sections
- transcript windows

Each chunk should maintain:

- source linkage
- position info
- provenance
- timestamps

---

### 4. LLM Metadata Pass

Use a frontier model or cheap model.

Generate lightweight metadata only.

Suggested fields:

```json
{
  "summary": "...",
  "tags": ["..."],
  "entities": ["..."],
  "importance": 0.0,
  "artifact_type": "tutorial",
  "time_sensitivity": "medium",
  "claims": [
    {
      "claim": "...",
      "confidence": 0.7
    }
  ]
}
```

Avoid:

- canonical labels
- ontology IDs
- rigid category hierarchies

---

### 5. Embeddings

Generate embeddings for:

- chunk text
- summaries
- optionally tags/entities

Store embeddings locally.

---

### 6. Persistence

Recommended storage layers:

## Object Store

Stores:

- raw artifacts
- extracted text
- transcripts
- OCR outputs

Examples:

- local filesystem
- S3-compatible store
- Google Drive

---

## Metadata Store

Stores:

- bundles
- chunks
- metadata
- timestamps
- tags
- importance scores
- provenance

Recommended:

- SQLite initially
- PostgreSQL later if needed

---

## Vector Index

Stores:

- embeddings
- chunk references

Recommended:

- FAISS initially

Avoid introducing distributed vector databases prematurely.

---

# Retrieval Architecture

# High-Level Flow

```text
User Prompt
   ↓
Query Classifier / Planner
   ↓
Hybrid Retrieval
   ↓
Reranking
   ↓
Context Packing
   ↓
Frontier Synthesis
   ↓
Answer + Citations
```

---

## Query Classification

Use Codex/frontier model.

Determine:

- query intent
- entities
- domains
- recency requirements
- aggregation requirements

Example:

```json
{
  "query_type": "comparison",
  "entities": ["Hermes", "OpenClaw"],
  "needs_recency": true
}
```

---

## Query Planning

Codex should generate multiple retrieval queries.

Example:

```json
{
  "searches": [
    "Hermes strengths weaknesses",
    "OpenClaw routing",
    "hybrid local agent routing"
  ]
}
```

Single-query retrieval is discouraged.

---

## Hybrid Retrieval

Deterministic.

Combine:

- vector search
- keyword search
- tag/entity matching
- recent-document retrieval

This improves recall substantially.

---

## Reranking

Deterministic.

Suggested formula:

```text
score =
  0.50 * vector_similarity
+ 0.20 * keyword_match
+ 0.15 * recency
+ 0.10 * importance
+ 0.05 * extraction_quality
```

This should remain configurable.

---

## Context Packing

Deterministic.

The frontier model should receive:

- chunk text
- summaries
- source metadata
- dates
- importance scores
- citations

Avoid passing raw unstructured dumps.

---

## Frontier Synthesis

The frontier model should:

- compare concepts
- merge duplicates
- rank strategies
- summarize findings
- identify conflicts
- generate recommendations

Examples:

- Hermes vs OpenClaw comparison
- top-N strategy ranking
- trend analysis
- conflicting claims analysis

---

# Tool / Skill Architecture

# Core Insight

The retrieval flow should NOT rely purely on prompting.

Instead:

- Codex should orchestrate
- deterministic tools should execute

Pattern:

```text
LLM Planner
  ↓
Deterministic Tools
  ↓
LLM Synthesizer
```

---

# Recommended Approach

Curio should expose deterministic retrieval capabilities as Codex tools.

Do NOT build:

- giant monolithic "answer everything" tools
- retrieval hidden inside prompts
- opaque pipelines

Prefer:

- small composable tools
- structured inputs/outputs
- deterministic retrieval semantics

---

## Suggested Initial Tools

### search_kb

Responsibilities:

- vector search
- keyword search
- reranking
- filtering

Suggested API:

```json
{
  "query": "Hermes vs OpenClaw",
  "top_k": 20,
  "recency_bias": "medium"
}
```

Returns:

- chunk text
- metadata
- scores
- citations

---

### get_context

Fetch:

- larger contexts
- neighboring chunks
- full artifacts
- bundle relationships

---

# Curio + Codex Integration Strategy

Recommended architecture:

```text
curio query "top 10 trading strategies"
```

Internally:

```text
Curio
  ↓
Codex (planner/synthesizer)
  ↓
search_kb tool
  ↓
Local KB
```

Important:

Curio should:

- define system prompts
- register tools
- own orchestration semantics

Codex should:

- plan retrieval
- reason over evidence
- synthesize answers

This preserves:

- Codex UX advantages
- deterministic infrastructure
- repeatability
- evolvability

---

# Implementation Plan

## Phase 1 — Minimal Viable KB

Target:

1–3 days

Implement:

- ingestion pipeline
- extraction
- chunking
- embeddings
- metadata generation
- SQLite metadata store
- FAISS vector index
- search_kb tool
- Codex orchestration

Skip:

- ontology systems
- graph ranking
- clustering pipelines
- canonical label registries
- distributed infrastructure

---

## Phase 2 — Quality Improvements

Possible additions:

- rerankers
- cached query plans
- better OCR
- artifact quality scoring
- retrieval evaluation harnesses
- automatic chunk compression
- hybrid BM25/vector retrieval

---

## Phase 3 — Advanced Research Infrastructure

Only if justified later:

- ontology layer
- concept graph
- symbolic reasoning
- graph ranking
- long-term memory systems
- multi-agent retrieval orchestration

---

# Risks and Tradeoffs

## Risk: Over-Reliance on Frontier Models

Potential issues:

- non-determinism
- ranking drift
- hallucinated grouping
- inconsistent synthesis

Mitigations:

- deterministic retrieval
- citations
- structured prompts
- constrained context windows

---

## Risk: Embedding Recall Failures

Mitigation:

- hybrid retrieval
- keyword fallback
- multi-query retrieval

---

## Risk: Premature Over-Engineering

Avoid:

- giant schemas
- ontology-first design
- graph algorithms too early
- distributed infrastructure prematurely

---

# References

## Retrieval-Augmented Generation (RAG)

- https://www.pinecone.io/learn/retrieval-augmented-generation/
- https://platform.openai.com/docs/guides/retrieval
- https://python.langchain.com/docs/concepts/rag/

---

## FAISS

- https://github.com/facebookresearch/faiss
- https://faiss.ai/

---

## BM25 / Hybrid Retrieval

- https://en.wikipedia.org/wiki/Okapi_BM25
- https://weaviate.io/blog/hybrid-search-explained

---

## HDBSCAN (Future Consideration)

- https://hdbscan.readthedocs.io/

---

## OpenAI / Codex

- https://platform.openai.com/docs
- https://github.com/openai/codex

---

## OCR / Extraction

- https://github.com/microsoft/markitdown
- https://tesseract-ocr.github.io/

---

## Knowledge Systems Inspiration

- https://github.com/openclaw/openclaw
- https://github.com/anthropics/claude-code
- https://obsidian.md/
- https://logseq.com/
