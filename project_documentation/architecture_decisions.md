# Architecture Decisions

This document records accepted architectural decisions.

Ideas under discussion are not decisions and belong in chat or `backlog.md`.

---

## ADR-001 — Build incrementally from non-agentic to agentic systems

**Status:** Accepted

### Decision

Develop the system incrementally, maintaining simpler implementations as baselines rather than starting directly from a complex agent architecture.

### Rationale

The project is intended both as a learning exercise and as an empirical study of whether added agency provides measurable value.

Without simpler baselines, improvements from agentic components cannot be properly evaluated.

---

## ADR-002 — Implement the first agent loop without an orchestration framework

**Status:** Accepted

### Decision

The first tool-using agent loop will be implemented directly in Python using the model/tool-calling API before implementing the equivalent workflow with LangGraph.

### Rationale

The goal is to understand state transitions, tool dispatch, termination, failure handling, and the model/application boundary before delegating those mechanisms to a framework.

### Revisit when

The manual agent loop is functional and its behaviour is understood.

---

## ADR-003 — PubMed is the initial biomedical evidence source

**Status:** Accepted

### Decision

The MVP will initially use PubMed as its external biomedical evidence source.

ClinicalTrials.gov, synthetic FHIR data, and other sources are deferred.

### Rationale

PubMed provides a realistic biomedical retrieval problem while keeping the initial tool surface small and avoiding private clinical data.

### Revisit when

The PubMed-based core system and its evaluation framework are stable.

---

## ADR-004 — Multi-agent systems are not part of the initial architecture

**Status:** Accepted

### Decision

Do not introduce multi-agent orchestration until simpler baselines and the single-agent/tool-using system have been evaluated.

### Rationale

Multi-agent systems introduce additional cost, nondeterminism, orchestration complexity, and failure modes. They should be introduced only if an experiment tests a concrete hypothesis about their benefit.

---

## ADR-005 — Use a local LLM for initial development

**Status:** Accepted

### Decision

Use Ollama with a small local model for the initial V0/V1 development
path, while keeping the LLM provider isolated behind a small application
interface.

The current development model is `qwen3:4b-instruct`.

The provider/model choice is not part of the permanent architecture
and may be revisited for later evaluation.

### Rationale

The project is intended to be developed without recurring API costs.

A local model is sufficient for learning and implementing the core
mechanisms currently under study:

- structured outputs;
- model/application boundaries;
- retrieval pipelines;
- tool calling;
- agent loops;
- state and orchestration;
- logging and evaluation infrastructure.

Provider isolation preserves the ability to evaluate a stronger hosted
model later without rewriting the surrounding pipeline.

A small local model may itself be a significant source of error and
therefore should not automatically be treated as representative of
stronger production models when interpreting later benchmark results.

### Revisit when

- model capability materially blocks an experiment;
- tool-calling reliability becomes inadequate;
- final portfolio/evaluation results require comparison with a stronger model;
- a suitable zero-cost or acceptably low-cost alternative becomes available.

---

## ADR-006 — Use one-shot LLM query generation in V0B

**Status:** Accepted

### Decision

V0B uses a fixed, non-agentic workflow:

1. Generate one structured PubMed query from the original question
   using an LLM and a versioned prompt.
2. Execute one PubMed search.
3. Fetch and normalize up to the configured top-k records.
4. Generate one structured synthesis from the original question
   and the retrieved evidence.
5. Validate citation consistency and build the final answer.

Application code controls the sequence. The model cannot choose
additional searches, revise the query after retrieval, or retry tools.

The raw-question query builder is retained as a minimal comparator.
Question-specific prefix-stripping rules are not part of the baseline.

### Rationale

Passing a complete natural-language question directly to PubMed can
introduce unintended search constraints. Development examples showed
that words such as "evidence" and "exists" became required search terms.

A single query-generation call addresses this interface problem without
introducing an agentic loop or hand-written rules for particular questions.

This provides a stronger baseline for investigating whether adaptive
retrieval adds value.

### Reproducibility and evaluation

Fixed control flow does not guarantee identical LLM outputs or live
PubMed results, even with fixed configuration.

Record prompt versions, model configuration, generated query, ordered
retrieved records, synthesis output, latency, and token usage.

Evaluate query fidelity separately from retrieval relevance and synthesis
grounding. Citation-consistency validation does not verify semantic support.

For later V0B/V1 comparisons, reuse query-generation and synthesis
components where applicable, and report differences in retrieval budgets
and model configuration. Improvements must not be attributed to agency
when other components changed without being controlled or reported.

### Scope

Iterative query revision, repeated searches, adaptive evidence selection,
and model-controlled stopping remain outside V0B.