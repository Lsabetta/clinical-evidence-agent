# Current Project State

## Current milestone

V0B — fixed one-shot PubMed workflow.
Core implementation operational; comparative smoke evaluation pending.

## Current objective

Evaluate V0B against the frozen V0A baseline using a shared smoke
benchmark, recording query fidelity, retrieval relevance, grounding,
citation correctness, latency, and token usage.

V0 still consists of two non-agentic baselines:

- **V0A:** LLM-only structured answer, with no external retrieval.
- **V0B:** one LLM-generated PubMed query, one PubMed search, batch
  retrieval of up to top-k records, and one LLM synthesis call.

Both accept the same natural-language question and return the same
`EvidenceAnswer` schema.

V0B has fixed application control flow. It does not revise queries,
repeat searches, or use an agentic loop. Fixed control flow does not
guarantee identical model outputs or live PubMed results.

## Implemented

### Repository and environment

- Git repository initialized and connected to GitHub.
- Python 3.12 environment managed with `uv`.
- `src/` package layout configured.
- pytest configured for automated tests.
- Local inference configured with Ollama using `qwen3:4b-instruct`.

### Structured output

- `Source` Pydantic model implemented.
- `EvidenceAnswer` Pydantic model implemented.
- `QuestionStatus` values:
  - `well_specified`
  - `underspecified`
  - `out_of_scope`
- `EvidenceStatus` values:
  - `sufficient`
  - `partial`
  - `insufficient`
  - `not_assessed`
- Schema validation tests implemented.

### LLM layer

- Provider-specific Ollama access isolated in `llm.py`.
- `generate_structured_answer()` accepts an arbitrary Pydantic output schema.
- LLM calls record:
  - model identifier;
  - latency;
  - input token count when available;
  - output token count when available.

### V0A pipeline

- `run_v0a(question)` implemented.
- Empty/whitespace-only questions are rejected deterministically.
- The LLM generates only:
  - `question_status`;
  - `summary`.
- V0A application logic deterministically sets:
  - `evidence_status = "not_assessed"`;
  - `sources = []`;
  - the limitation that no external biomedical literature was retrieved or verified.
- Current prompt version: `v0a-005`.
- Automated V0A tests use a mocked LLM call so they remain fast and deterministic.
- A separate manual smoke script exercises the real local model.
- Smoke cases currently cover:
  - focused biomedical evidence questions;
  - broad but answerable evidence questions;
  - genuinely underspecified questions;
  - out-of-scope individualized diagnostic requests.
- CLI entry point implemented through the project script.
- CLI emits the validated `EvidenceAnswer` as JSON.
- V0A run records are persisted as JSONL.
- Run records include:
  - timestamp;
  - input question;
  - prompt version;
  - model identifier;
  - latency;
  - input/output token counts;
  - schema-validation status;
  - validated answer;
  - error type/message when applicable.
- Validation failures and other runtime exceptions are logged separately.
- Final automated test suite passes.
- Final real-model CLI smoke run completed successfully with `v0a-005`.
- V0A is frozen as the permanent LLM-only baseline.
  
### V0B retrieval layer

- `PubMedRecord` schema implemented.
- `parse_pubmed_article()` normalizes article XML.
- `get_pubmed_records()` retrieves records in a batch, preserves
  requested order, removes duplicate input PMIDs, and raises an error
  if requested records are missing.
- `search_pubmed()` performs one ESearch request with explicit
  `sort=relevance`.
- Live search-to-record retrieval exercised successfully.
- 10 offline PubMed tests reported passing.

### V0B query generation and synthesis

- `generate_pubmed_query()` produces a structured `PubMedQuery`
  through one LLM call.
- Query prompt version: `pubmed-query-v003`.
- The raw-question query builder is retained as a minimal comparator;
  it is not used by the main V0B pipeline.
- `synthesize_v0b()` receives the original question and the retrieved
  records, and produces a structured `V0BDraft`.
- Synthesis prompt version: `v0b-synthesis-v002`.
- The model declares cited PMIDs; application code builds `Source`
  objects from retrieved metadata.
- Citation validation rejects unavailable PMIDs, duplicate declared
  PMIDs, and mismatches between recognized inline citations and
  declared PMIDs.
- These checks do not verify semantic support or ensure that every
  substantive claim has a citation.
- Application code adds limitations describing abstract-only evidence
  and the one-search/top-k retrieval scope.

### V0B orchestration, CLI, and logging

- `run_v0b()` implements the fixed query/search/fetch/synthesis workflow.
- Blank questions and invalid top-k values are rejected before
  external calls.
