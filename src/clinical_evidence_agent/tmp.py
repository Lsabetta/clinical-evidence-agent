from clinical_evidence_agent.tools.pubmed import get_pubmed_records
from clinical_evidence_agent.v0b import (
    synthesize_v0b,
    build_v0b_answer,
)

question = "Does melatonin improve sleep in adults with chronic insomnia?"

records = get_pubmed_records([
    "38016484",
    "27998379",
    "33164742",
])

print("Question:", question)
print("Evidence PMIDs:", [record.pmid for record in records])

result = synthesize_v0b(question, records)

# Print before validation so failures remain inspectable.
print("Draft:")
print(result.output.model_dump_json(indent=2))

print("Synthesis latency:", result.latency_s)
print("Synthesis tokens:", result.input_tokens, result.output_tokens)

# Citation validation is called inside build_v0b_answer().
answer = build_v0b_answer(result.output, records)

print("Final answer:")
print(answer.model_dump_json(indent=2))