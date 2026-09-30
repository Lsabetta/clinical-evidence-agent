import pytest

from clinical_evidence_agent.llm import LLMResult
from clinical_evidence_agent.v0a import V0ADraft, run_v0a


def test_v0a_builds_expected_answer(monkeypatch):
    def fake_generate_structured_answer(prompt, schema):
        return LLMResult(
            output=V0ADraft(
                question_status="well_specified",
                summary="Example summary.",
            ),
            model="fake-model",
            latency_s=1.0,
            input_tokens=10,
            output_tokens=5,
        )

    monkeypatch.setattr(
        "clinical_evidence_agent.v0a.generate_structured_answer",
        fake_generate_structured_answer,
    )

    result = run_v0a("What evidence exists for treatment X?")

    assert result.output.question_status == "well_specified"
    assert result.output.evidence_status == "not_assessed"
    assert result.output.sources == []
    assert result.output.limitations == [
        "No external biomedical literature was retrieved or verified."
    ]

def test_v0a_valueerror():
    with pytest.raises(ValueError):
        run_v0a("")

    with pytest.raises(ValueError):
        run_v0a(" ")