"""
retriever.py

Retrieves relevant log chunks from the vector database.
"""

from backend.llm.embeddings import EmbeddingManager
from backend.database.chroma import ChromaDatabase


class Retriever:
    """
    Retrieves relevant documents using embeddings
    and ChromaDB similarity search.

    Supports:

    - configurable top_k
    - optional source filtering
    - optional distance-threshold filtering
    - security-focused retrieval
    - document retrieval
    - metadata retrieval
    - scored retrieval
    """

    def __init__(
        self,
        database=None,
        embedding_manager=None,
        top_k=5,
        distance_threshold=None,
    ):
        """
        Initialize the retriever.
        """

        self.database = (
            database
            if database is not None
            else ChromaDatabase()
        )

        self.embedding_manager = (
            embedding_manager
            if embedding_manager is not None
            else EmbeddingManager()
        )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        self.top_k = top_k

        if distance_threshold is not None:

            if distance_threshold < 0:
                raise ValueError(
                    "distance_threshold must be "
                    "greater than or equal to 0."
                )

        self.distance_threshold = distance_threshold

    # ------------------------------------------------------------------
    # Main retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Retrieve documents relevant to a query.
        """

        if not query or not str(query).strip():

            raise ValueError(
                "Query cannot be empty."
            )

        number_of_results = (
            top_k
            if top_k is not None
            else self.top_k
        )

        if number_of_results <= 0:

            raise ValueError(
                "top_k must be greater than 0."
            )

        query_embedding = (
            self.embedding_manager.embed_text(
                str(query)
            )
        )

        where = None

        if source is not None:

            source_value = str(
                source
            ).strip()

            if not source_value:

                raise ValueError(
                    "source cannot be empty."
                )

            where = {
                "source": source_value
            }

        results = self.database.search(
            query_embedding=query_embedding,
            n_results=number_of_results,
            where=where,
        )

        if self.distance_threshold is None:

            return results

        return self._apply_distance_threshold(
            results
        )

    # ------------------------------------------------------------------
    # Security evidence retrieval
    # ------------------------------------------------------------------

    def retrieve_security_evidence(
        self,
        query,
        top_k=4,
        candidate_k=20,
        source=None,
    ):
        """
        Retrieve security-focused evidence.

        Semantic retrieval is performed first.

        For specific security intents, structured event types are
        also retrieved so explicit security events are not missed.

        Strict event filtering is applied only to security-specific
        intents where generic events could create false evidence:

            authentication
            privilege
            malware
            network_scan

        Generic and ordinary operational queries use semantic
        retrieval without strict security-event filtering.
        """

        if not isinstance(
            query,
            str,
        ):

            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:

            raise ValueError(
                "query cannot be empty."
            )

        if top_k <= 0:

            raise ValueError(
                "top_k must be greater than zero."
            )

        if candidate_k <= 0:

            raise ValueError(
                "candidate_k must be greater than zero."
            )

        # ----------------------------------------------------------
        # Detect query intent
        # ----------------------------------------------------------

        intent = self._detect_security_intent(
            query
        )

        # ----------------------------------------------------------
        # Strict security intents
        # ----------------------------------------------------------

        strict_security_intents = {
            "authentication",
            "privilege",
            "malware",
            "network_scan",
        }

        # ----------------------------------------------------------
        # Semantic candidate pool
        # ----------------------------------------------------------

        candidate_count = max(
            candidate_k,
            top_k,
        )

        candidates = self._semantic_candidates(
            query=query,
            top_k=candidate_count,
            source=source,
        )

        # ----------------------------------------------------------
        # Structured event types
        # ----------------------------------------------------------

        structured_events = []

        if intent == "authentication":

            structured_events = [
                "AUTH_FAILURE",
                "AUTH_FAILED",
                "LOGIN_FAILURE",
                "FAILED_LOGIN",
            ]

        elif intent == "privilege":

            structured_events = [
                "SUDO_COMMAND",
            ]

        elif intent == "network_scan":

            structured_events = [
                "NETWORK_SCAN",
                "PORT_SCAN",
                "RECONNAISSANCE",
                "SCANNING",
            ]

        elif intent == "malware":

            structured_events = [
                "MALWARE",
                "MALWARE_DETECTED",
                "MALICIOUS_EXECUTION",
                "SUSPICIOUS_EXECUTION",
            ]

        elif intent == "network":

            structured_events = [
                "NETWORK",
            ]

        # ----------------------------------------------------------
        # Retrieve structured matches
        # ----------------------------------------------------------

        if structured_events:

            for event_type in structured_events:

                where = {
                    "event_type": event_type
                }

                if source is not None:

                    source_value = str(
                        source
                    ).strip()

                    where = {
                        "$and": [
                            {
                                "event_type": event_type
                            },
                            {
                                "source": source_value
                            },
                        ]
                    }

                try:

                    results = (
                        self.database.collection.get(
                            where=where
                        )
                    )

                except Exception:

                    continue

                ids = results.get(
                    "ids",
                    [],
                )

                documents = results.get(
                    "documents",
                    [],
                )

                metadatas = results.get(
                    "metadatas",
                    [],
                )

                # --------------------------------------------------
                # Chroma .get() returns flat lists
                # --------------------------------------------------

                for index, document in enumerate(
                    documents
                ):

                    metadata = (
                        metadatas[index]
                        if index < len(metadatas)
                        and isinstance(
                            metadatas[index],
                            dict,
                        )
                        else {}
                    )

                    candidate_id = (
                        ids[index]
                        if index < len(ids)
                        else None
                    )

                    already_exists = any(
                        candidate.get("id")
                        == candidate_id
                        for candidate in candidates
                    )

                    if already_exists:

                        continue

                    candidates.append(
                        {
                            "id": candidate_id,
                            "document": document,
                            "metadata": metadata,
                            "distance": None,
                        }
                    )

        # ----------------------------------------------------------
        # No candidates
        # ----------------------------------------------------------

        if not candidates:

            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        # ----------------------------------------------------------
        # Rank candidates
        # ----------------------------------------------------------

        ranked = (
            self._rank_security_candidates(
                query=query,
                candidates=candidates,
                top_k=top_k,
            )
        )

        # ----------------------------------------------------------
        # Generic queries do not use strict event filtering
        # ----------------------------------------------------------

        if intent not in strict_security_intents:

            return ranked

        # ----------------------------------------------------------
        # Directly relevant event types
        # ----------------------------------------------------------

        relevant_events = {

            "authentication": {
                "AUTH_FAILURE",
                "AUTH_FAILED",
                "LOGIN_FAILURE",
                "FAILED_LOGIN",
            },

            "privilege": {
                "SUDO_COMMAND",
            },

            "malware": {
                "MALWARE",
                "MALWARE_DETECTED",
                "MALICIOUS_EXECUTION",
                "SUSPICIOUS_EXECUTION",
            },

            "network_scan": {
                "NETWORK_SCAN",
                "PORT_SCAN",
                "RECONNAISSANCE",
                "SCANNING",
            },
        }

        allowed_events = relevant_events.get(
            intent,
            set(),
        )

        # ----------------------------------------------------------
        # Extract ranked result lists
        # ----------------------------------------------------------

        ids = ranked.get(
            "ids",
            [[]],
        )

        documents = ranked.get(
            "documents",
            [[]],
        )

        metadatas = ranked.get(
            "metadatas",
            [[]],
        )

        distances = ranked.get(
            "distances",
            [[]],
        )

        ids = (
            ids[0]
            if ids
            and isinstance(
                ids[0],
                list,
            )
            else []
        )

        documents = (
            documents[0]
            if documents
            and isinstance(
                documents[0],
                list,
            )
            else []
        )

        metadatas = (
            metadatas[0]
            if metadatas
            and isinstance(
                metadatas[0],
                list,
            )
            else []
        )

        distances = (
            distances[0]
            if distances
            and isinstance(
                distances[0],
                list,
            )
            else []
        )

        # ----------------------------------------------------------
        # Keep only explicitly relevant event types
        # ----------------------------------------------------------

        keep = []

        for index, metadata in enumerate(
            metadatas
        ):

            if not isinstance(
                metadata,
                dict,
            ):

                continue

            event_type = str(
                metadata.get(
                    "event_type",
                    "",
                )
            ).upper()

            if event_type in allowed_events:

                keep.append(
                    index
                )

        # ----------------------------------------------------------
        # Return filtered results
        # ----------------------------------------------------------

        return {
            "ids": [[
                ids[index]
                for index in keep
                if index < len(ids)
            ]],

            "documents": [[
                documents[index]
                for index in keep
                if index < len(documents)
            ]],

            "metadatas": [[
                metadatas[index]
                for index in keep
                if index < len(metadatas)
            ]],

            "distances": [[
                distances[index]
                for index in keep
                if index < len(distances)
            ]],
        }

    # ------------------------------------------------------------------
    # Semantic candidates
    # ------------------------------------------------------------------

    def _semantic_candidates(
        self,
        query,
        top_k,
        source=None,
    ):
        """
        Retrieve a larger semantic candidate pool.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

        ids = results.get(
            "ids",
            [[]],
        )

        documents = results.get(
            "documents",
            [[]],
        )

        metadatas = results.get(
            "metadatas",
            [[]],
        )

        distances = results.get(
            "distances",
            [[]],
        )

        ids = (
            ids[0]
            if ids
            and isinstance(
                ids[0],
                list,
            )
            else []
        )

        documents = (
            documents[0]
            if documents
            and isinstance(
                documents[0],
                list,
            )
            else []
        )

        metadatas = (
            metadatas[0]
            if metadatas
            and isinstance(
                metadatas[0],
                list,
            )
            else []
        )

        distances = (
            distances[0]
            if distances
            and isinstance(
                distances[0],
                list,
            )
            else []
        )

        candidates = []

        for index, document in enumerate(
            documents
        ):

            candidates.append(
                {
                    "id": (
                        ids[index]
                        if index < len(ids)
                        else None
                    ),
                    "document": document,
                    "metadata": (
                        metadatas[index]
                        if index < len(metadatas)
                        and isinstance(
                            metadatas[index],
                            dict,
                        )
                        else {}
                    ),
                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                }
            )

        return candidates

    # ------------------------------------------------------------------
    # Rank security candidates
    # ------------------------------------------------------------------

    def _rank_security_candidates(
        self,
        query,
        candidates,
        top_k,
    ):
        """
        Rank candidates using security-aware scoring,
        remove duplicate documents, and encourage
        simple event diversity.
        """

        if not candidates:

            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        # ----------------------------------------------------------
        # Calculate scores
        # ----------------------------------------------------------

        for candidate in candidates:

            candidate["_security_score"] = (
                self._security_score(
                    query=query,
                    document=candidate["document"],
                    metadata=candidate["metadata"],
                    distance=candidate["distance"],
                )
            )

        # ----------------------------------------------------------
        # Highest score first
        # ----------------------------------------------------------

        candidates.sort(
            key=lambda item: (
                -item["_security_score"],
                (
                    item["distance"]
                    if item["distance"] is not None
                    else float("inf")
                ),
            )
        )

        # ----------------------------------------------------------
        # Remove duplicate documents
        # ----------------------------------------------------------

        selected = []

        seen_documents = set()

        event_counts = {}

        for candidate in candidates:

            document = str(
                candidate["document"]
            ).strip()

            if not document:

                continue

            normalised = " ".join(
                document.lower().split()
            )

            if normalised in seen_documents:

                continue

            event_type = str(
                candidate["metadata"].get(
                    "event_type",
                    "UNKNOWN",
                )
            ).upper()

            if event_counts.get(
                event_type,
                0,
            ) >= 2:

                continue

            seen_documents.add(
                normalised
            )

            event_counts[event_type] = (
                event_counts.get(
                    event_type,
                    0,
                ) + 1
            )

            selected.append(
                candidate
            )

            if len(selected) >= top_k:

                break

        # ----------------------------------------------------------
        # Return Chroma-compatible structure
        # ----------------------------------------------------------

        return {
            "ids": [[
                candidate["id"]
                for candidate in selected
            ]],

            "documents": [[
                candidate["document"]
                for candidate in selected
            ]],

            "metadatas": [[
                candidate["metadata"]
                for candidate in selected
            ]],

            "distances": [[
                candidate["distance"]
                for candidate in selected
            ]],
        }

    # ------------------------------------------------------------------
    # Security scoring
    # ------------------------------------------------------------------

    def _security_score(
        self,
        query,
        document,
        metadata,
        distance,
    ):
        """
        Calculate a simple security-aware ranking score.

        Semantic similarity provides the base score.
        Query intent and structured security metadata
        provide additional ranking signals.
        """

        query_lower = str(
            query
        ).lower()

        document_lower = str(
            document
        ).lower()

        metadata_text = " ".join(
            str(value).lower()
            for value in metadata.values()
            if value is not None
        )

        combined_text = (
            document_lower
            + " "
            + metadata_text
        )

        # ----------------------------------------------------------
        # Base semantic score
        # ----------------------------------------------------------

        if distance is None:

            score = 0.0

        else:

            score = 1.0 / (
                1.0 + float(distance)
            )

        intent = self._detect_security_intent(
            query_lower
        )

        event_type = str(
            metadata.get(
                "event_type",
                "",
            )
        ).upper()

        severity = str(
            metadata.get(
                "severity",
                "",
            )
        ).upper()

        process = str(
            metadata.get(
                "process",
                "",
            )
        ).lower()

        # ----------------------------------------------------------
        # Severity
        # ----------------------------------------------------------

        severity_bonus = {
            "HIGH": 2.5,
            "MEDIUM": 1.5,
            "LOW": 0.5,
            "INFO": 0.0,
        }

        score += severity_bonus.get(
            severity,
            0.0,
        )

        # ----------------------------------------------------------
        # Authentication
        # ----------------------------------------------------------

        if intent == "authentication":

            authentication_events = {
                "AUTH_FAILURE",
                "AUTH_FAILED",
                "LOGIN_FAILURE",
                "FAILED_LOGIN",
            }

            useful_events = {
                "SESSION_OPEN",
                "SESSION_CLOSE",
            }

            authentication_terms = [
                "failed password",
                "authentication failure",
                "failed authentication",
                "failed login",
                "invalid user",
            ]

            if event_type in authentication_events:

                score += 6.0

            elif event_type in useful_events:

                score += 1.0

            if process == "sshd":

                score += 2.5

            for term in authentication_terms:

                if term in combined_text:

                    score += 3.0

        # ----------------------------------------------------------
        # Privilege escalation
        # ----------------------------------------------------------

        elif intent == "privilege":

            if event_type == "SUDO_COMMAND":

                score += 6.0

            if process in {
                "sudo",
                "su",
                "pkexec",
            }:

                score += 4.0

            privilege_terms = [
                "sudo",
                "user=root",
                "root",
                "elevated privilege",
                "elevated privileges",
                "privilege escalation",
                "usermod",
                "passwd",
                "pkexec",
            ]

            matches = sum(
                1
                for term in privilege_terms
                if term in combined_text
            )

            score += min(
                matches * 2.0,
                6.0,
            )

            routine_events = {
                "KERNEL",
                "SYSTEM_EVENT",
                "SYSTEMD",
                "BOOT",
            }

            if (
                event_type in routine_events
                and severity == "INFO"
            ):

                score -= 3.0

        # ----------------------------------------------------------
        # Network scanning
        # ----------------------------------------------------------

        elif intent == "network_scan":

            if event_type in {
                "NETWORK_SCAN",
                "PORT_SCAN",
                "RECONNAISSANCE",
                "SCANNING",
            }:

                score += 6.0

            network_scan_terms = [
                "network scan",
                "network scanning",
                "port scan",
                "port scanning",
                "reconnaissance",
                "scan",
                "scanning",
            ]

            matches = sum(
                1
                for term in network_scan_terms
                if term in combined_text
            )

            score += min(
                matches * 2.0,
                8.0,
            )

        # ----------------------------------------------------------
        # General network activity
        # ----------------------------------------------------------

        elif intent == "network":

            if event_type == "NETWORK":

                score += 5.0

            network_terms = [
                "connection",
                "connections",
                "port",
                "network",
                "interface",
            ]

            matches = sum(
                1
                for term in network_terms
                if term in combined_text
            )

            score += min(
                matches * 1.5,
                6.0,
            )

        # ----------------------------------------------------------
        # Malware / executable activity
        # ----------------------------------------------------------

        elif intent == "malware":

            malware_terms = [
                "malware",
                "malicious",
                "suspicious executable",
                "executable",
                "payload",
                "process execution",
            ]

            matches = sum(
                1
                for term in malware_terms
                if term in combined_text
            )

            score += min(
                matches * 2.5,
                8.0,
            )

            if event_type == "AUDIT":

                score += 2.0

        # ----------------------------------------------------------
        # Generic security query
        # ----------------------------------------------------------

        else:

            security_events = {
                "SUDO_COMMAND": 4.0,
                "AUDIT": 3.5,
                "KERNEL_ERROR": 3.5,
                "BOOT_ERROR": 3.5,
                "NETWORK": 3.0,
            }

            score += security_events.get(
                event_type,
                0.0,
            )

            routine_events = {
                "SYSTEM_EVENT",
                "SYSTEMD",
                "BOOT",
                "DBUS",
                "CPU",
                "MEMORY",
                "STORAGE",
                "PACKAGE",
            }

            if (
                event_type in routine_events
                and severity == "INFO"
            ):

                score -= 2.0

            generic_terms = [
                "suspicious",
                "attack",
                "threat",
                "malicious",
                "intrusion",
                "anomaly",
            ]

            matches = sum(
                1
                for term in generic_terms
                if term in combined_text
            )

            score += min(
                matches * 1.0,
                4.0,
            )

        # ----------------------------------------------------------
        # Unknown INFO records
        # ----------------------------------------------------------

        if (
            event_type == "UNKNOWN"
            and severity == "INFO"
            and intent != "generic"
        ):

            score -= 1.0

        return score

    # ------------------------------------------------------------------
    # Security intent detection
    # ------------------------------------------------------------------

    def _detect_security_intent(
        self,
        query,
    ):
        """
        Determine the main security intent.

        Returns:

            authentication
            privilege
            network_scan
            network
            malware
            generic
        """

        query_lower = str(
            query
        ).lower()

        # ----------------------------------------------------------
        # Network scanning has priority over general network intent
        # ----------------------------------------------------------

        network_scan_terms = [
            "network scan",
            "network scanning",
            "port scan",
            "port scanning",
            "reconnaissance",
        ]

        if any(
            term in query_lower
            for term in network_scan_terms
        ):

            return "network_scan"

        # ----------------------------------------------------------
        # Other intents
        # ----------------------------------------------------------

        intent_terms = {

            "authentication": [
                "ssh",
                "sshd",
                "authentication",
                "auth",
                "login",
                "password",
                "credential",
                "brute force",
                "brute-force",
                "failed login",
                "failed password",
            ],

            "privilege": [
                "sudo",
                "privilege escalation",
                "privilege",
                "privileges",
                "elevated privilege",
                "elevated privileges",
                "root",
                "pkexec",
                " su ",
            ],

            "network": [
                "suspicious connection",
                "network connection",
                "network activity",
                "connections",
                "network",
            ],

            "malware": [
                "malware",
                "malicious",
                "executable",
                "payload",
                "process execution",
                "suspicious executable",
            ],
        }

        matches = {
            intent: sum(
                1
                for term in terms
                if term in query_lower
            )
            for intent, terms in intent_terms.items()
        }

        best_intent = max(
            matches,
            key=matches.get,
        )

        if matches[best_intent] == 0:

            return "generic"

        return best_intent

    # ------------------------------------------------------------------
    # Distance threshold
    # ------------------------------------------------------------------

    def _apply_distance_threshold(
        self,
        results,
    ):
        """
        Remove retrieved results whose distance exceeds
        the configured distance threshold.
        """

        if not results:

            return results

        distances = results.get(
            "distances",
            [],
        )

        if not distances:

            return results

        if not isinstance(
            distances,
            list,
        ):

            return results

        if len(distances) == 0:

            return results

        query_distances = distances[0]

        if not isinstance(
            query_distances,
            list,
        ):

            return results

        keep_indices = [
            index
            for index, distance in enumerate(
                query_distances
            )
            if distance <= self.distance_threshold
        ]

        filtered_results = dict(
            results
        )

        fields_to_filter = [
            "ids",
            "documents",
            "metadatas",
            "distances",
            "embeddings",
            "uris",
            "data",
        ]

        for field in fields_to_filter:

            values = results.get(
                field
            )

            if values is None:

                continue

            if not isinstance(
                values,
                list,
            ):

                continue

            if len(values) == 0:

                continue

            if isinstance(
                values[0],
                list,
            ):

                filtered_results[field] = [
                    [
                        values[0][index]
                        for index in keep_indices
                    ]
                ]

        return filtered_results

    # ------------------------------------------------------------------
    # Document retrieval
    # ------------------------------------------------------------------

    def retrieve_documents(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Retrieve only document text.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

        documents = results.get(
            "documents",
            [],
        )

        if not documents:

            return []

        if not isinstance(
            documents,
            list,
        ):

            return []

        if not isinstance(
            documents[0],
            list,
        ):

            return []

        return documents[0]

    # ------------------------------------------------------------------
    # Metadata retrieval
    # ------------------------------------------------------------------

    def retrieve_metadata(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Retrieve metadata associated with results.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

        metadata = results.get(
            "metadatas",
            [],
        )

        if not metadata:

            return []

        if not isinstance(
            metadata,
            list,
        ):

            return []

        if not isinstance(
            metadata[0],
            list,
        ):

            return []

        return metadata[0]

    # ------------------------------------------------------------------
    # Retrieval with scores
    # ------------------------------------------------------------------

    def retrieve_with_scores(
        self,
        query,
        top_k=None,
        source=None,
    ):
        """
        Return retrieved documents together with their
        ChromaDB distances.
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            source=source,
        )

        documents = results.get(
            "documents",
            [],
        )

        distances = results.get(
            "distances",
            [],
        )

        if not documents:

            return []

        if not isinstance(
            documents,
            list,
        ):

            return []

        if not isinstance(
            documents[0],
            list,
        ):

            return []

        documents = documents[0]

        if (
            isinstance(
                distances,
                list,
            )
            and len(distances) > 0
            and isinstance(
                distances[0],
                list,
            )
        ):

            distances = distances[0]

        else:

            distances = []

        output = []

        for index, document in enumerate(
            documents
        ):

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            output.append(
                {
                    "document": document,
                    "distance": distance,
                }
            )

        return output

    # ------------------------------------------------------------------
    # Database count
    # ------------------------------------------------------------------

    def count(self):
        """
        Return the number of records currently stored
        in the vector database.
        """

        return self.database.count()

    # ------------------------------------------------------------------
    # Retriever information
    # ------------------------------------------------------------------

    def info(self):
        """
        Return information about the Retriever.
        """

        return {
            "component": "Retriever",
            "top_k": self.top_k,
            "distance_threshold": (
                self.distance_threshold
            ),
            "database": self.database.info(),
            "embedding_model": (
                self.embedding_manager.model_information()
            ),
        }

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self):
        """
        Close the underlying database.
        """

        self.database.close()

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self):

        return (
            f"Retriever("
            f"top_k={self.top_k}, "
            f"distance_threshold="
            f"{self.distance_threshold}, "
            f"records={self.count()})"
        )