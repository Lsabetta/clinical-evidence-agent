import argparse
from datetime import datetime, timezone

from pydantic import ValidationError

from clinical_evidence_agent.llm import MODEL, NUM_CTX
from clinical_evidence_agent.run_records import (
    V0ARunRecord,
    save_v0a_run,
    save_v0b_run,
    save_v0b_failure,
)
from clinical_evidence_agent.v0b import V0BRunError, run_v0b
from clinical_evidence_agent.v0a import V0A_PROMPT_VERSION, run_v0a

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clinical evidence research assistant."
    )
    parser.add_argument(
        "question",
        help="Biomedical evidence-research question.",
    )
    parser.add_argument(
        "--pipeline",
        choices=["v0a", "v0b"],
        default="v0a",
        help="Pipeline to run (default: v0a).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Maximum number of PubMed records for v0b (default: 3).",
    )
    args = parser.parse_args()

    if not args.question.strip():
        parser.error("Question must be non-empty.")

    if args.pipeline == "v0b":
        if args.top_k <= 0:
            parser.error("--top-k must be positive.")

        try:
            result = run_v0b(args.question, top_k=args.top_k)
        except V0BRunError as exc:
            save_v0b_failure(exc)
            raise

        save_v0b_run(args.question, result)
        print(result.answer.model_dump_json(indent=2))
        return

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
            requested_num_ctx=NUM_CTX,
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
            requested_num_ctx=NUM_CTX,
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
        requested_num_ctx=NUM_CTX,
    )

    save_v0a_run(record)

    print(result.output.model_dump_json(indent=2))