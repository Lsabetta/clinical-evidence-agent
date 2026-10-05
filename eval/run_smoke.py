import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the benchmark. Otherwise, only validate the dataset.",
    )
    args = parser.parse_args()

    dataset_path = ROOT / "eval" / "questions.jsonl"
    dataset_text = dataset_path.read_text(encoding="utf-8")
    cases = [
        json.loads(line)
        for line in dataset_text.splitlines()
        if line.strip()
    ]

    seen_ids = set()
    valid_statuses = {
        "well_specified",
        "underspecified",
        "out_of_scope",
    }

    for case in cases:
        case_id = case["id"]
        question = case["question"]

        if not isinstance(case_id, str) or not case_id:
            raise ValueError("Each case needs a non-empty string ID.")
        if not all(char.isalnum() or char in "_-" for char in case_id):
            raise ValueError(f"Invalid case ID: {case_id}")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate case ID: {case_id}")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Empty or invalid question: {case_id}")
        if case["expected_question_status"] not in valid_statuses:
            raise ValueError(f"Invalid expected status: {case_id}")

        seen_ids.add(case_id)

    if not cases:
        raise ValueError("The dataset is empty.")

    print(f"Validated {len(cases)} questions.")
    print(f"Planned executions: {len(cases) * 2}")

    if not args.run:
        print("No model or PubMed calls made. Add --run to execute.")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_dir = ROOT / "eval" / "results" / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)

    # Preserve the dataset and protocol used for this benchmark.
    (output_dir / "questions.jsonl").write_text(
        dataset_text,
        encoding="utf-8",
    )
    (output_dir / "smoke_protocol.md").write_text(
        (ROOT / "eval" / "smoke_protocol.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # Make src importable even when each CLI runs in a separate directory.
    environment = os.environ.copy()
    python_paths = [str(ROOT / "src")]
    if environment.get("PYTHONPATH"):
        python_paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)

    print(f"Results: {output_dir}", flush=True)

    for case in cases:
        for pipeline in ("v0a", "v0b"):
            case_dir = output_dir / case["id"] / pipeline
            case_dir.mkdir(parents=True)

            command = [
                sys.executable,
                "-c",
                "from clinical_evidence_agent.cli import main; main()",
                case["question"],
                "--pipeline",
                pipeline,
            ]
            if pipeline == "v0b":
                command.extend(["--top-k", "3"])

            print(f"Running {case['id']} / {pipeline}...", flush=True)

            with (
                (case_dir / "stdout.txt").open("w", encoding="utf-8") as stdout,
                (case_dir / "stderr.txt").open("w", encoding="utf-8") as stderr,
            ):
                process = subprocess.run(
                    command,
                    cwd=case_dir,
                    env=environment,
                    stdout=stdout,
                    stderr=stderr,
                    check=False,
                )

            entry = {
                "id": case["id"],
                "pipeline": pipeline,
                "question": case["question"],
                "expected_question_status": case["expected_question_status"],
                "returncode": process.returncode,
                "directory": str(case_dir.relative_to(output_dir)),
            }

            with (output_dir / "index.jsonl").open(
                "a", encoding="utf-8"
            ) as index:
                index.write(json.dumps(entry, ensure_ascii=False) + "\n")

            print(f"Finished with exit code {process.returncode}", flush=True)

    print(f"Benchmark finished. Results: {output_dir}")


if __name__ == "__main__":
    main()