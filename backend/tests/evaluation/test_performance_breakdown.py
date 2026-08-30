"""
Performance breakdown evaluation.

Measures the execution time of the major stages of the
LogLlamalyzer RAG pipeline:

- embedding generation
- vector retrieval
- context construction
- LLM analysis
- total processing time

A controlled benchmark collection is used so that the
performance measurements are reproducible and do not
depend on the state of the development database.
"""

from pathlib import Path
import shutil
import sys
import time


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase
from backend.rag.retriever import Retriever
from backend.rag.context import ContextBuilder
from backend.llm.generation import RAGAnalyzer


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "performance_breakdown_test"
)

COLLECTION_NAME = "performance_breakdown"

TOP_K = 3


# ------------------------------------------------------------------
# Representative benchmark documents
# ------------------------------------------------------------------

DOCUMENTS = [
    (
        "Multiple failed SSH authentication attempts were "
        "detected from a remote IP address. Repeated failed "
        "password attempts may indicate an SSH brute force attack."
    ),
    (
        "The system recorded repeated failed login attempts "
        "for the same account. This pattern may indicate a "
        "credential attack."
    ),
    (
        "A user executed sudo commands to obtain elevated "
        "privileges. Suspicious privilege escalation activity "
        "should be investigated."
    ),
    (
        "A suspicious executable was launched from a temporary "
        "directory. Unexpected process execution may indicate "
        "malware activity."
    ),
    (
        "Multiple connections were attempted against different "
        "network ports. Repeated connection attempts may indicate "
        "network scanning or reconnaissance activity."
    ),
    (
        "The Apache web server started successfully and is "
        "operating normally."
    ),
    (
        "A user successfully logged into the system."
    ),
    (
        "The package manager completed a normal software update."
    ),
    (
        "The system completed a normal shutdown operation."
    ),
    (
        "The kernel reported a normal system event."
    ),
]


# ------------------------------------------------------------------
# Document metadata
# ------------------------------------------------------------------

IDS = [
    "performance_001",
    "performance_002",
    "performance_003",
    "performance_004",
    "performance_005",
    "performance_006",
    "performance_007",
    "performance_008",
    "performance_009",
    "performance_010",
]


METADATAS = [
    {
        "scenario": "ssh_brute_force",
        "classification": "ssh_brute_force",
        "severity": "HIGH",
        "source": "server-a",
        "log_type": "auth",
    },
    {
        "scenario": "credential_attack",
        "classification": "credential_attack",
        "severity": "MEDIUM",
        "source": "server-b",
        "log_type": "auth",
    },
    {
        "scenario": "privilege_escalation",
        "classification": "privilege_escalation",
        "severity": "HIGH",
        "source": "server-b",
        "log_type": "auth",
    },
    {
        "scenario": "malware",
        "classification": "malware",
        "severity": "HIGH",
        "source": "server-c",
        "log_type": "syslog",
    },
    {
        "scenario": "network_scanning",
        "classification": "network_scanning",
        "severity": "HIGH",
        "source": "server-c",
        "log_type": "syslog",
    },
    {
        "scenario": "normal_web_server",
        "classification": "normal",
        "severity": "INFO",
        "source": "server-a",
        "log_type": "apache",
    },
    {
        "scenario": "successful_login",
        "classification": "normal",
        "severity": "INFO",
        "source": "server-a",
        "log_type": "auth",
    },
    {
        "scenario": "normal_package_update",
        "classification": "normal",
        "severity": "INFO",
        "source": "server-b",
        "log_type": "dpkg",
    },
    {
        "scenario": "normal_shutdown",
        "classification": "normal",
        "severity": "INFO",
        "source": "server-c",
        "log_type": "syslog",
    },
    {
        "scenario": "normal_kernel_event",
        "classification": "normal",
        "severity": "INFO",
        "source": "server-c",
        "log_type": "kern",
    },
]


# ------------------------------------------------------------------
# Performance queries
# ------------------------------------------------------------------

QUERIES = [
    "failed SSH authentication brute force attack",
    "suspicious sudo privilege escalation activity",
    "possible malware execution detected",
    "possible network scanning suspicious connections",
    "repeated failed login attempts",
]


# ------------------------------------------------------------------
# Result extraction helpers
# ------------------------------------------------------------------

def extract_documents(results):
    """
    Extract document texts from a ChromaDB result dictionary.
    """

    if not results:
        return []

    documents = results.get(
        "documents",
        [],
    )

    if not isinstance(documents, list):
        return []

    if not documents:
        return []

    if not isinstance(documents[0], list):
        return []

    return documents[0]


# ------------------------------------------------------------------
# Timing helper
# ------------------------------------------------------------------

