import pytest

from clinical_evidence_agent.schemas import PubMedRecord
from clinical_evidence_agent.v0b import (
    V0BDraft,
    validate_draft_citations,
)
from unittest.mock import Mock

from clinical_evidence_agent import v0b
from clinical_evidence_agent.llm import LLMResult
from clinical_evidence_agent.query_generation import PubMedQuery
import json

from clinical_evidence_agent.run_records import save_v0b_run

def test_rejects_declared_source_without_inline_citation():
    record = PubMedRecord(
        pmid="123",
        title="Synthetic test article",
        url="https://pubmed.ncbi.nlm.nih.gov/123/",
        authors=[],
        publication_types=[],
    )

    draft = V0BDraft(
        question_status="well_specified",
        evidence_status="partial",
        summary="A summary without an inline citation.",
        cited_pmids=["123"],
        limitations=[],
    )

    with pytest.raises(
        ValueError,
        match="Inline citations do not match cited_pmids",
    ):
        validate_draft_citations(draft, [record])

from clinical_evidence_agent.v0b import build_v0b_answer


def test_build_answer_uses_retrieved_source_metadata():
    record = PubMedRecord(
        pmid="123",
        title="Retrieved title",
        url="https://pubmed.ncbi.nlm.nih.gov/123/",
        authors=[],
        publication_types=[],
    )

    draft = V0BDraft(
        question_status="well_specified",
        evidence_status="partial",
        summary="A synthetic claim [PMID: 123].",
        cited_pmids=["123"],
        limitations=["Small evidence set."],
    )

    answer = build_v0b_answer(draft, [record])

    assert len(answer.sources) == 1
    assert answer.sources[0].pmid == record.pmid
    assert answer.sources[0].title == record.title
    assert answer.sources[0].url == record.url
    assert answer.summary == draft.summary
    assert "Small evidence set." in answer.limitations

def test_run_v0b_connects_pipeline(monkeypatch, tmp_path):
    question = "Does melatonin improve sleep in adults?"
    query = "melatonin AND sleep AND adult"

    record = PubMedRecord(
        pmid="123",
        title="Synthetic article",
        url="https://pubmed.ncbi.nlm.nih.gov/123/",
        abstract="Synthetic evidence for testing.",
        authors=[],
        publication_types=[],
    )
    records = [record]

    query_result = LLMResult(
        output=PubMedQuery(query=query),
        model="test-model",
        latency_s=0.1,
        input_tokens=10,
        output_tokens=5,
    )

    synthesis_result = LLMResult(
        output=V0BDraft(
            question_status="well_specified",
            evidence_status="partial",
            summary="A synthetic finding [PMID: 123].",
            cited_pmids=["123"],
            limitations=[],
        ),
        model="test-model",
        latency_s=0.2,
        input_tokens=30,
        output_tokens=15,
    )

    generate = Mock(return_value=query_result)
    search = Mock(return_value=["123"])
    fetch = Mock(return_value=records)
    synthesize = Mock(return_value=synthesis_result)

    monkeypatch.setattr(v0b, "generate_pubmed_query", generate)
    monkeypatch.setattr(v0b, "search_pubmed", search)
    monkeypatch.setattr(v0b, "get_pubmed_records", fetch)
    monkeypatch.setattr(v0b, "synthesize_v0b", synthesize)

    result = v0b.run_v0b(question, top_k=3)

    generate.assert_called_once_with(question)
    search.assert_called_once_with(query, max_results=3)
    fetch.assert_called_once_with(["123"])
    synthesize.assert_called_once_with(question, records)

    assert result.retrieved_pmids == ["123"]
    assert result.records == records
    assert result.query_result == query_result
    assert result.synthesis_result == synthesis_result
    assert result.top_k == 3
    assert result.answer.sources[0].pmid == "123"
    assert result.answer.sources[0].title == "Synthetic article"
    
    path = tmp_path / "v0b.jsonl"
    save_v0b_run(question, result, path)

    saved = json.loads(path.read_text(encoding="utf-8"))

    assert saved["question"] == question
    assert saved["query_generation"]["query"] == query
    assert saved["retrieval"]["records"] == [
        record.model_dump(mode="json")
    ]
    assert saved["synthesis"]["draft"] == (
        synthesis_result.output.model_dump(mode="json")
    )
    assert saved["answer"] == result.answer.model_dump(mode="json")