"""
security_analysis.py

Defines the structured security analysis produced from
an LLM security response.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SecurityAnalysis:
    """
    Represents a structured cybersecurity analysis.

    The class separates the major sections of the LLM-generated
    security analysis so they can be consumed by later components.
    """

    threat_assessment: str

    evidence: List[str] = field(
        default_factory=list
    )

    security_interpretation: str = ""

    severity: str = ""

    recommended_actions: List[str] = field(
        default_factory=list
    )

    limitations: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # ----------------------------------------------------------
    # Dictionary Conversion
    # ----------------------------------------------------------

    def to_dict(self):
        """
        Convert the security analysis to a dictionary.
        """

        return {
            "threat_assessment": self.threat_assessment,
            "evidence": self.evidence,
            "security_interpretation":
                self.security_interpretation,
            "severity": self.severity,
            "recommended_actions":
                self.recommended_actions,
            "limitations": self.limitations,
            "metadata": self.metadata,
        }

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    def is_valid(self):
        """
        Check whether the analysis contains the required
        security assessment fields.
        """

        if not self.threat_assessment:
            return False

        if not self.severity:
            return False

        if not self.security_interpretation:
            return False

        return True

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return information about the analysis.
        """

        return {
            "component": "SecurityAnalysis",
            "evidence_count": len(
                self.evidence
            ),
            "recommended_action_count": len(
                self.recommended_actions
            ),
            "severity": self.severity,
            "valid": self.is_valid(),
        }

    # ----------------------------------------------------------
    # String Representation
    # ----------------------------------------------------------

    def __str__(self):
        """
        Return a readable representation.
        """

        return (
            "Security Analysis\n"
            f"Threat Assessment : "
            f"{self.threat_assessment}\n"
            f"Evidence          : "
            f"{len(self.evidence)} items\n"
            f"Interpretation    : "
            f"{self.security_interpretation}\n"
            f"Severity          : "
            f"{self.severity}\n"
            f"Actions           : "
            f"{len(self.recommended_actions)} items\n"
            f"Limitations       : "
            f"{self.limitations}\n"
            f"Metadata          : "
            f"{self.metadata}"
        )

    def __repr__(self):

        return (
            "SecurityAnalysis("
            f"severity='{self.severity}', "
            f"evidence_count="
            f"{len(self.evidence)})"
        )