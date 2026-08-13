"""
prompt_builder.py

Builds structured security-analysis prompts from
Phase 15 RAG context.
"""

from backend.rag.context import RAGContext
from backend.rag.context import ContextFormatter


class PromptBuilder:
    """
    Builds prompts for local LLM security analysis.
    """

    def __init__(
        self,
        formatter=None,
    ):
        self.formatter = (
            formatter
            if formatter is not None
            else ContextFormatter()
        )

    # ----------------------------------------------------------
    # Build Security Analysis Prompt
    # ----------------------------------------------------------

    def build(self, context):
        """
        Build a complete security-analysis prompt.
        """

        if not isinstance(
            context,
            RAGContext,
        ):
            raise TypeError(
                "context must be a RAGContext."
            )

        retrieved_context = (
            self.formatter.format(context)
        )

        prompt = f"""
You are a cybersecurity log analysis assistant.

Your task is to analyse security logs using the
retrieved evidence and security knowledge provided below.

IMPORTANT RULES:

1. Base your analysis only on the retrieved evidence.
2. Do not invent log events, users, IP addresses,
   timestamps, or attack details.
3. Clearly distinguish observed evidence from
   security interpretation.
4. If the evidence is insufficient, explicitly say so.
5. Identify potential security threats when supported
   by the evidence.
6. Provide a concise and technically useful response.

Analyse the following security query:

{context.query}

Retrieved evidence:

{retrieved_context}

Provide your analysis using the following structure:

THREAT ASSESSMENT
State whether the evidence indicates a potential
security threat.

EVIDENCE
List the important observations from the retrieved logs.

SECURITY INTERPRETATION
Explain what the observed evidence may indicate.

SEVERITY
Provide an estimated severity:
LOW, MEDIUM, HIGH, or CRITICAL.

RECOMMENDED ACTIONS
Provide practical actions that could help investigate
or mitigate the potential threat.

If the evidence does not support a conclusion,
clearly state the limitation.
""".strip()

        return prompt

    # ----------------------------------------------------------
    # Short Prompt
    # ----------------------------------------------------------

    def build_analysis_prompt(self, context):
        """
        Build a concise analysis prompt.

        This is useful when context length needs to be reduced.
        """

        if not isinstance(
            context,
            RAGContext,
        ):
            raise TypeError(
                "context must be a RAGContext."
            )

        retrieved_context = (
            self.formatter.format(context)
        )

        return (
            "Analyse the following security query "
            "using only the retrieved evidence.\n\n"
            f"QUERY:\n{context.query}\n\n"
            f"EVIDENCE:\n{retrieved_context}\n\n"
            "Identify the potential threat, supporting "
            "evidence, severity, and recommended actions. "
            "Do not invent information."
        )

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return information about the prompt builder.
        """

        return {
            "component": "PromptBuilder",
            "purpose": "Security log analysis",
            "formatter": (
                self.formatter.__class__.__name__
            ),
        }

    def __repr__(self):

        return (
            "PromptBuilder("
            f"formatter="
            f"'{self.formatter.__class__.__name__}')"
        )