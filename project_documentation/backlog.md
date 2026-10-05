# Project Backlog

Items in this file are ideas or possible future work.

They are **not** accepted architectural decisions and are **not** part of the current milestone unless explicitly promoted through a project decision.

## Healthcare extensions

- ClinicalTrials.gov integration.
- Synthetic patient records using Synthea / FHIR.
- Combine structured patient information with evidence retrieval.
- Human-in-the-loop review of selected evidence.

## Agentic experiments

- Compare single-agent vs multi-agent architectures.
- Dedicated research / synthesis / verification agents.
- Alternative retry/reflection strategies.
- Long-term or persistent memory, only if a concrete use case emerges.
- Compare LangGraph with another agent runtime/SDK.

## Retrieval experiments

- Query rewriting strategies.
- Reranking.
- Hybrid retrieval approaches.
- Additional biomedical literature sources.
- Vector database, only if a demonstrated retrieval requirement justifies it.

## Product / portfolio

- Web UI.
- Streamlit/Gradio demo.
- Architecture visualization.
- Interactive trace viewer.
- Public hosted demo.

## Possible research questions

- When does agent-controlled retrieval outperform deterministic retrieval?
- Does iterative search improve recall enough to justify additional cost?
- Does a verifier measurably reduce unsupported claims?
- Which failure modes increase as model autonomy increases?
- Does multi-agent decomposition improve quality over a simpler workflow?
