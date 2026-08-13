"""
analysis_parser.py

Parses an LLM security response into a structured
SecurityAnalysis object.
"""

import re

from .security_analysis import SecurityAnalysis


class AnalysisParser:
    """
    Converts an LLM response containing a security analysis
    into a structured SecurityAnalysis object.

    The parser intentionally does not import LLMResponse.
    This avoids a circular dependency between the generation
    and analysis packages.
    """

    # ----------------------------------------------------------
    # Parse Response
    # ----------------------------------------------------------

    def parse(self, response):
        """
        Parse an LLM response into SecurityAnalysis.

        The response must provide:
            - answer
            - metadata
        """

        if not hasattr(response, "answer"):
            raise TypeError(
                "response must provide an 'answer' attribute."
            )

        if not hasattr(response, "metadata"):
            raise TypeError(
                "response must provide a 'metadata' attribute."
            )

        answer = response.answer.strip()

        if not answer:
            raise ValueError(
                "LLM response answer cannot be empty."
            )

        # ------------------------------------------------------
        # Extract Sections
        # ------------------------------------------------------

        threat_assessment = self._extract_section(
            answer,
            "THREAT ASSESSMENT",
            [
                "EVIDENCE",
            ],
        )

        evidence_text = self._extract_section(
            answer,
            "EVIDENCE",
            [
                "SECURITY INTERPRETATION",
            ],
        )

        interpretation = self._extract_section(
            answer,
            "SECURITY INTERPRETATION",
            [
                "SEVERITY",
            ],
        )

        severity_text = self._extract_section(
            answer,
            "SEVERITY",
            [
                "RECOMMENDED ACTIONS",
            ],
        )

        actions_text = self._extract_section(
            answer,
            "RECOMMENDED ACTIONS",
            [
                "LIMITATIONS",
                "Note:",
            ],
        )

        limitations = self._extract_limitations(
            answer
        )

        # ------------------------------------------------------
        # Parse Lists
        # ------------------------------------------------------

        evidence = self._parse_list(
            evidence_text
        )

        recommended_actions = self._parse_list(
            actions_text
        )

        # ------------------------------------------------------
        # Parse Severity
        # ------------------------------------------------------

        severity = self._clean_severity(
            severity_text
        )

        # ------------------------------------------------------
        # Metadata
        # ------------------------------------------------------

        metadata = dict(
            response.metadata
        )

        metadata.update({
            "parsed": True,
            "parser": "AnalysisParser",
        })

        # ------------------------------------------------------
        # Create Structured Analysis
        # ------------------------------------------------------

        return SecurityAnalysis(
            threat_assessment=(
                self._clean_text(
                    threat_assessment
                )
            ),
            evidence=evidence,
            security_interpretation=(
                self._clean_text(
                    interpretation
                )
            ),
            severity=severity,
            recommended_actions=(
                recommended_actions
            ),
            limitations=(
                self._clean_text(
                    limitations
                )
            ),
            metadata=metadata,
        )

    # ----------------------------------------------------------
    # Section Extraction
    # ----------------------------------------------------------

    def _extract_section(
        self,
        text,
        heading,
        next_headings,
    ):
        """
        Extract text between one heading and the next
        recognised heading.

        Supported heading formats include:

            THREAT ASSESSMENT

            **THREAT ASSESSMENT**

            ## THREAT ASSESSMENT

            ### **THREAT ASSESSMENT**
        """

        heading_pattern = (
            r"(?:^|\n)"
            r"\s*"
            r"(?:#{1,6}\s*)?"
            r"(?:\*\*)?"
            + re.escape(heading)
            + r"(?:\*\*)?"
            r"\s*:?"
            r"\s*\n"
        )

        match = re.search(
            heading_pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return ""

        start = match.end()

        # ------------------------------------------------------
        # Find Next Heading
        # ------------------------------------------------------

        if next_headings:

            next_pattern = (
                r"(?:^|\n)"
                r"\s*"
                r"(?:#{1,6}\s*)?"
                r"(?:\*\*)?"
                r"(?:"
                + "|".join(
                    re.escape(item)
                    for item in next_headings
                )
                + r")"
                r"(?:\*\*)?"
                r"\s*:?"
                r"\s*(?:\n|$)"
            )

            next_match = re.search(
                next_pattern,
                text[start:],
                flags=re.IGNORECASE,
            )

            if next_match:

                end = (
                    start
                    + next_match.start()
                )

                return text[
                    start:end
                ].strip()

        return text[
            start:
        ].strip()

    # ----------------------------------------------------------
    # Limitations
    # ----------------------------------------------------------

    def _extract_limitations(
        self,
        text,
    ):
        """
        Extract either:

            LIMITATIONS

        or a trailing:

            Note: ...
        """

        section = self._extract_section(
            text,
            "LIMITATIONS",
            [],
        )

        if section:
            return section.strip()

        # ------------------------------------------------------
        # Note Format
        # ------------------------------------------------------

        note_match = re.search(
            r"(?:^|\n)"
            r"\s*(?:\*\*)?"
            r"Note:"
            r"(?:\*\*)?"
            r"\s*(.*)$",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if note_match:

            return note_match.group(
                1
            ).strip()

        return ""

    # ----------------------------------------------------------
    # List Parsing
    # ----------------------------------------------------------

    def _parse_list(
        self,
        text,
    ):
        """
        Convert numbered and bullet-point text into
        individual list items.

        Supported formats:

            1. Item
            2. Item

            1) Item
            2) Item

            - Item
            - Item

            * Item
            * Item

            • Item
            • Item

        Continuation lines are attached to the previous item.
        """

        if not text:
            return []

        lines = text.splitlines()

        items = []

        current_item = None

        for raw_line in lines:

            line = raw_line.strip()

            if not line:
                continue

            # --------------------------------------------------
            # Remove standalone Markdown emphasis
            # --------------------------------------------------

            line = re.sub(
                r"^\*\*(.*?)\*\*$",
                r"\1",
                line,
            ).strip()

            # --------------------------------------------------
            # Numbered Item
            # --------------------------------------------------

            numbered = re.match(
                r"^\s*\d+[\.\)]\s+(.*)",
                line,
            )

            if numbered:

                if current_item:

                    items.append(
                        self._clean_list_item(
                            current_item
                        )
                    )

                current_item = (
                    numbered.group(1)
                    .strip()
                )

                continue

            # --------------------------------------------------
            # Bullet Item
            # --------------------------------------------------

            bullet = re.match(
                r"^\s*[-*•]\s+(.*)",
                line,
            )

            if bullet:

                if current_item:

                    items.append(
                        self._clean_list_item(
                            current_item
                        )
                    )

                current_item = (
                    bullet.group(1)
                    .strip()
                )

                continue

            # --------------------------------------------------
            # Continuation Line
            # --------------------------------------------------

            if current_item:

                current_item += (
                    " " + line
                )

            else:

                current_item = line

        # ------------------------------------------------------
        # Add Final Item
        # ------------------------------------------------------

        if current_item:

            items.append(
                self._clean_list_item(
                    current_item
                )
            )

        return [
            item
            for item in items
            if item
        ]

    # ----------------------------------------------------------
    # List Item Cleaning
    # ----------------------------------------------------------

    def _clean_list_item(
        self,
        text,
    ):
        """
        Clean Markdown formatting and whitespace
        from an individual list item.
        """

        text = text.strip()

        # Remove leading bullets.
        text = re.sub(
            r"^[-*•]\s+",
            "",
            text,
        )

        # Remove Markdown emphasis.
        text = text.replace(
            "**",
            "",
        )

        # Normalise repeated whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ----------------------------------------------------------
    # Severity
    # ----------------------------------------------------------

    def _clean_severity(
        self,
        text,
    ):
        """
        Extract a recognised severity value.

        Supported values:

            LOW
            MEDIUM
            HIGH
            CRITICAL
        """

        if not text:
            return ""

        match = re.search(
            r"\b"
            r"(LOW|MEDIUM|HIGH|CRITICAL)"
            r"\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return text.strip()

        return match.group(
            1
        ).upper()

    # ----------------------------------------------------------
    # General Text Cleaning
    # ----------------------------------------------------------

    def _clean_text(
        self,
        text,
    ):
        """
        Clean Markdown formatting and whitespace.
        """

        if not text:
            return ""

        # Remove Markdown emphasis.
        text = text.replace(
            "**",
            "",
        )

        # Normalise whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return parser information.
        """

        return {
            "component": "AnalysisParser",
            "purpose": (
                "Parse LLM security analysis "
                "into structured fields"
            ),
            "output": "SecurityAnalysis",
        }

    # ----------------------------------------------------------
    # Representation
    # ----------------------------------------------------------

    def __repr__(self):

        return (
            "AnalysisParser("
            "output='SecurityAnalysis')"
        )