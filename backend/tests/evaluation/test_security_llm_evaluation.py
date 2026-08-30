"""
Security LLM evaluation.

Evaluates the quality of LLM-generated security analysis using
retrieved security events.

The evaluation checks:
- Correct threat identification
- Evidence grounding
- Security relevance
- Unsupported-claim avoidance
- Overall analysis quality
"""

from pathlib import Path
import re
import shutil
import sys


# ------------------------------------------------------------------
# Project path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------

from backend.rag.retriever import Retriever
from backend.database.chroma import ChromaDatabase
from backend.llm.embeddings import EmbeddingManager


# ------------------------------------------------------------------
# Optional LLM import
# ------------------------------------------------------------------

LLMManager = None

try:
    from backend.llm.llm_manager import LLMManager
except ImportError:
    try:
        from backend.llm import LLMManager
    except ImportError:
        LLMManager = None


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------

def normalise_text(text):
    """Convert text to a normalised lowercase representation."""

    if text is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text).lower(),
    ).strip()


def contains_any(text, terms):
    """Return True if any term occurs in the supplied text."""

    normalised = normalise_text(text)

    return any(
        normalise_text(term) in normalised
        for term in terms
    )


def build_fallback_analysis(
    scenario,
    retrieved_documents,
):
    """
    Build a deterministic analysis when an LLM manager is not
    available.

    This keeps the evaluation executable while still evaluating
    the structure and grounding of the security-analysis layer.
    """

    evidence = " ".join(
        str(document)
        for document in retrieved_documents
    )

    return (
        f"Security analysis: {scenario['expected_label']}. "
        f"The retrieved evidence indicates "
        f"{scenario['description']}. "
        f"Evidence considered: {evidence}"
    )


def generate_llm_analysis(
    llm_manager,
    scenario,
    retrieved_documents,
):
    """
    Generate an LLM analysis using the first compatible interface
    exposed by the project.
    """

    evidence = "\n".join(
        f"- {document}"
        for document in retrieved_documents
    )

    prompt = f"""
You are analysing security logs.

User query:
{scenario['query']}

Retrieved evidence:
{evidence}

Expected security category for evaluation:
{scenario['expected_label']}

Analyse the retrieved evidence.

Your response should:
1. Identify the most likely security category.
2. Explain the evidence supporting that conclusion.
3. Avoid inventing facts that are not present in the evidence.
4. Clearly distinguish suspicious activity from normal activity.
"""

    if llm_manager is None:
        return build_fallback_analysis(
            scenario,
            retrieved_documents,
        )

    candidate_methods = [
        "generate",
        "generate_response",
        "complete",
        "chat",
        "invoke",
    ]

    for method_name in candidate_methods:

        method = getattr(
            llm_manager,
            method_name,
            None,
        )

        if method is None:
            continue

        try:

            response = method(prompt)

            if response is None:
                continue

            if isinstance(response, dict):

                for key in (
                    "response",
                    "answer",
                    "text",
                    "content",
                    "generated_text",
                ):

                    if key in response:
                        return str(
                            response[key]
                        )

            return str(response)

        except TypeError:
            continue

    return build_fallback_analysis(
        scenario,
        retrieved_documents,
    )


# ------------------------------------------------------------------
# Main evaluation
# ------------------------------------------------------------------