def timed(function, *args, **kwargs):
    """
    Execute a function and return:

        result
        elapsed_time
    """

    start = time.perf_counter()

    result = function(
        *args,
        **kwargs,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return result, elapsed


# ------------------------------------------------------------------
# Database setup
# ------------------------------------------------------------------

def create_benchmark_database(
    embedding_manager,
):
    """
    Create and populate the controlled benchmark collection.
    """

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

    embeddings = embedding_manager.embed_texts(
        DOCUMENTS
    )

    database.add(
        ids=IDS,
        embeddings=embeddings,
        documents=DOCUMENTS,
        metadatas=METADATAS,
    )

    if database.count() != len(DOCUMENTS):

        raise AssertionError(
            "Benchmark database was not populated "
            "with the expected number of documents."
        )

    return database


# ------------------------------------------------------------------
# Main evaluation
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("PERFORMANCE BREAKDOWN EVALUATION")
    print("=" * 70)

    print()
    print(
        "Project Root:",
        PROJECT_ROOT,
    )

    print(
        "Queries Evaluated:",
        len(QUERIES),
    )

    print(
        "Benchmark Documents:",
        len(DOCUMENTS),
    )

    print("-" * 70)

    # --------------------------------------------------------------
    # Initialise embedding manager
    # --------------------------------------------------------------

    print()
    print(
        "Initialising embedding manager..."
    )

    embedding_manager = EmbeddingManager()

    print(
        "Embedding manager initialised."
    )

    # --------------------------------------------------------------
    # Create controlled benchmark database
    # --------------------------------------------------------------

    print()
    print(
        "Creating benchmark vector database..."
    )

    setup_start = time.perf_counter()

    database = create_benchmark_database(
        embedding_manager
    )

    setup_time = (
        time.perf_counter()
        - setup_start
    )

    print(
        "Benchmark database records:",
        database.count(),
    )

    print(
        f"Benchmark setup time: "
        f"{setup_time:.4f} seconds"
    )

    # --------------------------------------------------------------
    # Create Retriever
    # --------------------------------------------------------------

    retriever = Retriever(
        database=database,
        embedding_manager=embedding_manager,
        top_k=TOP_K,
        distance_threshold=0.98,
    )

    # --------------------------------------------------------------
    # Create ContextBuilder
    #
    # The performance benchmark measures the log-RAG path directly.
    # Knowledge retrieval is not included because the objective here
    # is to isolate the log retrieval and generation stages.
    # --------------------------------------------------------------

    context_builder = ContextBuilder(
        log_retriever=retriever,
        knowledge_retriever=None,
        top_k_logs=TOP_K,
        top_k_knowledge=0,
    )

    # --------------------------------------------------------------
    # Initialise the real RAG analyzer once.
    #
    # This is deliberately done outside the query timing loop so
    # that we measure analysis/generation time rather than repeated
    # object construction overhead.
    # --------------------------------------------------------------

    print()
    print(
        "Initialising RAG analyzer..."
    )

    analyzer_start = time.perf_counter()

    analyzer = RAGAnalyzer()

    analyzer_initialisation_time = (
        time.perf_counter()
        - analyzer_start
    )

    print(
        f"RAG analyzer initialisation: "
        f"{analyzer_initialisation_time:.4f} seconds"
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    performance_results = []

    # --------------------------------------------------------------
    # Evaluate queries
    # --------------------------------------------------------------

    for index, query in enumerate(
        QUERIES,
        start=1,
    ):

        print()
        print("=" * 70)
        print(
            f"QUERY {index}/{len(QUERIES)}"
        )
        print("=" * 70)

        print(
            "Query:",
            query,
        )

        query_result = {
            "query": query,
            "embedding_time": None,
            "retrieval_time": None,
            "context_time": None,
            "analysis_time": None,
            "total_time": None,
            "retrieval_count": 0,
            "context_log_count": 0,
            "analysis_success": False,
        }

        total_start = time.perf_counter()

        # ==========================================================
        # STEP 1 - QUERY EMBEDDING
        # ==========================================================

        print()
        print("STEP 1 - QUERY EMBEDDING")

        try:

            _, embedding_time = timed(
                embedding_manager.embed_text,
                query,
            )

            query_result[
                "embedding_time"
            ] = embedding_time

            print(
                f"Embedding Time: "
                f"{embedding_time:.4f} seconds"
            )

            print(
                "Embedding Status: PASS"
            )

        except Exception as exc:

            print(
                "Embedding Status: FAIL"
            )

            print(
                "Error:",
                exc,
            )

            raise

        # ==========================================================
        # STEP 2 - VECTOR RETRIEVAL
        # ==========================================================

        print()
        print("STEP 2 - VECTOR RETRIEVAL")

        try:

            retrieval_result, retrieval_time = timed(
                retriever.retrieve,
                query,
                TOP_K,
            )

            retrieved_documents = (
                extract_documents(
                    retrieval_result
                )
            )

            query_result[
                "retrieval_time"
            ] = retrieval_time

            query_result[
                "retrieval_count"
            ] = len(
                retrieved_documents
            )

            print(
                f"Retrieval Time: "
                f"{retrieval_time:.4f} seconds"
            )

            print(
                "Documents Retrieved:",
                len(retrieved_documents),
            )

            retrieval_pass = (
                len(retrieved_documents) > 0
            )

            print(
                "Retrieval Status:",
                "PASS"
                if retrieval_pass
                else "FAIL",
            )

        except Exception as exc:

            print(
                "Retrieval Status: FAIL"
            )

            print(
                "Error:",
                exc,
            )

            raise

        # ==========================================================
        # STEP 3 - CONTEXT CONSTRUCTION
        # ==========================================================

        print()
        print("STEP 3 - CONTEXT CONSTRUCTION")

        try:

            context, context_time = timed(
                context_builder.build,
                query,
            )

            query_result[
                "context_time"
            ] = context_time

            log_count = (
                context.log_count()
            )

            query_result[
                "context_log_count"
            ] = log_count

            print(
                f"Context Time: "
                f"{context_time:.4f} seconds"
            )

            print(
                "Log Results in Context:",
                log_count,
            )

            print(
                "Context Status:",
                "PASS"
                if log_count > 0
                else "FAIL",
            )

        except Exception as exc:

            print(
                "Context Status: FAIL"
            )

            print(
                "Error:",
                exc,
            )

            raise

        # ==========================================================
        # STEP 4 - LLM ANALYSIS
        # ==========================================================

        print()
        print("STEP 4 - LLM ANALYSIS")

        try:

            response, analysis_time = timed(
                analyzer.analyze,
                context,
            )

            query_result[
                "analysis_time"
            ] = analysis_time

            analysis_success = (
                response is not None
                and isinstance(
                    response.answer,
                    str,
                )
                and bool(
                    response.answer.strip()
                )
            )

            query_result[
                "analysis_success"
            ] = analysis_success

            print(
                f"LLM Analysis Time: "
                f"{analysis_time:.4f} seconds"
            )

            print(
                "Analysis Status:",
                "PASS"
                if analysis_success
                else "FAIL",
            )

        except Exception as exc:

            print(
                "Analysis Status: FAIL"
            )

            print(
                "Error:",
                exc,
            )

            raise

        # ==========================================================
        # STEP 5 - TOTAL
        # ==========================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        query_result[
            "total_time"
        ] = total_time

        print()
        print("STEP 5 - TOTAL")

        print(
            f"Total Processing Time: "
            f"{total_time:.4f} seconds"
        )

        performance_results.append(
            query_result
        )

    # --------------------------------------------------------------
    # Close retriever
    # --------------------------------------------------------------

    try:

        retriever.close()

    except Exception:

        pass

    # --------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------

    def collect(field):

        return [
            result[field]
            for result in performance_results
            if result[field] is not None
        ]

    def average(values):

        if not values:
            return 0.0

        return (
            sum(values)
            / len(values)
        )

    embedding_times = collect(
        "embedding_time"
    )

    retrieval_times = collect(
        "retrieval_time"
    )

    context_times = collect(
        "context_time"
    )

    analysis_times = collect(
        "analysis_time"
    )

    total_times = collect(
        "total_time"
    )

    average_embedding = average(
        embedding_times
    )

    average_retrieval = average(
        retrieval_times
    )

    average_context = average(
        context_times
    )

    average_analysis = average(
        analysis_times
    )

    average_total = average(
        total_times
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("PERFORMANCE BREAKDOWN RESULTS")
    print("=" * 70)

    print(
        f"Queries Evaluated: "
        f"{len(performance_results)}"
    )

    print(
        f"Benchmark Records: "
        f"{len(DOCUMENTS)}"
    )

    print()

    print(
        f"Analyzer Initialisation Time: "
        f"{analyzer_initialisation_time:.4f} seconds"
    )

    print(
        f"Average Query Embedding Time: "
        f"{average_embedding:.4f} seconds"
    )

    print(
        f"Average Retrieval Time: "
        f"{average_retrieval:.4f} seconds"
    )

    print(
        f"Average Context Time: "
        f"{average_context:.4f} seconds"
    )

    print(
        f"Average LLM Analysis Time: "
        f"{average_analysis:.4f} seconds"
    )

    print(
        f"Average Total Processing Time: "
        f"{average_total:.4f} seconds"
    )

    if total_times:

        print()

        print(
            f"Minimum Total Time: "
            f"{min(total_times):.4f} seconds"
        )

        print(
            f"Maximum Total Time: "
            f"{max(total_times):.4f} seconds"
        )

    # --------------------------------------------------------------
    # Stage contribution
    # --------------------------------------------------------------

    print()
    print("-" * 70)
    print("AVERAGE STAGE CONTRIBUTION")
    print("-" * 70)

    if average_total > 0:

        print(
            f"Embedding: "
            f"{average_embedding / average_total * 100:.2f}%"
        )

        print(
            f"Retrieval: "
            f"{average_retrieval / average_total * 100:.2f}%"
        )

        print(
            f"Context Building: "
            f"{average_context / average_total * 100:.2f}%"
        )

        print(
            f"LLM Analysis: "
            f"{average_analysis / average_total * 100:.2f}%"
        )

    # --------------------------------------------------------------
    # Per-query performance
    # --------------------------------------------------------------

    print()
    print("-" * 70)
    print("PER-QUERY PERFORMANCE")
    print("-" * 70)

    for index, result in enumerate(
        performance_results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{result['total_time']:.2f}s total | "
            f"Embedding: "
            f"{result['embedding_time']:.2f}s | "
            f"Retrieval: "
            f"{result['retrieval_time']:.2f}s | "
            f"Context: "
            f"{result['context_time']:.2f}s | "
            f"Analysis: "
            f"{result['analysis_time']:.2f}s"
        )

        print(
            f"   Retrieved: "
            f"{result['retrieval_count']} | "
            f"Context Logs: "
            f"{result['context_log_count']}"
        )

        print(
            f"   {result['query']}"
        )

    # --------------------------------------------------------------
    # Bottleneck
    # --------------------------------------------------------------

    print()
    print("-" * 70)
    print("PERFORMANCE BOTTLENECK")
    print("-" * 70)

    stage_averages = {
        "Query Embedding": average_embedding,
        "Retrieval": average_retrieval,
        "Context Building": average_context,
        "LLM Analysis": average_analysis,
    }

    bottleneck = max(
        stage_averages,
        key=stage_averages.get,
    )

    print(
        "Largest measured stage:",
        bottleneck,
    )

    print(
        f"Average time: "
        f"{stage_averages[bottleneck]:.4f} seconds"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("PERFORMANCE BREAKDOWN VALIDATION")
    print("=" * 70)

    embedding_valid = (
        len(embedding_times)
        == len(QUERIES)
    )

    retrieval_valid = all(
        result["retrieval_count"] > 0
        for result in performance_results
    )

    context_valid = all(
        result["context_log_count"] > 0
        for result in performance_results
    )

    analysis_valid = all(
        result["analysis_success"]
        for result in performance_results
    )

    total_valid = (
        len(total_times)
        == len(QUERIES)
    )

    print(
        "Embedding timing:",
        "PASS"
        if embedding_valid
        else "FAIL",
    )

    print(
        "Retrieval measurement:",
        "PASS"
        if retrieval_valid
        else "FAIL",
    )

    print(
        "Context measurement:",
        "PASS"
        if context_valid
        else "FAIL",
    )

    print(
        "LLM analysis measurement:",
        "PASS"
        if analysis_valid
        else "FAIL",
    )

    print(
        "Total timing:",
        "PASS"
        if total_valid
        else "FAIL",
    )

    # --------------------------------------------------------------
    # Fail if the benchmark did not actually exercise the pipeline
    # --------------------------------------------------------------

    if not embedding_valid:

        raise AssertionError(
            "Embedding performance measurement failed."
        )

    if not retrieval_valid:

        raise AssertionError(
            "Retrieval performance measurement failed."
        )

    if not context_valid:

        raise AssertionError(
            "Context construction measurement failed."
        )

    if not analysis_valid:

        raise AssertionError(
            "LLM analysis performance measurement failed."
        )

    if not total_valid:

        raise AssertionError(
            "Total performance measurement failed."
        )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "PERFORMANCE BREAKDOWN EVALUATION PASSED"
    )
    print("=" * 70)

    print(
        "All major RAG processing stages were measured "
        "successfully using the actual project components."
    )

    print("=" * 70)

    # --------------------------------------------------------------
    # Best-effort cleanup
    # --------------------------------------------------------------

    try:

        database.close()

    except Exception:

        pass

    try:

        if DATABASE_PATH.exists():

            shutil.rmtree(
                DATABASE_PATH
            )

            print(
                "Benchmark database cleanup: PASS"
            )

    except PermissionError:

        print(
            "Benchmark database cleanup: SKIPPED "
            "(files still locked by ChromaDB)"
        )

    except Exception as exc:

        print(
            "Benchmark database cleanup: SKIPPED "
            f"({exc})"
        )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()