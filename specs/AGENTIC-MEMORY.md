# Agentic Memory Architecture

## Current Status

This document is retained as a starting-point discussion artifact. The normative
Curio KB decision is now [KB.md](/Users/zeph/github/tzaffi/curio/specs/KB.md).

The core tiering idea below still stands, but it needs three corrections:

- Curio's KB should be evidence-first, not memory-system-first. The canonical
  base is exact artifacts, dossier snapshots, evaluations, and source lineage.
- Semantic memory is broader than vector search. It includes chunks, claims,
  entity mentions, memory notes, summaries, lexical indexes, embeddings, and
  graph overlays.
- Derived memories are not ground truth. Summaries, graph communities, note
  links, and vector indexes must remain rebuildable from canonical evidence.

## Executive Summary

Curio should implement a hybrid agentic memory architecture rather than relying on a single memory paradigm such as:

- pure vector databases
- pure markdown/wiki memory
- pure episodic logs
- pure graph memory
- monolithic "memory operating systems"

Current industry sentiment strongly favors composable hybrid systems that combine:

1. episodic logs
2. semantic retrieval
3. structured state
4. curated long-term knowledge
5. summarization/consolidation pipelines

The recommended architecture for Curio is:

```text
Raw Events / Artifacts
    ↓
Episodic Memory Store
    ↓
Consolidation Pipeline
    ↓
Hybrid Retrieval Layer
    ├── Vector Memory
    ├── Structured State Memory
    └── Curated Wiki Memory
```

This design aligns well with:

- OpenClaw-style autonomous agent execution
- Hermes routing/orchestration
- local-first operation
- human-debuggable workflows
- deterministic state handling
- long-running agent sessions

The key architectural principle is:

> Semantic memory should never be treated as ground truth state.

Instead:

- vector memory is for fuzzy recall
- structured memory is for facts/state
- markdown/wiki memory is for durable curated knowledge
- episodic memory is for reconstruction and summarization

---

# Goals

The memory system should:

- support long-running autonomous agents
- support local-first operation
- remain human-debuggable
- support deterministic state handling
- avoid context window explosion
- support future model routing
- support memory consolidation and summarization
- support retrieval ranking improvements over time
- support multi-modal artifacts

Non-goals:

- full AGI-style memory simulation
- opaque self-modifying memory
- replacing deterministic databases with embeddings

---

# Research Findings

## 1. Industry Sentiment Has Shifted Away From Pure Vector Memory

Early agent systems heavily relied on vector databases.

Typical architecture:

```text
Agent → Embed → Store → Semantic Search → Prompt
```

Problems discovered:

- embedding drift
- poor chunk retrieval
- retrieval instability
- lack of deterministic state
- inability to distinguish importance
- “bag of memories” failure mode

Current sentiment:

> Vector memory is necessary but insufficient.

Vector search should be treated as:

- semantic recall
- contextual augmentation
- fuzzy search

NOT:

- authoritative state
- reliable memory correctness

---

## 2. Markdown / Wiki Memory Remains Extremely Valuable

Karpathy-style markdown/wiki memory remains popular because it provides:

- transparency
- editability
- git versioning
- human oversight
- deterministic instructions

Typical use cases:

- system prompts
- operational rules
- tool documentation
- curated knowledge
- high-value summaries

Weaknesses:

- manual maintenance
- poor automatic retrieval
- difficult scaling

Current consensus:

> Wiki memory works best as curated long-term memory layered on top of automated retrieval systems.

---

## 3. Structured Memory Is Making A Comeback

Many advanced agent builders are returning to:

- SQLite
- JSON state
- graph databases
- typed schemas
- event sourcing

Reason:

Deterministic state matters.

Examples:

- task status
- workflow progress
- routing metadata
- portfolio state
- user preferences
- configuration

Embeddings are poor replacements for these workloads.

Current consensus:

> Important state should be stored structurally.

---

## 4. Episodic Memory Is Increasingly Important

Modern agent systems increasingly separate:

