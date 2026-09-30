from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from clinical_evidence_agent.schemas import EvidenceAnswer



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