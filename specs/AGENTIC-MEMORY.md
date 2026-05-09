# Agentic Memory Architecture

## Requirements

Curio's KB should be an agent-neutral, evidence-grounded,
write-time-synthesized knowledge layer. It should work beside arbitrary agents
and harnesses rather than replacing their native memory systems. The KB may
support many contributing agents, but canonical shared knowledge should be
governed by a librarian process.

The terms `MUST`, `SHOULD`, `MAY`, and `MUST NOT` are used in the RFC sense.

### Simplicity

The KB MUST be as simple as possible while still satisfying the core evidence,
governance, and usability requirements.

When requirements conflict, Curio SHOULD prefer the simpler design unless the
more complex design is clearly needed for correctness, auditability, or agent
interoperability.

### Agent-Neutral Interoperability

The KB MUST work alongside arbitrary agents, tools, and harnesses.

The KB MUST NOT require Curio to replace an agent runtime's native memory
system.

Agents SHOULD be able to read from the KB through stable tool, CLI, or MCP-style
interfaces.

Agents MAY keep their own private or native memories, but those memories MUST
NOT be treated as canonical KB state unless explicitly promoted through the KB's
governance process.

### Ownership And Governance

The KB MUST support agent-owned work areas for drafts, provisional findings,
source notes, experiments, and proposed edits.

The KB as a whole SHOULD be governed by a special librarian role. The librarian
owns canonical synthesis, deduplication, contradiction handling, and integration
across independent agent findings.

The KB SHOULD include an auditor role. The auditor owns trust certification,
source verification, workflow verification, proposed-change approval, and
generated-evidence audit policy.

A single human or agent MAY play multiple roles, but the KB model SHOULD keep
contributor, curator, librarian, and auditor responsibilities conceptually
separate. A librarian MAY also act as an auditor only when explicitly certified
for that role.

### Trust And Certification

The KB MUST distinguish trusted canonical knowledge from unreviewed agent
output.

Untrusted or uncertified agents MAY propose changes, but they MUST NOT mutate
canonical shared knowledge directly.

Only the auditor role SHOULD certify agents, sources, workflows, or proposed
changes as trusted.

Findings MUST NOT become canonical shared knowledge unless approved by an
auditor policy.

The auditor policy MAY grant automatic approval for low-impact findings,
trusted agent carveouts, trusted source classes, or reproducible workflows.

Reproducible evidence MAY reduce required audit depth, but it MUST NOT bypass
the audit policy.

### Evidence Provenance

Canonical findings MUST trace to primary evidence whenever possible.

Primary evidence MAY be external source material, such as papers, repos,
webpages, transcripts, datasets, or images.

Primary evidence MAY also be generated evidence, such as backtest reports,
benchmark results, model evaluations, simulations, experiments, or human-authored
observations.

The KB MUST distinguish primary evidence from curator audit trails. Curator
audit trails record how a finding was discovered, processed, summarized,
proposed, or verified.

Curator audit trails MAY include Curio dossier/evaluation payloads, agent logs,
tool-call traces, retrieval transcripts, experiment notebooks, librarian
synthesis records, or auditor verification records.

Curator audit trails MUST NOT be treated as primary evidence unless the curator
artifact itself is the subject of the finding.

### Generated Evidence

The KB MUST support canonical findings derived from generated evidence.

Generated evidence MUST include enough reproducibility metadata to audit the
finding. This SHOULD include input data references, code or method version,
parameter configuration, execution timestamp, result artifacts, and environment
metadata where relevant.

Generated evidence SHOULD be independently verifiable by a librarian, auditor,
or repeat run before it becomes canonical when the finding affects important
decisions.

Generated evidence MAY require deeper audit, including code review, input data
verification, parameter review, or independent rerun.

### Write-Time Synthesis

The KB SHOULD synthesize most durable findings at write time.

Runtime retrieval SHOULD be used to find, verify, and contextualize knowledge,
not to redo expensive synthesis on every query.

The KB MUST NOT allow write-time summaries to replace primary evidence.
Summaries must preserve citations or links sufficient to audit, rebuild, and
challenge the synthesized finding.

### Timeless And Time-Sensitive Knowledge

The KB SHOULD support both timeless knowledge and time-sensitive knowledge.

Timeless knowledge SHOULD be optimized for durable synthesis, stable concepts,
and long-lived pages or records.

Time-sensitive knowledge SHOULD carry source dates, discovery dates, review
dates, freshness status, and stale-or-superseded markers when relevant.

If supporting time-sensitive knowledge substantially increases complexity, Curio
MAY optimize the initial KB for timeless knowledge and rely on explicit refresh,
flush, or re-research workflows for fast-moving domains.

### Human-Grokkable Representation

The KB MUST be human-grokkable either natively or through a reproducible
projection.

The projection MUST be browseable, searchable, and usable without requiring an
agent to interpret it.

The human-readable representation SHOULD expose citations, ownership,
freshness/staleness status, and review state.

### Versioning And Rollback

The KB MUST be versioned and rollbackable.

A local git-backed snapshot system is sufficient for v1.

The KB SHOULD support daily or hourly snapshots if finer-grained semantic
versioning is not implemented.

Canonical changes SHOULD preserve enough history to identify what changed, who
or what proposed it, what evidence supported it, and when it was accepted.

### Cost And Runtime Efficiency

The KB MUST have understandable LLM cost behavior.

The KB SHOULD prefer write-time synthesis and cheap runtime lookup over repeated
expensive runtime synthesis.

The KB SHOULD make major cost classes visible, including ingestion cost,
synthesis cost, verification cost, indexing cost, and query-time cost.

The KB MUST record LLM usage for KB operations when available, including model
name, provider, input tokens, cached input tokens, output tokens, total tokens,
and estimated monetary cost.

The KB SHOULD record wall-clock runtime, storage size, artifact counts, index
sizes, and operation success or failure status.

Cost reporting SHOULD be attributable to operation type, such as ingestion,
synthesis, audit, indexing, retrieval, and query answering.

### CLI, MCP, And Tool Access

The KB SHOULD provide a CLI or MCP interface unless the chosen architecture
makes that unnecessary.

At minimum, agents SHOULD have deterministic ways to search, read canonical
findings, inspect provenance, propose changes, and retrieve cited evidence.

### Health Checks

The KB SHOULD support health checks or linting.

Health checks SHOULD detect missing citations, stale findings, contradictions,
orphan pages, duplicate concepts, unreviewed proposed changes, oversized pages,
and findings without primary evidence.

Health checks MAY be run by the librarian, auditor, CI, a scheduled job, or a
manual CLI command.

### Existing Libraries And Academic Grounding

The KB SHOULD prefer academically grounded designs over popularity-driven or
vibe-driven systems.

When no mature academic gold standard exists, the KB SHOULD prefer designs that
are supported by strong papers, strong empirical benchmarks, or respected AI
practitioners.

The KB SHOULD consider popular open-source libraries when they reduce complexity
without compromising evidence provenance, governance, human readability, or
agent-neutral interoperability.

The KB MUST NOT adopt a memory library merely because it is popular if doing so
would force Curio into an opaque, hard-to-audit, or agent-runtime-specific
design.

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
