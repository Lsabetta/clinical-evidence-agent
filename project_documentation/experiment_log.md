# Experiment Log

This file contains completed experiments and empirical results only.

Do not record expected results here. Hypotheses and planned experiments belong in the relevant task discussion or backlog until the experiment has actually been run.

---

## Experiment template

### EXP-XXX — Title

**Date:**

**Question / hypothesis:**

**Systems compared:**

**Dataset / test cases:**

**Configuration:**

**Metrics:**

**Results:**

**Interpretation:**

**Limitations / confounders:**

**Decision / next action:**


### EXP-001 — V0A prompt smoke validation

**Date:** 2026-09-25

**Question / hypothesis:**

Can the local `qwen3:4b-instruct` model, using the V0A prompt, produce a valid coarse `question_status` classification while V0A application logic deterministically enforces the no-retrieval fields?

**Systems compared:**

Successive V0A prompt revisions during development; final configuration `v0a-005`.

**Dataset / test cases:**

Small manually selected smoke set covering:

- focused biomedical evidence question;
- broad but meaningful biomedical evidence questions;
- genuinely underspecified biomedical question;
- individualized diagnostic request outside project scope.

**Configuration:**

- Ollama local inference.
- Model: `qwen3:4b-instruct`.
- Structured output via Pydantic schema.
- Temperature: 0.
- No external retrieval.

**Metrics:**

- expected vs. generated `question_status`;
- schema validity;
- V0A invariant validity;
- qualitative inspection of summary;
- latency and token counts recorded during manual runs.

**Results:**

The final `v0a-005` prompt produced the expected `question_status` on the final smoke cases.

The V0A pipeline deterministically produced:

- `evidence_status = "not_assessed"`;
- `sources = []`;
- explicit limitation stating that no external biomedical literature was retrieved or verified.

Earlier prompt versions exposed ambiguity in the definition of `well_specified` versus `underspecified` and showed that delegating deterministic V0A fields to the model introduced unnecessary failure modes.

**Interpretation:**

The current V0A prompt and pipeline are adequate for continuing implementation.

The exercise also supported keeping facts known by construction outside model control rather than asking the LLM to reproduce them.

**Limitations / confounders:**

- This is a development smoke test, not an independent benchmark.
- Several examples were used while refining the prompt, so the final pass rate must not be interpreted as generalization performance.
- The dataset is very small.
- Only one local model was tested.
- Medical correctness was not evaluated.

**Decision / next action:**

Freeze `V0A_PROMPT_VERSION = "v0a-005"` for the current baseline.

Do not perform further prompt tuning on these same smoke examples.

Complete the V0A CLI and run logging before starting V0B.

### EXP-002 — Variability in repeated PubMed searches

**Date:** 2026-10-01

**Question / hypothesis:**
Do identical PubMed ESearch requests return the same ordered top-k PMIDs?

**Configuration:**
- Query: `semaglutide AND cardiovascular`
- Database: `pubmed`
- `retmax=3`, `retmode=xml`
- Repeated live requests with `sort=relevance`.
- Follow-up diagnostic with `sort=pub_date`.

**Results:**
Repeated requests with `sort=relevance` returned different top-3 PMIDs.
Two inspected raw XML responses had identical request URLs,
`Count=1602`, `QueryTranslation`, `RetStart=0`, and `RetMax=3`,
but different, non-overlapping PMID lists.
No explicit errors or warnings appeared in those responses.

Fetched PMIDs matched searched PMIDs within each run.

With `sort=pub_date`, the top-3 PMIDs remained unchanged across
the repetitions performed.

**Interpretation:**
The observed variation was already present in the ESearch response,
rather than introduced by our XML parser or record retrieval.
The comparison suggests an association with relevance sorting.
The underlying cause is unknown; unstable ordering of tied scores
is one unverified hypothesis.

**Limitations / confounders:**
Small manual diagnostic using one query and a short observation period.
Relevance scores and server-side state were unavailable.
Stable results with publication-date sorting do not establish
long-term reproducibility.

**Decision / next action:**
Retain `sort=relevance` for the initial baseline.
Preserve retrieved evidence in V0B run logs so synthesis can be
repeated with identical inputs.
Use fixed simulated responses for automated client tests.

### EXP-003 — V0B end-to-end smoke run and grounding failure

**Date:** 2026-10-02

**Question / hypothesis:**
Does the complete V0B CLI workflow execute successfully, preserve its
evidence snapshot, and produce a synthesis faithful to that evidence?

**Systems compared:**
V0B only; no paired V0A comparison in this experiment.

**Dataset / test cases:**
One development question:
"Does melatonin improve sleep in adults with chronic insomnia?"

**Configuration:**
- Model: `qwen3:4b-instruct`, temperature 0.
- Query prompt: `pubmed-query-v003`.
- Synthesis prompt: `v0b-synthesis-v002`.
- Query: `melatonin AND sleep AND "chronic insomnia" AND adult`.
- One live PubMed search, `sort=relevance`, top-k 3.
- Retrieved PMIDs: 27998379, 33164742, 36179487.
- Evidence scope: metadata and abstracts.

**Results:**
- CLI execution and JSONL logging completed successfully.
- The log preserved all three normalized records, draft, and final answer.
- Schema and citation-consistency checks passed.
- Final sources: 27998379 and 36179487.
- Evidence status: `partial`.
- Query generation: 14.684 s; 217 input / 18 output tokens.
- Retrieval: 1.044 s.
- Synthesis: 195.538 s; 2711 input / 343 output tokens.
- Total pipeline latency: 211.268 s.

Manual inspection identified:
- A claim that comorbid insomnia was not assessed, contradicted by
  the supplied abstract of PMID 36179487.
- An overly categorical conclusion about ineffectiveness, losing
  distinctions between populations and statistical findings.
- A limitation describing the evidence as restricted to a systematic
  review despite also citing a clinical practice guideline.

**Interpretation:**
The technical pipeline worked, but the synthesis was not fully faithful
to the supplied evidence. Citation consistency does not establish
semantic support. Most measured latency occurred during synthesis;
the underlying performance cause was not established.

**Limitations / confounders:**
One development question, already used during prompt refinement.
One local model and one live retrieval snapshot.
This is not an independent benchmark or evidence of comparative quality.

**Decision / next action:**
Preserve this run as a development failure case.
Proceed to a shared V0A/V0B smoke benchmark with fixed configurations
and explicit manual review criteria, without further tuning on this case.