- raw events
- summarized memory
- curated memory

This mimics:

- human episodic memory
- replay systems
- event sourcing

Advantages:

- auditability
- replayability
- better summarization
- memory compression
- future retraining opportunities

Typical pipeline:

```text
Raw Event
    ↓
Short-term Context
    ↓
Periodic Consolidation
    ↓
Long-term Semantic Memory
```

---

## 5. Unified “Memory Operating Systems” Are Promising But Immature

Systems like gbrain attempt to unify:

- vector memory
- episodic memory
- summarization
- retrieval ranking
- consolidation

Advantages:

- cleaner abstraction
- less plumbing
- easier experimentation

Weaknesses:

- opaque retrieval behavior
- difficult debugging
- immature ecosystem
- uncertain scaling properties
- risk of lock-in

Current sentiment:

> Unified memory systems are directionally correct but not yet sufficiently battle-tested to replace composable architectures.

---

# Suggested Design

## High-Level Architecture

```text
                   ┌───────────────────────┐
                   │  Raw Events / Media   │
                   └──────────┬────────────┘
                              │
                              ▼
                   ┌───────────────────────┐
                   │ Episodic Event Store  │
                   └──────────┬────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌────────────────────┐      ┌────────────────────┐
    │ Consolidation Jobs │      │ Structured State   │
    │ Summaries / Tags   │      │ SQLite / JSON      │
    └──────────┬─────────┘      └────────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │ Semantic Memory Layer       │
    │ Embeddings / Vector Search  │
    └──────────┬──────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │ Curated Wiki Memory         │
    │ Markdown / Specs / Notes    │
    └─────────────────────────────┘
```

---

## Core Principle: Memory Tiering

Different memory types solve different problems.

| Memory Type | Purpose           | Storage          | Reliability |
| ----------- | ----------------- | ---------------- | ----------- |
| Episodic    | Raw history       | Append-only logs | High        |
| Semantic    | Fuzzy recall      | Vector DB        | Medium      |
| Structured  | Facts/state       | SQLite/JSON      | Very High   |
| Wiki        | Curated knowledge | Markdown/git     | Very High   |

---

## Recommended Components

### 1. Episodic Memory Layer

Recommended implementation:

- append-only event log
- JSONL or SQLite-backed
- immutable artifacts
- timestamped events

Store:

- prompts
- responses
- tool calls
- retrieved documents
- execution traces
- routing decisions
- media artifacts

Potential future features:

- replay
- debugging
- training data generation
- memory importance scoring

---

### 2. Structured State Layer

Recommended implementation:

- SQLite first
- typed schemas
- deterministic state transitions

Store:

- workflow state
- task queues
- routing preferences
- agent configuration
- execution metadata
- durable facts

Avoid storing critical state only in embeddings.

---

### 3. Semantic Memory Layer

Recommended implementation:

- local embeddings
- FAISS or Chroma
- reranking support
- chunk metadata

Recommended retrieval pipeline:

```text
Query
  ↓
Embedding Search
  ↓
Metadata Filtering
  ↓
Reranker
  ↓
Prompt Assembly
```

Important:

- retrieval quality matters more than embedding quality
- reranking is increasingly considered mandatory
- chunking strategy heavily impacts quality

Potential future improvements:

- hybrid BM25 + embeddings
- learned retrieval ranking
- temporal weighting
- importance decay

---

### 4. Curated Wiki Layer

Recommended implementation:

- markdown files
- git versioning
- human-editable specs

Store:

- operational procedures
- agent policies
- system prompts
- architecture notes
- curated summaries
- high-signal distilled knowledge

This layer should remain intentionally human-readable.

---

# Suggested Retrieval Flow

## Example Retrieval Pipeline

```text
User Request
    ↓
Task Classification
    ↓
Determine Needed Memory Types
    ├── Structured State?
    ├── Semantic Recall?
    ├── Wiki Knowledge?
    └── Episodic Replay?
    ↓
Retrieve + Rerank
    ↓
Assemble Context
    ↓
Execute Agent Step
```

