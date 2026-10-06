# V0A/V0B exploratory smoke benchmark: first run

Review date: 2026-10-05. Run: `20261005T105933093343Z`.

## Status and scope

The fixed V0B workflow is retained as an implemented baseline with documented failures. This report closes the first execution/grounding review and independently checks two selected reference claims. It is not a complete clinical accuracy evaluation, an exhaustive literature review, or evidence that either baseline is clinically reliable. No V1 advantage has been demonstrated.

Review method: assistant-assisted inspection of saved outputs and evidence snapshots, plus external PubMed abstract checks for Q05 and Q09. A separate human clinical review has not been performed. Other substantive clinical accuracy judgments remain `not_assessed`. This is a descriptive, single-run evaluation, not a blinded or statistically powered comparison.

## Configuration and provenance

- Ten questions, one execution per pipeline; original failures retained.
- Model: `qwen3:4b-instruct`; requested temperature: 0.
- Prompts: `v0a-005`, `pubmed-query-v003`, `v0b-synthesis-v002`.
- V0B: one query-generation call, one PubMed search (`sort=relevance`, top-k 3), batch fetch, one synthesis call.
- Original logs did not record explicit requested context size. Q01's error reported 4096 available tokens; do not infer this for every original call.
- Questions, protocol, drafts, records, answers, stderr and index are preserved in the original archive.
- No rerun or post-benchmark fix is substituted into original results.
- Original archive SHA-256: `53bf2456d26fe42845b2308529383a93b145b80decaa089468fcfd219fd7faee`.

## Execution and classification

| Metric | V0A | V0B |
|---|---:|---:|
| Successful executions | 10/10 | 8/10 |
| Correct question_status among final answers | 8/10 | 5/8 |
| Mean recorded latency, successful executions | 14.3 s | 208.6 s |

Latencies have different boundaries: V0A records its LLM-call latency, whereas V0B records pipeline latency. The success-conditioned averages exclude V0B failures and use different question subsets. No speed ratio or overall quality score is inferred.

| Case | Pipeline | Exit code | Final question_status | Recorded latency (s) |
|---|---|---:|---|---:|
| Q01 | v0a | 0 | well_specified | 28.4 |
| Q01 | v0b | 1 | no final answer | 13.7 |
| Q02 | v0a | 0 | well_specified | 14.2 |
| Q02 | v0b | 0 | well_specified | 313.2 |
| Q03 | v0a | 0 | well_specified | 14.4 |
| Q03 | v0b | 0 | well_specified | 185.3 |
| Q04 | v0a | 0 | well_specified | 12.8 |
| Q04 | v0b | 0 | well_specified | 278.6 |
| Q05 | v0a | 0 | well_specified | 17.1 |
| Q05 | v0b | 0 | well_specified | 48.6 |
| Q06 | v0a | 0 | well_specified | 15.3 |
| Q06 | v0b | 0 | out_of_scope | 174.2 |
| Q07 | v0a | 0 | underspecified | 10.2 |
| Q07 | v0b | 0 | well_specified | 210.3 |
| Q08 | v0a | 0 | underspecified | 10.1 |
| Q08 | v0b | 0 | well_specified | 166.7 |
| Q09 | v0a | 0 | out_of_scope | 10.7 |
| Q09 | v0b | 0 | underspecified | 292.1 |
| Q10 | v0a | 0 | out_of_scope | 9.4 |
| Q10 | v0b | 1 | no final answer | 120.1 |

## Case findings from saved evidence

| Case | Finding |
|---|---|
| Q01 | Synthesis rejected: 4474 input tokens exceed 4096 available context. No final answer. Retrieval includes a directly relevant exercise review plus a TENS review and an osteoarthritis burden study. Query adds `chronic`. |
| Q02 | Some quantitative results are reproduced correctly, but the 5% weight-loss result is attributed to PMID 39458528 instead of 41692034. The former is a meta-analysis of RCTs, not a single comparative study. |
| Q03 | Correct aggregate effect and very-low certainty, followed by unsupported assertions that diagnosed-depression populations were excluded/not evaluated. Unreported subgroup estimates do not establish absent studies. One retrieved record concerns maternal nutrition and offspring. |
| Q04 | Main AAD estimate is supported. Claimed absence of adverse-event data beyond general symptoms contradicts the quantitative safety analysis in PMID 29257353. |
| Q05 | Zero records. Query contains an ungrouped OR and exclusion words treated as required terms. Final answer contains `[PMID: ]`, silently ignored by the original validator. External reference review below. |
| Q06 | Two sickle-cell reviews retrieved. V0B recognizes irrelevance but incorrectly marks a valid migraine question `out_of_scope`. |
| Q07 | V0A incorrectly marks the question underspecified. V0B recognizes a case report and a protocol, then overstates absence of outcomes despite the case report describing fatigue measurement and change. |
| Q08 | V0A correctly marks the question underspecified. V0B marks it well specified and lets retrieved conditions determine the answer to an ambiguous question. |
| Q09 | Both misclassify the question. V0B query ends with `2024:`; actual date-filter interpretation is not established from the saved log. It generalizes absent retrieved trials to absent literature. External reference review below. |
| Q10 | V0A recognizes the individual-diagnosis request as out of scope. V0B draft says underspecified and cites 35965030 and 40527717 inline but declares only 40527717. Validation correctly prevents delivery. Draft findings are diagnostic, not a successful final answer. |

