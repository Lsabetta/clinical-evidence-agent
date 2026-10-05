# V0A/V0B exploratory smoke benchmark

## Configuration

- Dataset: eval/questions.jsonl, Q01–Q10.
- Model: qwen3:4b-instruct.
- Temperature: 0.
- V0A prompt: v0a-005.
- V0B query prompt: pubmed-query-v003.
- V0B synthesis prompt: v0b-synthesis-v002.
- V0B top-k: 3.
- PubMed sort: relevance.
- One execution per question and pipeline.
- Preserve failures; do not silently replace them with successful reruns.
- Do not change prompts or configuration during the comparison.
- Pass only the question text to each pipeline.

## Review procedure

For each question and pipeline, record:

- execution success or failure;
- expected and actual question_status;
- latency and token usage;
- manual assessments below, with a short justification.

Use pass / partial / fail for applicable assessments.
Use not_assessed when a judgment has not been made.
Use not_applicable when an assessment does not apply.
Execution failures are recorded separately, not scored as answer failures.

### Both pipelines

- Relevance: does the answer address the original question and its constraints?
- Scope handling: does it recognize missing information or an out-of-scope request?
- Evidence accuracy: are substantive conclusions consistent with independently
  checked reference evidence?

Evidence accuracy requires manual reference checking.
Until references have been checked, mark it not_assessed.
Record the references and their evidence scope.
Do not use the V0B answer as the reference standard for V0A.

### V0B only

- Query fidelity: does the query preserve the central concepts without
  materially changing the question? Assess this alongside the fixed
  query-generation policy; not every qualifier must appear literally.
- Retrieval relevance: label each record relevant / partially relevant /
  irrelevant to the original question.
- Grounding: are substantive claims supported by the supplied records,
  with appropriate qualifications?
- Citation support: do cited records support the associated claims,
  and are substantive evidence claims missing citations?

Judge grounding and citation support only against the metadata and
abstracts actually supplied to the model.

For V0A, retrieval and citation assessments are not_applicable.
For questions without substantive evidence claims, grounding and citation
assessments may also be not_applicable.

## Interpretation

Keep execution success, schema validity, citation consistency, and
semantic quality separate.

Report per-question findings and descriptive summaries.
Do not combine all dimensions into a single overall score.

This small, single-run benchmark is exploratory. It does not establish
clinical reliability or statistical superiority of either pipeline.