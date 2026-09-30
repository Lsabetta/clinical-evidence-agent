from pydantic import BaseModel

from clinical_evidence_agent.llm import (
    LLMResult,
    generate_structured_answer,
)
from clinical_evidence_agent.schemas import (
    EvidenceAnswer,
    QuestionStatus,
)


V0A_PROMPT_VERSION = "v0a-005"


class V0ADraft(BaseModel):
    question_status: QuestionStatus
    summary: str

def build_v0a_prompt(question: str) -> str:
    return f"""
You are answering a biomedical evidence-research question
using only your internal model knowledge.

Provide a concise best-effort answer to the question.

Do not claim that PubMed or external literature was searched,
retrieved, checked, or verified.
Do not provide citations, PMIDs, or specific references.

question_status semantics:

- well_specified:
  The question is sufficiently clear to provide a meaningful general
  biomedical evidence-oriented answer, even if the topic is broad.

- underspecified:
  Important information is missing or ambiguous enough that answering
  would require making arbitrary assumptions about what the user means.

- out_of_scope:
  The request is not a biomedical evidence-research question, or it asks
  for individualized diagnosis or clinical advice.

Examples:

- "What evidence exists for ibuprofen in the treatment of sore throat?"
  -> well_specified

- "Can immunosuppressants be used during chemotherapy?"
  -> well_specified

- "Is vitamin supplementation beneficial during chemotherapy?"
  -> well_specified

- "What are the effects of vitamins?"
  -> underspecified

- "I have fever and chest pain. What disease do I have?"
  -> out_of_scope

Question:
{question}
""".strip()


def run_v0a(question: str) -> LLMResult[EvidenceAnswer]:
    question = question.strip()

    if not question:
        raise ValueError("Question must be non-empty.")

    llm_result = generate_structured_answer(
        prompt=build_v0a_prompt(question),
        schema=V0ADraft,
    )

    draft = llm_result.output

    answer = EvidenceAnswer(
        question_status=draft.question_status,
        evidence_status="not_assessed",
        summary=draft.summary,
        sources=[],
        limitations=[
            "No external biomedical literature was retrieved or verified."
        ],
    )

    return LLMResult(
        output=answer,
        model=llm_result.model,
        latency_s=llm_result.latency_s,
        input_tokens=llm_result.input_tokens,
        output_tokens=llm_result.output_tokens,
    )