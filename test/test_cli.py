import json
import sys
from unittest.mock import Mock

import pytest

from clinical_evidence_agent import cli, v0b
from clinical_evidence_agent.llm import LLMResult
from clinical_evidence_agent.query_generation import PubMedQuery


def test_v0b_cli_logs_partial_results_on_fetch_failure(
    monkeypatch,
    tmp_path,
):
    # Il log viene scritto nella directory temporanea del test.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "clinical-evidence-agent",
            "Does melatonin improve sleep?",
            "--pipeline",
            "v0b",
            "--top-k",
            "2",
        ],
    )

    query_result = LLMResult(
        output=PubMedQuery(query="melatonin AND insomnia"),
        model="test-model",
        latency_s=0.1,
        input_tokens=20,
        output_tokens=5,
    )
    fetch_error = TimeoutError("PubMed fetch timed out")

    generate_query = Mock(return_value=query_result)
    search = Mock(return_value=["38016484", "27998379"])
    fetch = Mock(side_effect=fetch_error)
    synthesize = Mock()

    monkeypatch.setattr(v0b, "generate_pubmed_query", generate_query)
    monkeypatch.setattr(v0b, "search_pubmed", search)
    monkeypatch.setattr(v0b, "get_pubmed_records", fetch)
    monkeypatch.setattr(v0b, "synthesize_v0b", synthesize)

    with pytest.raises(v0b.V0BRunError) as caught:
        cli.main()

    # L'errore originale resta accessibile.
    assert caught.value.cause is fetch_error
    assert caught.value.__cause__ is fetch_error

    search.assert_called_once_with(
        "melatonin AND insomnia",
        max_results=2,
    )
    fetch.assert_called_once_with(["38016484", "27998379"])
    synthesize.assert_not_called()

    # Verifichiamo il file realmente scritto dalla CLI.
    log_path = tmp_path / "runs" / "v0b.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])

    assert record["status"] == "failure"
    assert record["failed_stage"] == "fetch"
    assert record["error_type"] == "TimeoutError"
    assert record["query_generation"]["query"] == "melatonin AND insomnia"
    assert record["retrieval"]["returned_pmids"] == [
        "38016484",
        "27998379",
    ]
    assert record["retrieval"]["records"] is None
    assert record["synthesis"]["draft"] is None
    assert record["answer"] is None