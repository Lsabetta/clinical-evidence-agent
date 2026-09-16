from pydantic import BaseModel
from typing import Literal

class Source(BaseModel):
    pmid: str
    pmcid: str | None = None
    title: str
    url: str

QuestionStatus = Literal[
    "well_specified",
    "underspecified",
    "out_of_scope",
]
EvidenceStatus = Literal[
    "sufficient",
    "partial",
    "insufficient",
    "not_assessed",
]

class EvidenceAnswer(BaseModel):
    question_status: QuestionStatus
    evidence_status: EvidenceStatus
    summary: str
    sources: list[Source]
    limitations: list[str]