## Independent reference checks

Reference evidence scope: PubMed metadata and abstracts only, accessed 2026-10-05. Both publications predate the benchmark. These targeted checks establish counterexamples to particular claims; they are not exhaustive gold-standard answer sets or recall denominators.

### Q05: aspirin for primary prevention in older adults

Reference: [ASPREE, PMID 30221597](https://pubmed.ncbi.nlm.nih.gov/30221597/), DOI 10.1056/NEJMoa1805819 (2018).

The randomized trial enrolled 19,114 adults without cardiovascular disease, generally aged at least 70 (at least 65 for Black and Hispanic US participants), comparing aspirin 100 mg with placebo. Over median 4.7-year follow-up, cardiovascular disease was not significantly reduced (HR 0.95, 95% CI 0.83–1.08), while major hemorrhage increased (HR 1.38, 95% CI 1.18–1.62).

Expected key distinction: no demonstrated significant cardiovascular reduction in this trial is not proof of exactly zero effect; bleeding harms must not be omitted.

- V0A evidence accuracy: **fail** for its explicit assertion that ASPREE demonstrated significant cardiovascular benefit.
- V0B retrieval: missed this relevant reference and returned no records. Its abstention is appropriate relative to the empty snapshot; the unqualified limitation asserting no available evidence overreaches. Overall answer adequacy: **partial**, with malformed citation separately recorded. It is not an accurate substantive answer to the clinical evidence question.

### Q09: randomized tirzepatide versus semaglutide evidence from 2024 onward

Reference: [SURMOUNT-5, PMID 40353578](https://pubmed.ncbi.nlm.nih.gov/40353578/), DOI 10.1056/NEJMoa2416394. Published online 2025-05-11, journal issue 2025-07-03.

This phase 3b open-label randomized trial compared the drugs in 751 adults with obesity without type 2 diabetes. At 72 weeks, mean weight change was −20.2% for tirzepatide versus −13.7% for semaglutide (P<0.001), at the maximum tolerated doses studied. Gastrointestinal events were most common. The population, doses and follow-up constrain applicability.

- V0A evidence accuracy: **fail** for denying the existence of a qualifying trial.
- V0B evidence accuracy: **fail** for the same global denial. It did not retrieve this reference; the correct evidence-scoped statement would concern only the supplied records.
- The absence claim in a review searched through 2024 cannot establish absence of trials published subsequently.

## Post-benchmark changes (excluded from scores)

1. Malformed bracketed PMID markers are now rejected; user reported offline tests passing.
2. Context requested explicitly at 8192 tokens; requested context added to ordinary logging per agreed edits.
3. A separate Q01 synthesis replay used the same three saved records, consumed 4474 input / 321 output tokens, and completed in 332.4 seconds. User-provided `ollama ps` showed 8192 context and 100% CPU. This does not establish hardware placement in earlier runs.
4. The replay still misstates some certainty/comparator details and omits immediate citations for several claims. Context repair is not a grounding repair.

## Decision and next experiment

Stop prompt tuning on this smoke set. Preserve the baseline code checkpoint, original logs, and post-fix checkpoint separately; insert actual Git hashes when available. Baseline implementation is operational, but semantic quality remains limited and independent accuracy review is incomplete.

Proceed to the manual V1 loop already planned. Hypothesis: adaptive retrieval can recover useful evidence after empty or irrelevant first results. Keep synthesis shared. Bound execution at six actual tool invocations, counting each search and fetch, including failed calls. Record actions, arguments, evidence additions, termination reason, latency and token usage.

For a focused agency comparison, use the same initial query-generation component and synthesis prompt; document evidence/context budgets and any component differences. Changed live PubMed results are a confounder. Evaluate paired runs with preserved snapshots and comparable settings, not the old 4096-context failures against a new 8192-context agent without qualification.

Q05/Q09 now serve as diagnosed development cases, not unseen generalization tests. Recovery of their reference evidence is informative but does not by itself prove general benefit. Keep fresh cases for later evaluation. Do not expose reference PMIDs to the agent during the recovery test.

First V1 implementation unit: a tool-calling adapter and dispatcher for `search_pubmed` and `get_pubmed_records`, with explicit state, a tool-call budget and a terminal transition to the shared synthesis function. No LangGraph or verifier at this stage.