This avoids:

- over-fetching
- irrelevant semantic noise
- context flooding
- hallucinated memory retrieval

---

# Suggested Consolidation Pipeline

## Memory Consolidation Jobs

Periodic background jobs should:

1. summarize episodic logs
2. extract entities/topics
3. generate semantic chunks
4. update vector memory
5. promote high-signal summaries into wiki memory

Example:

```text
Conversation Logs
    ↓
Summarization
    ↓
Entity Extraction
    ↓
Embedding Generation
    ↓
Semantic Storage
```

---

# Local-First Considerations

Curio should prioritize:

- offline capability
- local embeddings
- local vector DB
- local markdown storage
- SQLite over distributed infra initially

Avoid early complexity:

- distributed vector systems
- cloud-only memory services
- heavyweight graph infrastructure

The initial implementation should optimize for:

- reliability
- debuggability
- iteration speed

---

# Suggested Initial Stack

## Phase 1

Recommended technologies:

| Component        | Recommendation              |
| ---------------- | --------------------------- |
| Structured State | SQLite                      |
| Episodic Memory  | JSONL or SQLite             |
| Vector Search    | FAISS                       |
| Embeddings       | local sentence transformers |
| Curated Memory   | Markdown                    |
| Reranking        | cross-encoder reranker      |

---

## Phase 2

Potential upgrades:

- hybrid BM25 retrieval
- graph memory overlays
- memory importance scoring
- temporal decay
- retrieval analytics
- automated memory pruning
- learned reranking

---

# Implementation Priorities

## Priority 1

Build deterministic foundations first:

- episodic logging
- structured state
- markdown memory

## Priority 2

Add semantic retrieval:

- embeddings
- chunking
- reranking

## Priority 3

Add consolidation:

- summarization
- entity extraction
- memory promotion

## Priority 4

Experiment with advanced memory systems:

- graph overlays
- agent-generated memory
- self-healing retrieval
- memory scoring

---

# Anti-Patterns To Avoid

## Avoid Embedding Everything

Not all information belongs in vector search.

Critical state should remain structured.

---

## Avoid Opaque Memory Mutation

Agents should not freely rewrite durable memory without traceability.

All mutations should be:

- logged
- inspectable
- reversible

---

## Avoid Massive Context Dumps

Retrieval quality matters more than retrieval quantity.

Prefer:

- reranking
- filtering
- task-aware retrieval

Over:

- dumping hundreds of chunks into prompts

---

# Recommended Future Research

Areas worth exploring later:

- retrieval-aware fine tuning
- memory scoring heuristics
- graph-enhanced retrieval
- long-horizon task memory
- reinforcement-learned retrieval
- hierarchical memory
- multi-agent shared memory

---

# References

## General Memory Systems

- https://www.anthropic.com/engineering/building-effective-agents
- https://lilianweng.github.io/posts/2023-06-23-agent/
- https://arxiv.org/abs/2304.03442
- https://arxiv.org/abs/2308.15022

## Vector Search / Retrieval

- https://github.com/facebookresearch/faiss
- https://www.trychroma.com/
- https://www.pinecone.io/learn/retrieval-augmented-generation/
- https://huggingface.co/sentence-transformers

## Reranking

- https://www.sbert.net/examples/applications/retrieve_rerank/README.html
- https://www.cohere.com/retrieval

## Markdown / Wiki Memory

- https://obsidian.md/
- https://github.com/langchain-ai/langmem

## Event Sourcing / Episodic Concepts

- https://martinfowler.com/eaaDev/EventSourcing.html
- https://www.cqrs.com/event-sourcing/

## Graph / Structured Memory

- https://neo4j.com/developer/knowledge-graph/
- https://www.sqlite.org/index.html

## Local Agent Ecosystem

- https://ollama.com/
- https://github.com/open-webui/open-webui
- https://github.com/microsoft/autogen

## Long Context / Agent Research

- https://arxiv.org/abs/2310.08560
- https://arxiv.org/abs/2309.07864
