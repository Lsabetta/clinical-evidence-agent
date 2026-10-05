import pytest
from pydantic import ValidationError

from clinical_evidence_agent.schemas import EvidenceAnswer, Source


def test_correct_evidence_answer():
    answer = EvidenceAnswer(
        question_status="well_specified",
        evidence_status="not_assessed",
        summary="Ibuprofen may reduce sore-throat symptoms.",
        sources=[],
        limitations=["No external evidence was retrieved."],
    )

    assert answer.question_status == "well_specified"
    assert answer.evidence_status == "not_assessed"
    assert answer.sources == []


def test_incorrect_question_status():
    with pytest.raises(ValidationError):
        EvidenceAnswer(
            question_status="unclear",
            evidence_status="not_assessed",
            summary="...",
            sources=[],
            limitations=[],
        )

def test_correct_answer_with_sources():
    answer = EvidenceAnswer(
        question_status="well_specified",
        evidence_status="partial",
        summary="Ibuprofen may reduce sore-throat symptoms.",
        sources=[Source(pmid="123", title="...", url="...")],
        limitations=["Only a limited set of external evidence was retrieved."],
    )

    assert answer.question_status == "well_specified"
    assert answer.evidence_status == "partial"
    assert len(answer.sources) == 1
    assert answer.sources[0].pmid == "123"
    assert answer.sources[0].pmcid is None