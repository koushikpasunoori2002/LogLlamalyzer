"""
Final quantitative evaluation.

Produces a reproducible quantitative summary of the completed
LogLlamalyzer retrieval, source filtering, metadata preservation,
and processing performance.

Metrics include:

- retrieval Hit@1
- retrieval Hit@3
- mean reciprocal rank (MRR)
- source filtering accuracy
- classification preservation
- severity preservation
- embedding latency
- retrieval latency
- context construction latency
- LLM analysis latency
- end-to-end processing latency
- successful analysis rate

The evaluation uses controlled benchmark data so that the expected
security scenario and source are known in advance.
"""

from pathlib import Path
import json
import shutil
import statistics
import sys
import time


# ------------------------------------------------------------------
# Project root
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager
from backend.rag.retriever import Retriever
from backend.rag.context import ContextBuilder
from backend.llm.generation import RAGAnalyzer


# ------------------------------------------------------------------
# Evaluation database
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "final_quantitative_evaluation"
)

COLLECTION_NAME = (
    "final_quantitative_evaluation"
)


# ------------------------------------------------------------------
# Benchmark dataset
# ------------------------------------------------------------------

BENCHMARK_DOCUMENTS = [
    (
        "Multiple failed SSH authentication attempts were "
        "detected from a remote IP address. Repeated failed "
        "password attempts indicate a possible SSH brute force "
        "attack."
    ),
    (
        "Repeated failed login attempts against the same account "
        "may indicate a credential attack."
    ),
    (
        "A user executed sudo commands to obtain elevated "
        "privileges. The activity may indicate privilege "
        "escalation."
    ),
    (
        "A suspicious executable was launched from a temporary "
        "directory. The activity may indicate malware execution."
    ),
    (
        "Multiple connections were attempted against different "
        "network ports. The pattern may indicate network scanning "
        "or reconnaissance."
    ),
    (
        "The Apache web server started successfully and is "
        "operating normally."
    ),
]


# ------------------------------------------------------------------
# IDs
# ------------------------------------------------------------------

BENCHMARK_IDS = [
    "quantitative_001",
    "quantitative_002",
    "quantitative_003",
    "quantitative_004",
    "quantitative_005",
    "quantitative_006",
]


# ------------------------------------------------------------------
# Metadata
# ------------------------------------------------------------------

BENCHMARK_METADATA = [
    {
        "source": "server-a",
        "synchronized_source": "server-a",
        "scenario": "ssh_brute_force",
        "classification": "ssh_brute_force",
        "severity": "HIGH",
        "log_type": "auth",
    },
    {
        "source": "server-b",
        "synchronized_source": "server-b",
        "scenario": "credential_attack",
        "classification": "credential_attack",
        "severity": "MEDIUM",
        "log_type": "auth",
    },
    {
        "source": "server-b",
        "synchronized_source": "server-b",
        "scenario": "privilege_escalation",
        "classification": "privilege_escalation",
        "severity": "HIGH",
        "log_type": "auth",
    },
    {
        "source": "server-c",
        "synchronized_source": "server-c",
        "scenario": "malware",
        "classification": "malware",
        "severity": "HIGH",
        "log_type": "syslog",
    },
    {
        "source": "server-c",
        "synchronized_source": "server-c",
        "scenario": "network_scanning",
        "classification": "network_scanning",
        "severity": "HIGH",
        "log_type": "syslog",
    },
    {
        "source": "server-a",
        "synchronized_source": "server-a",
        "scenario": "normal",
        "classification": "normal",
        "severity": "INFO",
        "log_type": "apache",
    },
]


# ------------------------------------------------------------------
# Retrieval benchmark cases
# ------------------------------------------------------------------

RETRIEVAL_CASES = [
    {
        "query": (
            "failed SSH authentication "
            "brute force attack"
        ),
        "expected_classification": "ssh_brute_force",
        "expected_source": "server-a",
    },
    {
        "query": (
            "repeated failed login "
            "credential attack"
        ),
        "expected_classification": "credential_attack",
        "expected_source": "server-b",
    },
    {
        "query": (
            "sudo privilege escalation "
            "elevated privileges"
        ),
        "expected_classification": "privilege_escalation",
        "expected_source": "server-b",
    },
    {
        "query": (
            "suspicious executable "
            "malware execution"
        ),
        "expected_classification": "malware",
        "expected_source": "server-c",
    },
    {
        "query": (
            "network scanning "
            "suspicious connections"
        ),
        "expected_classification": "network_scanning",
        "expected_source": "server-c",
    },
]


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------

def average(values):

    if not values:
        return 0.0

    return sum(values) / len(values)