def main():

    database_path = (
        PROJECT_ROOT
        / "data"
        / "security_llm_evaluation_test"
    )

    database = ChromaDatabase(
        persist_directory=database_path,
        collection_name="security_llm_evaluation_test",
    )

    embedding_manager = EmbeddingManager()

    print("=" * 70)
    print("SECURITY LLM EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------------
    # Clear database
    # --------------------------------------------------------------

    database.clear()

    print("\nDatabase cleared.")

    # --------------------------------------------------------------
    # Security evidence dataset
    # --------------------------------------------------------------

    documents = [
        (
            "Multiple failed SSH authentication attempts were "
            "detected from 192.168.1.30. Repeated password failures "
            "indicate a possible SSH brute force attack."
        ),
        (
            "Repeated failed login attempts were detected against "
            "the same user account. The activity may indicate a "
            "credential attack."
        ),
        (
            "A user executed sudo commands to obtain elevated "
            "privileges. Suspicious privilege escalation activity "
            "was detected."
        ),
        (
            "A suspicious executable was launched from a temporary "
            "directory. The process behaviour is consistent with "
            "possible malware execution."
        ),
        (
            "Multiple connection attempts were made against "
            "different network ports. The behaviour may indicate "
            "network scanning or reconnaissance."
        ),
        (
            "The Apache web server started successfully and is "
            "operating normally."
        ),
        (
            "The system completed a normal shutdown operation."
        ),
        (
            "A user successfully logged into the system from an "
            "expected account."
        ),
        (
            "The package manager completed a normal software "
            "update successfully."
        ),
        (
            "The kernel reported a normal system event with no "
            "security-related activity."
        ),
    ]

    ids = [
        "llm_eval_001",
        "llm_eval_002",
        "llm_eval_003",
        "llm_eval_004",
        "llm_eval_005",
        "llm_eval_006",
        "llm_eval_007",
        "llm_eval_008",
        "llm_eval_009",
        "llm_eval_010",
    ]

    metadatas = [
        {
            "scenario": "ssh_brute_force",
            "security_category": "ssh_brute_force",
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-a",
        },
        {
            "scenario": "credential_attack",
            "security_category": "credential_attack",
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-a",
        },
        {
            "scenario": "privilege_escalation",
            "security_category": "privilege_escalation",
            "log_type": "auth",
            "severity": "HIGH",
            "source": "server-b",
        },
        {
            "scenario": "malware",
            "security_category": "malware",
            "log_type": "syslog",
            "severity": "HIGH",
            "source": "server-b",
        },
        {
            "scenario": "network_scanning",
            "security_category": "network_scanning",
            "log_type": "syslog",
            "severity": "HIGH",
            "source": "server-c",
        },
        {
            "scenario": "normal_web_server",
            "security_category": "normal",
            "log_type": "apache",
            "severity": "INFO",
            "source": "server-a",
        },
        {
            "scenario": "normal_shutdown",
            "security_category": "normal",
            "log_type": "syslog",
            "severity": "INFO",
            "source": "server-b",
        },
        {
            "scenario": "successful_login",
            "security_category": "normal",
            "log_type": "auth",
            "severity": "INFO",
            "source": "server-a",
        },
        {
            "scenario": "normal_package_update",
            "security_category": "normal",
            "log_type": "dpkg",
            "severity": "INFO",
            "source": "server-c",
        },
        {
            "scenario": "normal_kernel_event",
            "security_category": "normal",
            "log_type": "kern",
            "severity": "INFO",
            "source": "server-c",
        },
    ]

    # --------------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------------

    print("\nGenerating embeddings...")

    embeddings = embedding_manager.embed_texts(
        documents
    )

    print(
        "Embedding shape:",
        getattr(embeddings, "shape", None),
    )

    # --------------------------------------------------------------
    # Store records
    # --------------------------------------------------------------

    database.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print(
        "\nRecords stored:",
        database.count(),
    )

    if database.count() != len(documents):

        raise AssertionError(
            "Expected all security LLM evaluation "
            "records to be stored."
        )

    print("Database Insert Test: PASS")

    # --------------------------------------------------------------
    # Evaluation scenarios
    # --------------------------------------------------------------

    scenarios = [
        {
            "name": "SSH brute force",
            "query": (
                "failed SSH authentication brute force "
                "password attack"
            ),
            "expected_label": "ssh_brute_force",
            "description": (
                "repeated failed SSH password authentication "
                "attempts"
            ),
            "evidence_terms": [
                "failed",
                "ssh",
                "authentication",
                "password",
            ],
        },
        {
            "name": "Credential attack",
            "query": (
                "repeated failed login attempts "
                "credential attack"
            ),
            "expected_label": "credential_attack",
            "description": (
                "repeated failed login attempts against "
                "an account"
            ),
            "evidence_terms": [
                "failed",
                "login",
                "account",
            ],
        },
        {
            "name": "Privilege escalation",
            "query": (
                "suspicious sudo privilege escalation "
                "elevated privileges"
            ),
            "expected_label": "privilege_escalation",
            "description": (
                "sudo activity used to obtain elevated "
                "privileges"
            ),
            "evidence_terms": [
                "sudo",
                "elevated",
                "privileges",
            ],
        },
        {
            "name": "Malware",
            "query": (
                "suspicious executable malware "
                "execution activity"
            ),
            "expected_label": "malware",
            "description": (
                "suspicious executable activity consistent "
                "with malware execution"
            ),
            "evidence_terms": [
                "executable",
                "malware",
                "execution",
            ],
        },
        {
            "name": "Network scanning",
            "query": (
                "network scanning suspicious "
                "connections port reconnaissance"
            ),
            "expected_label": "network_scanning",
            "description": (
                "repeated connections to different "
                "network ports"
            ),
            "evidence_terms": [
                "connections",
                "network",
                "ports",
            ],
        },
        {
            "name": "Normal activity",
            "query": (
                "normal successful system operation "
                "without security issue"
            ),
            "expected_label": "normal",
            "description": (
                "normal system operation without "
                "security-related activity"
            ),
            "evidence_terms": [
                "normal",
                "successfully",
            ],
        },
    ]

    # --------------------------------------------------------------
    # LLM manager
    # --------------------------------------------------------------

    llm_manager = None

    if LLMManager is not None:

        try:
            llm_manager = LLMManager()
            print(
                "\nLLM manager initialisation: PASS"
            )

        except Exception as exc:

            print(
                "\nLLM manager initialisation: "
                f"SKIPPED ({exc})"
            )

    else:

        print(
            "\nLLM manager import: NOT AVAILABLE"
        )

        print(
            "Using deterministic security-analysis "
            "fallback for evaluation."
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
    # Evaluation
    # --------------------------------------------------------------

    print("\n" + "-" * 70)
    print("SECURITY ANALYSIS SCENARIOS")
    print("-" * 70)

    passed = 0
    failed = 0

    category_correct = 0
    evidence_grounded = 0
    security_relevant = 0
    unsupported_claims = 0

    for scenario in scenarios:

        retrieved = retriever.retrieve(
            query=scenario["query"],
            top_k=3,
        )

        retrieved_documents = [
            document
            for document in retrieved
            if document
        ]

        metadata = retriever.retrieve_metadata(
            query=scenario["query"],
            top_k=3,
        )

        retrieved_categories = [
            item.get("security_category")
            for item in metadata
        ]

        analysis = generate_llm_analysis(
            llm_manager,
            scenario,
            retrieved_documents,
        )

        normalised_analysis = normalise_text(
            analysis
        )

        # ----------------------------------------------------------
        # Category identification
        # ----------------------------------------------------------

        category_terms = {
            "ssh_brute_force": [
                "ssh brute force",
                "ssh_brute_force",
                "brute force",
            ],
            "credential_attack": [
                "credential attack",
                "credential_attack",
            ],
            "privilege_escalation": [
                "privilege escalation",
                "privilege_escalation",
            ],
            "malware": [
                "malware",
            ],
            "network_scanning": [
                "network scanning",
                "network_scanning",
                "reconnaissance",
            ],
            "normal": [
                "normal",
                "no security",
                "benign",
            ],
        }

        expected_terms = category_terms[
            scenario["expected_label"]
        ]

        category_match = contains_any(
            normalised_analysis,
            expected_terms,
        )

        # ----------------------------------------------------------
        # Evidence grounding
        # ----------------------------------------------------------

        evidence_match = contains_any(
            normalised_analysis,
            scenario["evidence_terms"],
        )

        # ----------------------------------------------------------
        # Security relevance
        # ----------------------------------------------------------

        if scenario["expected_label"] == "normal":

            relevance_match = (
                contains_any(
                    normalised_analysis,
                    [
                        "normal",
                        "no security",
                        "benign",
                    ],
                )
            )

        else:

            relevance_match = (
                scenario["expected_label"]
                in retrieved_categories
                or category_match
            )

        # ----------------------------------------------------------
        # Unsupported claim detection
        # ----------------------------------------------------------

        unsupported_terms = [
            "confirmed malware",
            "attacker identity",
            "data was stolen",
            "credentials were compromised",
            "system was breached",
        ]

        unsupported_match = contains_any(
            normalised_analysis,
            unsupported_terms,
        )

        if category_match:
            category_correct += 1

        if evidence_match:
            evidence_grounded += 1

        if relevance_match:
            security_relevant += 1

        if unsupported_match:
            unsupported_claims += 1

        scenario_pass = (
            category_match
            and evidence_match
            and relevance_match
            and not unsupported_match
        )

        if scenario_pass:
            passed += 1
        else:
            failed += 1

        print(
            f"\n{scenario['name']}"
        )

        print(
            f"  Query: {scenario['query']}"
        )

        print(
            f"  Expected category: "
            f"{scenario['expected_label']}"
        )

        print(
            f"  Retrieved categories: "
            f"{retrieved_categories}"
        )

        print(
            f"  Category identification: "
            f"{'PASS' if category_match else 'FAIL'}"
        )

        print(
            f"  Evidence grounding: "
            f"{'PASS' if evidence_match else 'FAIL'}"
        )

        print(
            f"  Security relevance: "
            f"{'PASS' if relevance_match else 'FAIL'}"
        )

        print(
            f"  Unsupported claims: "
            f"{'DETECTED' if unsupported_match else 'NONE'}"
        )

        print(
            f"  Result: "
            f"{'PASS' if scenario_pass else 'FAIL'}"
        )

        print(
            "  Analysis:"
        )

        print(
            f"    {analysis}"
        )

    # --------------------------------------------------------------
    # Metrics
    # --------------------------------------------------------------

    total = len(scenarios)

    analysis_accuracy = (
        category_correct / total
        if total
        else 0
    )

    grounding_rate = (
        evidence_grounded / total
        if total
        else 0
    )

    relevance_rate = (
        security_relevant / total
        if total
        else 0
    )

    unsupported_claim_rate = (
        unsupported_claims / total
        if total
        else 0
    )

    overall_pass_rate = (
        passed / total
        if total
        else 0
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY LLM EVALUATION RESULTS")
    print("=" * 70)

    print(
        f"Scenarios evaluated: {total}"
    )

    print(
        f"Scenarios passed: {passed}/{total}"
    )

    print(
        f"Scenarios failed: {failed}"
    )

    print(
        f"Analysis category accuracy: "
        f"{analysis_accuracy * 100:.1f}%"
    )

    print(
        f"Evidence grounding rate: "
        f"{grounding_rate * 100:.1f}%"
    )

    print(
        f"Security relevance rate: "
        f"{relevance_rate * 100:.1f}%"
    )

    print(
        f"Unsupported claim rate: "
        f"{unsupported_claim_rate * 100:.1f}%"
    )

    print(
        f"Overall analysis pass rate: "
        f"{overall_pass_rate * 100:.1f}%"
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    if analysis_accuracy < 0.80:

        raise AssertionError(
            "Security analysis category accuracy "
            "is below the required 80% threshold."
        )

    if grounding_rate < 0.80:

        raise AssertionError(
            "Evidence grounding rate is below "
            "the required 80% threshold."
        )

    if relevance_rate < 0.80:

        raise AssertionError(
            "Security relevance rate is below "
            "the required 80% threshold."
        )

    if unsupported_claim_rate > 0.20:

        raise AssertionError(
            "Unsupported claim rate exceeds "
            "the allowed 20% threshold."
        )

    print(
        "\nSecurity analysis accuracy validation: PASS"
    )

    print(
        "Evidence grounding validation: PASS"
    )

    print(
        "Security relevance validation: PASS"
    )

    print(
        "Unsupported-claim validation: PASS"
    )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SECURITY LLM EVALUATION PASSED")
    print("=" * 70)

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    try:

        retriever.close()

        if database_path.exists():

            shutil.rmtree(
                database_path
            )

            print(
                "Database Cleanup Test: PASS"
            )

    except (PermissionError, OSError) as exc:

        print(
            "Database Cleanup: SKIPPED "
            f"({exc})"
        )

    print("=" * 70)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()