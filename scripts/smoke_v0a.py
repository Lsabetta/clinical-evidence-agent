from clinical_evidence_agent.v0a import run_v0a


CASES = [
    (
        "What evidence exists for ibuprofen in the treatment of sore throat?",
        "well_specified",
    ),
    (
        "Can immunosuppressants be used during chemotherapy?",
        "well_specified",
    ),
    (
        "Is vitamin supplementation beneficial during chemotherapy?",
        "well_specified",
    ),
    (
        "What are the effects of vitamins?",
        "underspecified",
    ),
    (
        "I have fever and chest pain. What disease do I have?",
        "out_of_scope",
    ),
]


def main() -> None:
    for question, expected_status in CASES:
        print("=" * 80)
        print(f"Question: {question}")
        print(f"Expected: {expected_status}")

        result = run_v0a(question)

        actual_status = result.output.question_status
        passed = actual_status == expected_status

        print(f"Actual:   {actual_status}")
        print(f"PASS:     {passed}")
        print(f"Summary:  {result.output.summary}")
        print(f"Latency:  {result.latency_s:.1f} s")
        print(
            f"Tokens:   {result.input_tokens} in / "
            f"{result.output_tokens} out"
        )


if __name__ == "__main__":
    main()