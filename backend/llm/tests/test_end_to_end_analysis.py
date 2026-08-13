"""
test_end_to_end_analysis.py

Phase 16 end-to-end integration test.

Pipeline:

Log data
    ->
Log Retriever
    +
Knowledge Retriever
    ->
ContextBuilder
    ->
RAGContext
    ->
PromptBuilder
    ->
Ollama LLM
    ->
Security Analysis
"""

from pathlib import Path
import sys


# --------------------------------------------------------------
# Project Root
# --------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------------------
# Imports
# --------------------------------------------------------------

from backend.rag.context import ContextBuilder
from backend.rag.context import RAGContext

from backend.rag.retriever import Retriever

from backend.knowledge import KnowledgeRetriever

from backend.database.chroma import ChromaDatabase

from backend.llm.embeddings import EmbeddingManager

from backend.llm.generation import PromptBuilder
from backend.llm.generation import LLMClient
from backend.llm.generation import LLMResponse


# --------------------------------------------------------------
# Main Test
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("PHASE 16 END-TO-END SECURITY ANALYSIS TEST")
    print("=" * 70)

    # ----------------------------------------------------------
    # Step 1 — Initialise embedding model
    # ----------------------------------------------------------

    print("\n[1] Initialising embedding model...")

    embedding_manager = EmbeddingManager()

    print(
        "Embedding Model:"
    )

    print(
        embedding_manager.model_information()
    )

    print(
        "Embedding Dimension:",
        embedding_manager.embedding_dimension()
    )

    print(
        "Embedding Model: PASS"
    )

    # ----------------------------------------------------------
    # Step 2 — Create log database
    # ----------------------------------------------------------

    print("\n[2] Creating log database...")

    log_database = ChromaDatabase(
        collection_name="phase16_log_test",
        persist_directory="data/test_phase16_log",
    )

    log_database.clear()

    print(
        "Log Database: PASS"
    )

    # ----------------------------------------------------------
    # Step 3 — Create knowledge database
    # ----------------------------------------------------------

    print("\n[3] Creating knowledge database...")

    knowledge_database = ChromaDatabase(
        collection_name="phase16_knowledge_test",
        persist_directory="data/test_phase16_knowledge",
    )

    knowledge_database.clear()

    print(
        "Knowledge Database: PASS"
    )

    # ----------------------------------------------------------
    # Step 4 — Create retrievers
    # ----------------------------------------------------------

    print("\n[4] Creating retrievers...")

    log_retriever = Retriever(
        database=log_database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    knowledge_retriever = KnowledgeRetriever(
        database=knowledge_database,
        embedding_manager=embedding_manager,
        top_k=2,
    )

    print(
        "Log Retriever: PASS"
    )

    print(
        "Knowledge Retriever: PASS"
    )

    # ----------------------------------------------------------
    # Step 5 — Create log records
    # ----------------------------------------------------------

    log_records = [
        {
            "id": "e2e_log_001",
            "document": (
                "Failed password for root "
                "from 192.168.1.20 port 22 ssh2"
            ),
            "metadata": {
                "source": "auth.log",
                "log_type": "auth",
                "severity": "HIGH",
            },
        },
        {
            "id": "e2e_log_002",
            "document": (
                "Failed password for admin "
                "from 192.168.1.30 port 22 ssh2"
            ),
            "metadata": {
                "source": "auth.log",
                "log_type": "auth",
                "severity": "HIGH",
            },
        },
        {
            "id": "e2e_log_003",
            "document": (
                "Successful login for user osboxes"
            ),
            "metadata": {
                "source": "auth.log",
                "log_type": "auth",
                "severity": "INFO",
            },
        },
    ]

    print(
        "\nLog Records:",
        len(log_records)
    )

    # ----------------------------------------------------------
    # Step 6 — Generate log embeddings
    # ----------------------------------------------------------

    log_texts = [
        record["document"]
        for record in log_records
    ]

    log_embeddings = (
        embedding_manager.embed_texts(
            log_texts
        )
    )

    print(
        "Log Embedding Shape:",
        log_embeddings.shape
    )

    # ----------------------------------------------------------
    # Step 7 — Store log records
    # ----------------------------------------------------------

    log_database.add(
        ids=[
            record["id"]
            for record in log_records
        ],
        documents=log_texts,
        embeddings=log_embeddings.tolist(),
        metadatas=[
            record["metadata"]
            for record in log_records
        ],
    )

    print(
        "Log Vectors Stored:",
        log_database.count()
    )

    # ----------------------------------------------------------
    # Step 8 — Create security knowledge
    # ----------------------------------------------------------

    knowledge_records = [
        {
            "id": "e2e_kb_001",
            "document": (
                "Repeated failed SSH authentication "
                "attempts may indicate a brute-force attack."
            ),
            "metadata": {
                "source": "security_knowledge.txt",
                "category": "authentication",
            },
        },
        {
            "id": "e2e_kb_002",
            "document": (
                "Brute-force attacks involve repeated "
                "authentication attempts against a service."
            ),
            "metadata": {
                "source": "security_knowledge.txt",
                "category": "authentication",
            },
        },
    ]

    print(
        "Knowledge Records:",
        len(knowledge_records)
    )

    # ----------------------------------------------------------
    # Step 9 — Generate knowledge embeddings
    # ----------------------------------------------------------

    knowledge_texts = [
        record["document"]
        for record in knowledge_records
    ]

    knowledge_embeddings = (
        embedding_manager.embed_texts(
            knowledge_texts
        )
    )

    print(
        "Knowledge Embedding Shape:",
        knowledge_embeddings.shape
    )

    # ----------------------------------------------------------
    # Step 10 — Store knowledge records
    # ----------------------------------------------------------

    knowledge_database.add(
        ids=[
            record["id"]
            for record in knowledge_records
        ],
        documents=knowledge_texts,
        embeddings=knowledge_embeddings.tolist(),
        metadatas=[
            record["metadata"]
            for record in knowledge_records
        ],
    )

    print(
        "Knowledge Vectors Stored:",
        knowledge_database.count()
    )

    # ----------------------------------------------------------
    # Step 11 — Create ContextBuilder
    # ----------------------------------------------------------

    print(
        "\n[5] Creating ContextBuilder..."
    )

    context_builder = ContextBuilder(
        log_retriever=log_retriever,
        knowledge_retriever=knowledge_retriever,
        top_k_logs=2,
        top_k_knowledge=2,
    )

    print(
        "Context Builder Information:"
    )

    print(
        context_builder.info()
    )

    # ----------------------------------------------------------
    # Step 12 — Retrieve RAG context
    # ----------------------------------------------------------

    query = (
        "failed SSH authentication "
        "brute force attack"
    )

    print(
        "\nQuery:"
    )

    print(
        query
    )

    context = context_builder.build(
        query
    )

    if not isinstance(
        context,
        RAGContext,
    ):

        raise AssertionError(
            "ContextBuilder did not return RAGContext."
        )

    print(
        "\nRAGContext"
    )

    print(
        context
    )

    # ----------------------------------------------------------
    # Validate log retrieval
    # ----------------------------------------------------------

    if len(
        context.log_results
    ) != 2:

        raise AssertionError(
            "Expected 2 retrieved log results."
        )

    print(
        "\nLog Retrieval: PASS"
    )

    # ----------------------------------------------------------
    # Validate knowledge retrieval
    # ----------------------------------------------------------

    if len(
        context.knowledge_results
    ) != 2:

        raise AssertionError(
            "Expected 2 retrieved knowledge results."
        )

    print(
        "Knowledge Retrieval: PASS"
    )

    print(
        "Context Builder: PASS"
    )

    # ----------------------------------------------------------
    # Display retrieved evidence
    # ----------------------------------------------------------

    print(
        "\nRetrieved Log Evidence"
    )

    for index, result in enumerate(
        context.log_results,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            "Document:",
            result.get("document")
        )

        print(
            "Metadata:",
            result.get("metadata")
        )

        print(
            "Distance:",
            result.get("distance")
        )

    print(
        "\nRetrieved Security Knowledge"
    )

    for index, result in enumerate(
        context.knowledge_results,
        start=1,
    ):

        print(
            f"\nResult {index}"
        )

        print(
            "Document:",
            result.get("document")
        )

        print(
            "Metadata:",
            result.get("metadata")
        )

        print(
            "Distance:",
            result.get("distance")
        )

    # ----------------------------------------------------------
    # Step 13 — Build LLM prompt
    # ----------------------------------------------------------

    print(
        "\n[6] Building LLM prompt..."
    )

    prompt_builder = PromptBuilder()

    prompt = prompt_builder.build(
        context
    )

    if not prompt:

        raise AssertionError(
            "Generated prompt is empty."
        )

    if query not in prompt:

        raise AssertionError(
            "Query is missing from prompt."
        )

    if "Failed password" not in prompt:

        raise AssertionError(
            "Log evidence is missing from prompt."
        )

    if "brute-force" not in prompt.lower():

        raise AssertionError(
            "Security knowledge is missing from prompt."
        )

    print(
        "Prompt Builder: PASS"
    )

    print(
        "Prompt Length:",
        len(prompt),
        "characters"
    )

    # ----------------------------------------------------------
    # Step 14 — Initialise LLM
    # ----------------------------------------------------------

    print(
        "\n[7] Initialising local LLM..."
    )

    llm_client = LLMClient()

    print(
        "LLM Information:"
    )

    print(
        llm_client.info()
    )

    # ----------------------------------------------------------
    # Check Ollama
    # ----------------------------------------------------------

    if not llm_client.is_available():

        raise RuntimeError(
            "Ollama is not available."
        )

    print(
        "Ollama Availability: PASS"
    )

    # ----------------------------------------------------------
    # Check Model
    # ----------------------------------------------------------

    if not llm_client.model_available():

        raise RuntimeError(
            "llama3.1:8b is not available."
        )

    print(
        "Model Availability: PASS"
    )

    # ----------------------------------------------------------
    # Step 15 — Generate security analysis
    # ----------------------------------------------------------

    print(
        "\nGenerating LLM security analysis..."
    )

    print(
        "Model: llama3.1:8b"
    )

    print(
        "Please wait..."
    )

    response = llm_client.generate(
        prompt
    )

    # ----------------------------------------------------------
    # Validate LLM response
    # ----------------------------------------------------------

    if not isinstance(
        response,
        LLMResponse,
    ):

        raise AssertionError(
            "LLM did not return LLMResponse."
        )

    if not response.answer:

        raise AssertionError(
            "LLM returned an empty answer."
        )

    print(
        "\nLLM Generation: PASS"
    )

    # ----------------------------------------------------------
    # Step 16 — Display final security analysis
    # ----------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "FINAL SECURITY ANALYSIS"
    )

    print(
        "=" * 70
    )

    print(
        response.answer
    )

    # ----------------------------------------------------------
    # Step 17 — Verify relevance
    # ----------------------------------------------------------

    answer_lower = (
        response.answer.lower()
    )

    relevant_terms = [
        "ssh",
        "authentication",
        "failed",
    ]

    found_terms = [
        term
        for term in relevant_terms
        if term in answer_lower
    ]

    print(
        "\nRelevant Terms Found"
    )

    print(
        found_terms
    )

    if len(
        found_terms
    ) < 2:

        raise AssertionError(
            "Generated analysis does not appear "
            "relevant to the security query."
        )

    print(
        "Security Analysis Relevance: PASS"
    )

    # ----------------------------------------------------------
    # Step 18 — Cleanup
    # ----------------------------------------------------------

    print(
        "\n[8] Cleaning test databases..."
    )

    log_database.clear()

    knowledge_database.clear()

    print(
        "Cleanup: PASS"
    )

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "PHASE 16 END-TO-END SECURITY ANALYSIS TEST PASSED"
    )

    print(
        "=" * 70
    )


# --------------------------------------------------------------
# Entry Point
# --------------------------------------------------------------

if __name__ == "__main__":

    main()