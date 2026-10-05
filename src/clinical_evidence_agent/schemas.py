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

class PubMedRecord(BaseModel):
    pmid: str
    title: str
    url: str
    abstract: str | None = None
    pmcid: str | None = None
    authors: list[str]
    journal: str | None = None
    publication_date: str | None = None
    publication_types: list[str]