- CLI supports `--pipeline v0a|v0b` and `--top-k`; V0A remains the default.
- Successful V0B runs are saved to `runs/v0b.jsonl`.
- Logs preserve the generated query, ordered evidence snapshot,
  structured draft, final answer, prompt versions, model identifiers,
  token usage, and stage/total latency.
- `V0BTrace` and `V0BRunError` preserve completed stage results when
  a pipeline stage fails.
- The CLI logs failures with their stage, original error, and partial
  results before re-raising the exception.
- Invalid raw LLM responses are not currently preserved when structured
  parsing fails.
- Offline tests cover citation checks, answer construction, successful
  orchestration/logging, and CLI logging after a simulated fetch failure.
- A real end-to-end CLI run completed successfully on 2026-10-02.

### Known limitations and observed failures

- Query generation has shown fidelity errors, including mishandled
  exclusion criteria.
- Identical live ESearch requests with `sort=relevance` have returned
  different top-k results; the cause has not been established.
- The 2026-10-02 melatonin run passed schema and citation-consistency
  checks but contained unsupported or contradicted synthesis claims.
- In particular, the synthesis incorrectly stated that comorbid
  insomnia was not assessed, despite its presence in the supplied
  meta-analysis abstract, and overstated the conclusion about efficacy.
- That run took approximately 211.3 seconds: 14.7 seconds for query
  generation, 1.0 second for retrieval, and 195.5 seconds for synthesis.
- Technical execution success does not establish answer correctness.
- The shared V0A/V0B smoke benchmark has not yet been completed.

## Current scope

The project follows `project_strategy.md`.

The initial domain is biomedical evidence retrieval, with PubMed as the first external evidence source.

No agent framework or agentic architecture has been implemented yet.

## Accepted constraints

- Start simple and add agency incrementally.
- Preserve meaningful baselines for later comparison.
- Implement the first tool-using agent loop manually before relying on an orchestration framework.
- Do not introduce multi-agent architecture before simpler approaches have been implemented and evaluated.
- Do not use real private patient data.
- V0A and V0B must accept the same user-facing input and return the same top-level output schema.
- V0B does not need to outperform V0A to be considered complete; whether retrieval improves quality is an experimental question, not a Definition of Done requirement.

## V0 input

V0A and V0B accept the same input:

```text
question: str
```

The question must be a non-empty natural-language biomedical evidence-research question.

The V0 interface does not require structured PICO fields or patient records. Diagnostic reasoning over individual patient symptoms is outside the current scope.

## V0 output schema

V0A and V0B return a common structured output represented by `EvidenceAnswer`.

### `question_status`

Indicates whether the input question is sufficiently specified to support a meaningful evidence-oriented answer.

Allowed values:

- `well_specified`
- `underspecified`
- `out_of_scope`

This describes the quality/scope of the input question, not the amount or quality of evidence retrieved.

### `evidence_status`

Indicates whether the evidence actually available to the system during the current run is sufficient to support the answer.

Allowed values:

- `sufficient`
- `partial`
- `insufficient`
- `not_assessed`

For V0A, which performs no external evidence retrieval, `evidence_status` must be `not_assessed`.

### `summary`

A concise natural-language answer to the user's question.

It should contain:

- the main conclusion;
- the main evidence or reasoning supporting that conclusion.

It must not present information as externally verified if that information was not available to the system during the run.

For V0B, the summary must be grounded only in the PubMed evidence actually retrieved.

### `sources`

The external sources actually used to support the answer.

Each source contains:

- `pmid`: required;
- `pmcid`: optional;
- `title`: required;
- `url`: required.

For V0A, `sources` must be an empty list.

Retrieved records that are not actually used to support the final answer should not automatically appear in `sources`.

### `limitations`

A list of specific factors that reduce the strength, completeness, or interpretability of the answer.

Examples include:

- no external evidence retrieval;
- retrieval limited to the top-k PubMed results;
- possible relevant studies not retrieved;
- abstract-only evidence when full text was unavailable;
- heterogeneous study populations, interventions, or outcomes;
- conflicting evidence;
- insufficient evidence for a robust conclusion.

`limitations` should describe limitations of the answer or available evidence, not serve as a generic execution log.

## V0 measurements and logging

### V0A

Record at least:

- input question;
- model identifier/configuration needed for reproducibility;
- prompt or prompt version;
- raw model output where useful for debugging;
- validated `EvidenceAnswer`;
- latency;
- token usage and estimated cost when available;
- schema-validation success/failure.

### V0B

Record all V0A measurements plus:

- LLM-generated PubMed query and query-generation prompt version;
- requested `top_k` / maximum number of results;
- PMIDs returned by PubMed;
- number of records successfully retrieved and normalized;
- which retrieved records were actually cited in `sources`;
- PubMed/tool latency separately from LLM latency where practical.
- explicit PubMed sort parameter;
- the complete ordered list of normalized `PubMedRecord` objects
  actually supplied to the synthesis model, including available abstracts,
  so synthesis can be repeated without rerunning live retrieval.

These measurements are process observability data and should not be conflated with `EvidenceAnswer.limitations`.
Repeated live ESearch requests with identical parameters and
`sort=relevance` have returned different top-k PMIDs (EXP-002).

V0B fixes the application’s retrieval procedure, but does not assume
identical results from repeated live PubMed searches.
Evidence snapshot logging is implemented for successful retrieval.
Failure logs preserve results from stages completed before the error.

Query-generation and synthesis calls record their latency and token
usage separately. Retrieval and total pipeline latency are also logged.

Validation flags describe mechanical checks, not semantic grounding.
Unavailable validation results are recorded as null.

## V0 success criteria / Definition of Done

### V0A — LLM-only baseline

V0A is complete when:

- a CLI or equivalent entry point accepts a non-empty biomedical evidence question;
- the system performs no external evidence retrieval;
- the model returns output that validates as `EvidenceAnswer`;
- `sources == []`;
- `evidence_status == not_assessed`;
- the answer does not claim that external literature was searched or verified;
- required run measurements are logged;
- basic automated tests cover schema validation and the V0A invariants above.

V0A is a behavioral and measurement baseline; medical correctness is not a completion criterion at this stage.

### V0B — Fixed one-shot PubMed baseline

V0B is complete when:

- it accepts the same input format and returns the same `EvidenceAnswer` schema as V0A;
- it generates one structured PubMed query using a versioned LLM prompt and fixed configuration, without iterative revision;
- exactly one PubMed search is performed in a successful run, with no search retries or iterative retrieval;
- the configured top-k records are retrieved and normalized when available;
- synthesis uses only evidence actually retrieved during that run;
- `sources` contains only retrieved records actually used to support the final answer;
- the answer does not claim support from full text unless full text was explicitly retrieved and available to the system;
- query, PMIDs, retrieval metadata, latency, token usage, and schema-validation status are logged;
- basic automated tests cover query-generation integration, retrieval normalization, schema validity, citation consistency, orchestration, and preservation/logging of partial results on failure.
V0B does **not** need to outperform V0A to satisfy its Definition of Done.
Grounding and actual citation support require manual evaluation.
Passing schema and citation-consistency checks does not establish
that these behavioral requirements are satisfied.
## Smoke benchmark for baseline validation

Before using V0A and V0B as experimental baselines, create a small manually curated smoke benchmark of approximately 10 biomedical evidence questions.

The benchmark should include a mix of:

- focused questions with relatively clear evidence;
- underspecified or heterogeneous questions;
- questions with potentially conflicting evidence;
- questions with limited evidence;
- sufficiently specific or recent questions that may expose weaknesses of an LLM-only answer.

For the smoke benchmark, manually inspect at least:

- **query fidelity:** whether the V0B PubMed query represents the user's intended question rather than a materially different one;
- **retrieval relevance:** whether retrieved records are pertinent to the question;
- **grounding:** whether V0B claims are supported by the retrieved evidence;
- **citation correctness:** whether cited sources actually support the associated answer content.

Where feasible, annotate reference-relevant PMIDs and expected key claims, but a full gold-standard benchmark is deferred to the later evaluation phase.

The initial V0A-vs-V0B comparison is exploratory. A failure of V0B to improve over V0A is a valid experimental result and should trigger analysis of query construction, retrieval, synthesis, and benchmark design rather than being treated as an implementation failure.

## Open questions

No unresolved architectural decision currently blocks V0B evaluation.

The one-shot LLM query-generation decision is recorded in ADR-006
and reflected in the project strategy.

Remaining empirical questions include query fidelity, retrieval relevance,
synthesis grounding, and whether retrieval improves answers over V0A.

Iterative query revision, repeated retrieval, reranking, and agent-controlled
tool use remain outside V0B.

## Next deliverable

Prepare and run the shared V0A/V0B smoke benchmark:

1. Align project documentation with the implemented one-shot workflow.
2. Remove retrieval diagnostic prints from CLI standard output, if still
   present, so successful CLI output is a single JSON object.
3. Define approximately 10 questions and a common manual review rubric.
4. Mark questions already used for prompt development as development cases.
5. Fix model configuration, prompt versions, and top-k for the comparison.
6. Run both baselines and preserve run logs and V0B evidence snapshots.
7. Review query fidelity, retrieval relevance, grounding, and citation
   correctness alongside latency and token usage.
8. Record observed failures without tuning prompts on the evaluation set
   during the comparison.