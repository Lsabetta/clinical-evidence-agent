import argparse
from datetime import datetime, timezone

from pydantic import ValidationError

from clinical_evidence_agent.llm import MODEL
from clinical_evidence_agent.run_records import V0ARunRecord, save_v0a_run
from clinical_evidence_agent.v0a import V0A_PROMPT_VERSION, run_v0a

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clinical evidence research assistant."
    )
    parser.add_argument(
        "question",
        help="Biomedical evidence-research question.",
    )

    args = parser.parse_args()

    try:
        result = run_v0a(args.question)

    except ValidationError as exc:
        record = V0ARunRecord(
            timestamp=datetime.now(timezone.utc),
            question=args.question,
            prompt_version=V0A_PROMPT_VERSION,
            model=MODEL,
            latency_s=None,
            input_tokens=None,
            output_tokens=None,
            schema_valid=False,
            answer=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        save_v0a_run(record)
        raise

    except Exception as exc:
        record = V0ARunRecord(
            timestamp=datetime.now(timezone.utc),
            question=args.question,
            prompt_version=V0A_PROMPT_VERSION,
            model=MODEL,
            latency_s=None,
            input_tokens=None,
            output_tokens=None,
            schema_valid=None,
            answer=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        save_v0a_run(record)
        raise
    
    record = V0ARunRecord(
        timestamp=datetime.now(timezone.utc),
        question=args.question,
        prompt_version=V0A_PROMPT_VERSION,
        model=result.model,
        latency_s=result.latency_s,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        schema_valid=True,
        answer=result.output,
    )

    save_v0a_run(record)

    print(result.output.model_dump_json(indent=2))