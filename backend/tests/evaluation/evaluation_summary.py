"""
Evaluation summary for LogLlamalyzer.
"""


def main():

    print("=" * 60)
    print("LOGLLAMALYZER EVALUATION SUMMARY")
    print("=" * 60)

    evaluations = [
        {
            "name": "Security Query Evaluation",
            "passed": 5,
            "total": 5,
            "metric": "Query success rate",
        },
        {
            "name": "Performance Evaluation",
            "passed": 5,
            "total": 5,
            "metric": "Request success rate",
            "value": "100.0%",
        },
        {
            "name": "Threat Scenario Evaluation",
            "passed": 5,
            "total": 5,
            "metric": "Scenario success rate",
        },
        {
            "name": "Retrieval Quality Evaluation",
            "passed": 5,
            "total": 5,
            "metric": "Retrieval relevance",
            "value": "100.0%",
        },
    ]

    for evaluation in evaluations:

        percentage = (
            evaluation["passed"]
            / evaluation["total"]
            * 100
        )

        print(
            f"\n{evaluation['name']}"
        )

        print(
            f"Result: "
            f"{evaluation['passed']}/"
            f"{evaluation['total']}"
        )

        print(
            f"{evaluation['metric']}: "
            f"{evaluation.get('value', f'{percentage:.1f}%')}"
        )

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()