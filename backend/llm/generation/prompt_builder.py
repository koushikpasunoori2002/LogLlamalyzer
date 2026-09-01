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

        # ------------------------------------------------------
        # Application-provided evidence classification
        # ------------------------------------------------------

        evidence_classification = (
            context.metadata.get(
                "evidence_classification",
                "NOT SUPPORTED",
            )
        )

        prompt = f"""
You are a cybersecurity log analysis assistant.

Your task is to analyse security logs using the
retrieved evidence and security knowledge provided below.

IMPORTANT RULES:

1. Base your analysis only on the retrieved evidence.

2. The LOG EVIDENCE section contains the actual log records
   retrieved from the system.

3. Describe what the logs actually show before interpreting them.

4. Do not describe the user's query as if it were a log event.

5. Do not invent events, users, IP addresses, commands,
   timestamps, attack details, or outcomes.

6. Do not assume that a security-related event is automatically
   evidence of the specific threat in the query.

7. Only state that a threat is supported when the retrieved logs
   contain evidence directly relevant to that threat.

8. Distinguish between:

   - DIRECT EVIDENCE: the log explicitly shows behaviour related
     to the queried threat.

   - INDIRECT EVIDENCE: the log is security-related but does not
     directly establish the queried threat.

   - INSUFFICIENT EVIDENCE: the retrieved logs do not provide
     enough information to support the queried threat.

9. SESSION_OPEN and SESSION_CLOSE events must not be interpreted
   as failed authentication or brute-force attempts unless the
   logs contain explicit failed-authentication evidence.

10. AppArmor DENIED, kernel errors, audit events, or other generic
    security events must not automatically be classified as
    malware, intrusion, or attack activity.

11. Security knowledge may explain an observed event, but it must
    not be presented as observed log evidence.

12. When evidence is indirect or insufficient, explicitly say so.

13. Refer to actual fields such as timestamp, source, severity,
    event type, process, user, and message when available.

14. Provide a technically useful conclusion rather than a generic
    description of the queried attack.


PYTHON EVIDENCE CLASSIFICATION RULE

The application provides an evidence classification in the context
metadata field `evidence_classification`.

Use this classification as authoritative.

Do not change or contradict it.

If the classification is:

- NOT SUPPORTED: state that the queried threat is not established
  by the retrieved log evidence.

- POSSIBLE: state that related or privileged activity was observed,
  but the queried threat is not conclusively established.

- SUPPORTED: state that the retrieved evidence supports the queried
  threat.


SOURCE FIELD RULE

When referring to the log source, use the metadata field `source`.

Do not use `hostname` as the source identifier.

`hostname` identifies the machine that generated the event.
`source` identifies the synchronized log source/server.


CLASSIFICATION CONSISTENCY

The THREAT ASSESSMENT classification must agree with the evidence.

Do not output SUPPORTED and then state that the evidence is indirect
or insufficient.

If the evidence is indirect, the classification must be POSSIBLE.

If the evidence does not establish the queried threat, the
classification must be NOT SUPPORTED.


CLASSIFICATION

The application-provided classification is:

{evidence_classification}

Use this exact classification in your response.
Do not replace it with another classification.


Analyse the following security query:

{context.query}


Retrieved evidence:

{retrieved_context}


Provide the final answer in exactly this structure:

THREAT ASSESSMENT

{evidence_classification}

Give a brief explanation of why this classification applies.

SECURITY INTERPRETATION

Explain what the retrieved log evidence demonstrates and
what it does not demonstrate in relation to the query.

Use precise identity terminology:
- `source` identifies the synchronized log source/server.
- `hostname` identifies the machine that generated the log.
- Do not confuse `source` with `hostname`.
- For command execution events, describe the relationship between
  the account, process, and command exactly as shown by the log.

For sudo activity, describe it as privileged activity unless
the logs explicitly demonstrate unauthorized or malicious
privilege escalation.

IMPORTANT INTERPRETATION RULE

Never say that a user "successfully escalated privileges" merely
because a SUDO_COMMAND event exists.

A SUDO_COMMAND demonstrates that sudo was used to execute a command
with elevated privileges.

It does not by itself demonstrate:
- successful privilege escalation;
- unauthorized privilege escalation;
- malicious privilege escalation;
- compromise of the system.

Use wording such as:
"The logs show sudo activity associated with the osboxes account,
executing commands with root privileges."

Only state that privilege escalation occurred when the logs
explicitly demonstrate that outcome.

SEVERITY

State LOW, MEDIUM, HIGH, or CRITICAL based only on the retrieved
evidence.

RECOMMENDED ACTIONS

Provide 2-4 practical investigation or mitigation actions.

Do not reproduce individual log records.
Do not claim that privilege escalation succeeded unless the
retrieved logs explicitly demonstrate that outcome.
Do not create an EVIDENCE section.
Do not output prompt instructions, decision rules,
classification rules, or reasoning guidelines.
Do not repeat phrases such as "State the application-provided
classification" in the final answer.
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

        evidence_classification = (
            context.metadata.get(
                "evidence_classification",
                "NOT SUPPORTED",
            )
        )

        return (
            "Analyse the following security query "
            "using only the retrieved evidence.\n\n"

            f"QUERY:\n{context.query}\n\n"

            f"EVIDENCE CLASSIFICATION:\n"
            f"{evidence_classification}\n\n"

            f"EVIDENCE:\n{retrieved_context}\n\n"

            "Use the application-provided evidence classification "
            "exactly as given. Do not contradict it.\n\n"

            "Identify the relevant observations, explain their "
            "relationship to the query, state the classification, "
            "severity, and recommended actions. "
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