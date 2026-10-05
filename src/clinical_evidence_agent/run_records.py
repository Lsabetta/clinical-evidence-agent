from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from clinical_evidence_agent.schemas import EvidenceAnswer
import json

from clinical_evidence_agent.query_generation import QUERY_PROMPT_VERSION
from clinical_evidence_agent.v0b import (
    V0BResult,
    V0BRunError,
    V0B_SYNTHESIS_PROMPT_VERSION,
)


class V0ARunRecord(BaseModel):
    timestamp: datetime
    question: str
    prompt_version: str
    model: str
    latency_s: float | None
    input_tokens: int | None
    output_tokens: int | None
    schema_valid: bool | None
    answer: EvidenceAnswer | None
    error_type: str | None = None
    error_message: str | None = None

def save_v0a_run(
    record: V0ARunRecord,
    path: Path = Path("runs/v0a.jsonl"),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(record.model_dump_json())
        file.write("\n")


def save_v0b_run(
    question: str,
    result: V0BResult,
    path: Path = Path("runs/v0b.jsonl"),
) -> None:
    query_call = result.query_result
    synthesis_call = result.synthesis_result

    record = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "v0b",
        "status": "success",
        "question": question.strip(),
        "query_generation": {
            "prompt_version": QUERY_PROMPT_VERSION,
            "model": query_call.model,
            "temperature": 0,
            "query": query_call.output.query,
            "latency_s": query_call.latency_s,
            "input_tokens": query_call.input_tokens,
            "output_tokens": query_call.output_tokens,
        },
        "retrieval": {
            "sort": "relevance",
            "top_k": result.top_k,
            "returned_pmids": result.retrieved_pmids,
            "record_count": len(result.records),
            "records": [
                item.model_dump(mode="json")
                for item in result.records
            ],
            "latency_s": result.retrieval_latency_s,
        },
        "synthesis": {
            "prompt_version": V0B_SYNTHESIS_PROMPT_VERSION,
            "model": synthesis_call.model,
            "temperature": 0,
            "latency_s": synthesis_call.latency_s,
            "input_tokens": synthesis_call.input_tokens,
            "output_tokens": synthesis_call.output_tokens,
            "draft": synthesis_call.output.model_dump(mode="json"),
        },
        "validation": {
            "schema_valid": True,
            "citation_consistency_valid": True,
        },
        "answer": result.answer.model_dump(mode="json"),
        "total_latency_s": result.total_latency_s,
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False))
        file.write("\n")

def save_v0b_failure(
    error: V0BRunError,
    path: Path = Path("runs/v0b.jsonl"),
) -> None:
    trace = error.trace
    query_call = trace.query_result
    synthesis_call = trace.synthesis_result

    record = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "v0b",
        "status": "failure",
        "question": trace.question,
        "failed_stage": trace.stage,
        "error_type": type(error.cause).__name__,
        "error_message": str(error.cause),
        "query_generation": {
            "prompt_version": QUERY_PROMPT_VERSION,
            "model": query_call.model if query_call else None,
            "temperature": 0,
            "query": query_call.output.query if query_call else None,
            "latency_s": query_call.latency_s if query_call else None,
            "input_tokens": query_call.input_tokens if query_call else None,
            "output_tokens": query_call.output_tokens if query_call else None,
        },
        "retrieval": {
            "sort": "relevance",
            "top_k": trace.top_k,
            "returned_pmids": trace.retrieved_pmids,
            "record_count": (
                len(trace.records)
                if trace.records is not None
                else None
            ),
            "records": (
                [item.model_dump(mode="json") for item in trace.records]
                if trace.records is not None
                else None
            ),
            "latency_s": trace.retrieval_latency_s,
        },
        "synthesis": {
            "prompt_version": V0B_SYNTHESIS_PROMPT_VERSION,
            "model": synthesis_call.model if synthesis_call else None,
            "temperature": 0,
            "latency_s": (
                synthesis_call.latency_s if synthesis_call else None
            ),
            "input_tokens": (
                synthesis_call.input_tokens if synthesis_call else None
            ),
            "output_tokens": (
                synthesis_call.output_tokens if synthesis_call else None
            ),
            "draft": (
                synthesis_call.output.model_dump(mode="json")
                if synthesis_call else None
            ),
        },
        "validation": {
            "schema_valid": True if synthesis_call else None,
            "citation_consistency_valid": None,
        },
        "answer": None,
        "total_latency_s": trace.total_latency_s,
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False))
        file.write("\n")