def percentage(
    numerator,
    denominator,
):

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100.0
    )


# ------------------------------------------------------------------
# Database preparation
# ------------------------------------------------------------------

def create_database():

    if DATABASE_PATH.exists():

        try:

            shutil.rmtree(
                DATABASE_PATH
            )

        except PermissionError:

            pass

    database = ChromaDatabase(
        persist_directory=DATABASE_PATH,
        collection_name=COLLECTION_NAME,
    )

    embedding_manager = (
        EmbeddingManager()
    )

    embeddings = (
        embedding_manager.embed_texts(
            BENCHMARK_DOCUMENTS
        )
    )

    database.add(
        ids=BENCHMARK_IDS,
        embeddings=embeddings,
        documents=BENCHMARK_DOCUMENTS,
        metadatas=BENCHMARK_METADATA,
    )

    return (
        database,
        embedding_manager,
    )


# ------------------------------------------------------------------
# Main evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "FINAL QUANTITATIVE EVALUATION"
    )
    print("=" * 70)

    print()
    print(
        "Preparing controlled quantitative benchmark..."
    )

    database, embedding_manager = (
        create_database()
    )

    print(
        "Benchmark records:",
        database.count(),
    )

    # --------------------------------------------------------------
    # Retriever
    # --------------------------------------------------------------

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=3,
        distance_threshold=0.98,
    )

    # --------------------------------------------------------------
    # Evaluation storage
    # --------------------------------------------------------------

    retrieval_ranks = []
    hit_at_1 = 0
    hit_at_3 = 0

    source_checks = []
    classification_checks = []
    severity_checks = []

    embedding_times = []
    retrieval_times = []
    context_times = []
    analysis_times = []
    total_times = []

    successful_analyses = 0

    # --------------------------------------------------------------
    # Evaluate retrieval benchmark
    # --------------------------------------------------------------

    print()
    print("-" * 70)
    print(
        "RETRIEVAL QUALITY"
    )
    print("-" * 70)

    for index, case in enumerate(
        RETRIEVAL_CASES,
        start=1,
    ):

        query = case["query"]

        expected_classification = (
            case["expected_classification"]
        )

        expected_source = (
            case["expected_source"]
        )

        print()
        print(
            f"QUERY {index}/{len(RETRIEVAL_CASES)}"
        )

        print(
            "Query:",
            query,
        )

        # ----------------------------------------------------------
        # Embedding timing
        # ----------------------------------------------------------

        embedding_start = (
            time.perf_counter()
        )

        query_embedding = (
            embedding_manager.embed_text(
                query
            )
        )

        embedding_elapsed = (
            time.perf_counter()
            - embedding_start
        )

        embedding_times.append(
            embedding_elapsed
        )

        # ----------------------------------------------------------
        # Retrieval timing
        # ----------------------------------------------------------

        retrieval_start = (
            time.perf_counter()
        )

        results = retriever.retrieve(
            query=query,
            top_k=3,
        )

        retrieval_elapsed = (
            time.perf_counter()
            - retrieval_start
        )

        retrieval_times.append(
            retrieval_elapsed
        )

        metadata = results.get(
            "metadatas",
            [],
        )

        if metadata:

            metadata = metadata[0]

        else:

            metadata = []

        classifications = [
            item.get(
                "classification"
            )
            for item in metadata
        ]

        sources = [
            item.get(
                "source"
            )
            for item in metadata
        ]

        # ----------------------------------------------------------
        # Rank calculation
        # ----------------------------------------------------------

        matching_rank = None

        for rank, item in enumerate(
            metadata,
            start=1,
        ):

            if (
                item.get(
                    "classification"
                )
                == expected_classification
            ):

                matching_rank = rank
                break

        if matching_rank is not None:

            retrieval_ranks.append(
                matching_rank
            )

            if matching_rank == 1:

                hit_at_1 += 1

            if matching_rank <= 3:

                hit_at_3 += 1

        # ----------------------------------------------------------
        # Classification and severity
        # ----------------------------------------------------------

        classification_checks.append(
            expected_classification
            in classifications
        )

        expected_severity = None

        for item in metadata:

            if item.get(
                "classification"
            ) == expected_classification:

                expected_severity = (
                    item.get(
                        "severity"
                    )
                )

                break

        severity_checks.append(
            expected_severity
            is not None
        )

        # ----------------------------------------------------------
        # Source-aware retrieval
        # ----------------------------------------------------------

        filtered_metadata = (
            retriever.retrieve_metadata(
                query=query,
                top_k=3,
                source=expected_source,
            )
        )

        filtered_sources = [
            item.get(
                "source"
            )
            for item in filtered_metadata
        ]

        source_valid = (
            len(filtered_sources) > 0
            and all(
                source == expected_source
                for source in filtered_sources
            )
        )

        source_checks.append(
            source_valid
        )

        print(
            "Top classifications:",
            classifications,
        )

        print(
            "Matching rank:",
            matching_rank,
        )

        print(
            "Filtered sources:",
            filtered_sources,
        )

        print(
            "Embedding time:",
            f"{embedding_elapsed:.4f}s",
        )

        print(
            "Retrieval time:",
            f"{retrieval_elapsed:.4f}s",
        )

    # --------------------------------------------------------------
    # Retrieval summary
    # --------------------------------------------------------------

    mean_reciprocal_rank = average(
        [
            1.0 / rank
            for rank in retrieval_ranks
        ]
    )

    hit_at_1_rate = percentage(
        hit_at_1,
        len(RETRIEVAL_CASES),
    )

    hit_at_3_rate = percentage(
        hit_at_3,
        len(RETRIEVAL_CASES),
    )

    classification_rate = percentage(
        sum(
            classification_checks
        ),
        len(
            classification_checks
        ),
    )

    severity_rate = percentage(
        sum(
            severity_checks
        ),
        len(
            severity_checks
        ),
    )

    source_rate = percentage(
        sum(
            source_checks
        ),
        len(
            source_checks
        ),
    )

    print()
    print("=" * 70)
    print(
        "RETRIEVAL METRICS"
    )
    print("=" * 70)

    print(
        "Queries evaluated:",
        len(RETRIEVAL_CASES),
    )

    print(
        "Hit@1:",
        f"{hit_at_1_rate:.2f}%",
    )

    print(
        "Hit@3:",
        f"{hit_at_3_rate:.2f}%",
    )

    print(
        "MRR:",
        f"{mean_reciprocal_rank:.4f}",
    )

    print(
        "Classification preservation:",
        f"{classification_rate:.2f}%",
    )

    print(
        "Severity preservation:",
        f"{severity_rate:.2f}%",
    )

    print(
        "Source filtering accuracy:",
        f"{source_rate:.2f}%",
    )

    # ==============================================================
    # PERFORMANCE MEASUREMENT
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "PROCESSING PERFORMANCE"
    )
    print("-" * 70)

    analyzer = None

    try:

        analyzer_start = (
            time.perf_counter()
        )

        analyzer = RAGAnalyzer()

        analyzer_initialisation_time = (
            time.perf_counter()
            - analyzer_start
        )

    except Exception as exc:

        analyzer_initialisation_time = 0.0

        print(
            "Analyzer initialisation error:",
            exc,
        )

    print(
        "Analyzer initialisation:",
        f"{analyzer_initialisation_time:.4f}s",
    )

    # --------------------------------------------------------------
    # Measure complete pipeline
    # --------------------------------------------------------------

    for index, case in enumerate(
        RETRIEVAL_CASES,
        start=1,
    ):

        query = case["query"]

        total_start = (
            time.perf_counter()
        )

        # ----------------------------------------------------------
        # Embedding
        # ----------------------------------------------------------

        embedding_start = (
            time.perf_counter()
        )

        embedding_manager.embed_text(
            query
        )

        embedding_elapsed = (
            time.perf_counter()
            - embedding_start
        )

        embedding_times.append(
            embedding_elapsed
        )

        # ----------------------------------------------------------
        # Retrieval
        # ----------------------------------------------------------

        retrieval_start = (
            time.perf_counter()
        )

        results = retriever.retrieve(
            query=query,
            top_k=3,
        )

        retrieval_elapsed = (
            time.perf_counter()
            - retrieval_start
        )

        retrieval_times.append(
            retrieval_elapsed
        )

        # ----------------------------------------------------------
        # Context construction
        # ----------------------------------------------------------

        context_start = (
            time.perf_counter()
        )

        context_builder = (
            ContextBuilder(
                log_retriever=retriever,
                knowledge_retriever=None,
                top_k_logs=3,
                top_k_knowledge=3,
            )
        )

        context = (
            context_builder.build(
                query
            )
        )

        context_elapsed = (
            time.perf_counter()
            - context_start
        )

        context_times.append(
            context_elapsed
        )

        # ----------------------------------------------------------
        # LLM analysis
        # ----------------------------------------------------------

        analysis_start = (
            time.perf_counter()
        )

        analysis_success = False

        if analyzer is not None:

            try:

                response = analyzer.analyze(
                    context
                )

                answer = getattr(
                    response,
                    "answer",
                    "",
                )

                analysis_success = (
                    isinstance(
                        answer,
                        str,
                    )
                    and bool(
                        answer.strip()
                    )
                )

            except Exception as exc:

                print(
                    "Analysis error:",
                    exc,
                )

        analysis_elapsed = (
            time.perf_counter()
            - analysis_start
        )

        analysis_times.append(
            analysis_elapsed
        )

        if analysis_success:

            successful_analyses += 1

        # ----------------------------------------------------------
        # Total
        # ----------------------------------------------------------

        total_elapsed = (
            time.perf_counter()
            - total_start
        )

        total_times.append(
            total_elapsed
        )

        retrieved_documents = (
            results.get(
                "documents",
                [],
            )
        )

        if retrieved_documents:

            retrieved_documents = (
                retrieved_documents[0]
            )

        else:

            retrieved_documents = []

        print()
        print(
            f"Query {index}: {query}"
        )

        print(
            "Retrieved documents:",
            len(retrieved_documents),
        )

        print(
            "Context logs:",
            context.log_count(),
        )

        print(
            "Analysis generated:",
            analysis_success,
        )

        print(
            "Total time:",
            f"{total_elapsed:.4f}s",
        )

    # --------------------------------------------------------------
    # Performance statistics
    # --------------------------------------------------------------

    average_embedding_time = average(
        embedding_times
    )

    average_retrieval_time = average(
        retrieval_times
    )

    average_context_time = average(
        context_times
    )

    average_analysis_time = average(
        analysis_times
    )

    average_total_time = average(
        total_times
    )

    minimum_total_time = (
        min(total_times)
        if total_times
        else 0.0
    )

    maximum_total_time = (
        max(total_times)
        if total_times
        else 0.0
    )

    analysis_success_rate = percentage(
        successful_analyses,
        len(RETRIEVAL_CASES),
    )

    print()
    print("=" * 70)
    print(
        "PERFORMANCE METRICS"
    )
    print("=" * 70)

    print(
        "Average embedding time:",
        f"{average_embedding_time:.4f}s",
    )

    print(
        "Average retrieval time:",
        f"{average_retrieval_time:.4f}s",
    )

    print(
        "Average context time:",
        f"{average_context_time:.4f}s",
    )

    print(
        "Average LLM analysis time:",
        f"{average_analysis_time:.4f}s",
    )

    print(
        "Average total processing time:",
        f"{average_total_time:.4f}s",
    )

    print(
        "Minimum total time:",
        f"{minimum_total_time:.4f}s",
    )

    print(
        "Maximum total time:",
        f"{maximum_total_time:.4f}s",
    )

    print(
        "Successful analyses:",
        f"{successful_analyses}/{len(RETRIEVAL_CASES)}",
    )

    print(
        "Analysis success rate:",
        f"{analysis_success_rate:.2f}%",
    )

    # --------------------------------------------------------------
    # Bottleneck
    # --------------------------------------------------------------

    stage_averages = {
        "Embedding": average_embedding_time,
        "Retrieval": average_retrieval_time,
        "Context": average_context_time,
        "LLM Analysis": average_analysis_time,
    }

    bottleneck = max(
        stage_averages,
        key=stage_averages.get,
    )

    print()
    print(
        "Largest measured stage:",
        bottleneck,
    )

    print(
        "Bottleneck average:",
        f"{stage_averages[bottleneck]:.4f}s",
    )

    # ==============================================================
    # RELIABILITY METRICS
    # ==============================================================

    print()
    print("-" * 70)
    print(
        "RELIABILITY METRICS"
    )
    print("-" * 70)

    validation_results = []

    # Empty query validation
    try:

        retriever.retrieve(
            query="",
            top_k=3,
        )

        empty_query_valid = False

    except ValueError:

        empty_query_valid = True

    validation_results.append(
        empty_query_valid
    )

    # Invalid top-k validation
    try:

        Retriever(
            database=database,
            embedding_manager=embedding_manager,
            top_k=0,
        )

        invalid_top_k_valid = False

    except ValueError:

        invalid_top_k_valid = True

    validation_results.append(
        invalid_top_k_valid
    )

    # Invalid distance threshold validation
    try:

        Retriever(
            database=database,
            embedding_manager=embedding_manager,
            top_k=3,
            distance_threshold=-1,
        )

        invalid_threshold_valid = False

    except ValueError:

        invalid_threshold_valid = True

    validation_results.append(
        invalid_threshold_valid
    )

    reliability_rate = percentage(
        sum(validation_results),
        len(validation_results),
    )

    print(
        "Input validation checks:",
        len(validation_results),
    )

    print(
        "Validation checks passed:",
        sum(validation_results),
    )

    print(
        "Validation reliability:",
        f"{reliability_rate:.2f}%",
    )

    # ==============================================================
    # FINAL QUANTITATIVE SUMMARY
    # ==============================================================

    quantitative_summary = {
        "benchmark_records": database.count(),
        "retrieval_queries": len(
            RETRIEVAL_CASES
        ),
        "retrieval": {
            "hit_at_1_percent": round(
                hit_at_1_rate,
                2,
            ),
            "hit_at_3_percent": round(
                hit_at_3_rate,
                2,
            ),
            "mrr": round(
                mean_reciprocal_rank,
                4,
            ),
            "classification_preservation_percent": round(
                classification_rate,
                2,
            ),
            "severity_preservation_percent": round(
                severity_rate,
                2,
            ),
            "source_filtering_accuracy_percent": round(
                source_rate,
                2,
            ),
        },
        "performance": {
            "analyzer_initialisation_seconds": round(
                analyzer_initialisation_time,
                4,
            ),
            "average_embedding_seconds": round(
                average_embedding_time,
                4,
            ),
            "average_retrieval_seconds": round(
                average_retrieval_time,
                4,
            ),
            "average_context_seconds": round(
                average_context_time,
                4,
            ),
            "average_llm_analysis_seconds": round(
                average_analysis_time,
                4,
            ),
            "average_total_seconds": round(
                average_total_time,
                4,
            ),
            "minimum_total_seconds": round(
                minimum_total_time,
                4,
            ),
            "maximum_total_seconds": round(
                maximum_total_time,
                4,
            ),
            "bottleneck": bottleneck,
        },
        "reliability": {
            "checks": len(validation_results),
            "passed": sum(validation_results),
            "reliability_percent": round(
                reliability_rate,
                2,
            ),
            "analysis_success_rate_percent": round(
                analysis_success_rate,
                2,
            ),
        },
    }

    # --------------------------------------------------------------
    # Save machine-readable summary
    # --------------------------------------------------------------

    output_directory = (
        PROJECT_ROOT
        / "outputs"
        / "results"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_directory
        / "final_quantitative_evaluation.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            quantitative_summary,
            file,
            indent=4,
        )

    # --------------------------------------------------------------
    # Final summary
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "FINAL QUANTITATIVE SUMMARY"
    )
    print("=" * 70)

    print(
        json.dumps(
            quantitative_summary,
            indent=4,
        )
    )

    print()
    print(
        "Results saved to:",
        output_file,
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    evaluation_valid = (
        database.count()
        == len(BENCHMARK_DOCUMENTS)
        and hit_at_3_rate
        == 100.0
        and classification_rate
        == 100.0
        and severity_rate
        == 100.0
        and source_rate
        == 100.0
        and reliability_rate
        == 100.0
        and len(total_times)
        == len(RETRIEVAL_CASES)
    )

    print()
    print("=" * 70)
    print(
        "FINAL QUANTITATIVE VALIDATION"
    )
    print("=" * 70)

    print(
        "Benchmark integrity:",
        "PASS"
        if database.count()
        == len(BENCHMARK_DOCUMENTS)
        else "FAIL",
    )

    print(
        "Hit@3:",
        "PASS"
        if hit_at_3_rate == 100.0
        else "FAIL",
    )

    print(
        "Classification preservation:",
        "PASS"
        if classification_rate == 100.0
        else "FAIL",
    )

    print(
        "Severity preservation:",
        "PASS"
        if severity_rate == 100.0
        else "FAIL",
    )

    print(
        "Source filtering:",
        "PASS"
        if source_rate == 100.0
        else "FAIL",
    )

    print(
        "Reliability:",
        "PASS"
        if reliability_rate == 100.0
        else "FAIL",
    )

    print(
        "Performance timing:",
        "PASS"
        if len(total_times)
        == len(RETRIEVAL_CASES)
        else "FAIL",
    )

    print()

    if not evaluation_valid:

        print(
            "FINAL QUANTITATIVE EVALUATION FAILED"
        )

        print("=" * 70)

        try:
            database.close()
        except Exception:
            pass

        raise SystemExit(1)

    print(
        "FINAL QUANTITATIVE EVALUATION PASSED"
    )

    print("=" * 70)

    # --------------------------------------------------------------
    # Close database
    # --------------------------------------------------------------

    try:

        database.close()

    except Exception:

        pass

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        if DATABASE_PATH.exists():

            shutil.rmtree(
                DATABASE_PATH
            )

            print(
                "Database cleanup: PASS"
            )

    except PermissionError:

        print(
            "Database cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Database cleanup: SKIPPED "
            f"({exc})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()