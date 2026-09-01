const API_URL =
    "http://127.0.0.1:8001";


const queryInput =
    document.getElementById(
        "query"
    );


const sourceInput =
    document.getElementById(
        "source"
    );


const analyzeButton =
    document.getElementById(
        "analyze-button"
    );


const resultBox =
    document.getElementById(
        "result"
    );


const statusBox =
    document.getElementById(
        "status"
    );


const sourceMetadata =
    document.getElementById(
        "metadata-source"
    );


const logsMetadata =
    document.getElementById(
        "metadata-logs"
    );


const knowledgeMetadata =
    document.getElementById(
        "metadata-knowledge"
    );


const evidenceBox =
    document.getElementById(
        "evidence"
    );


// ==========================================================
// Dashboard elements
// ==========================================================

const dashboardTotal =
    document.getElementById(
        "dashboard-total"
    );


const dashboardHigh =
    document.getElementById(
        "dashboard-high"
    );


const dashboardAuthFailure =
    document.getElementById(
        "dashboard-auth-failure"
    );


const dashboardSudo =
    document.getElementById(
        "dashboard-sudo"
    );


const dashboardSources =
    document.getElementById(
        "dashboard-sources"
    );


const dashboardEvents =
    document.getElementById(
        "dashboard-events"
    );


// ==========================================================
// Reset metadata
// ==========================================================

function resetMetadata() {

    sourceMetadata.textContent =
        "All sources";

    logsMetadata.textContent =
        "0";

    knowledgeMetadata.textContent =
        "0";
}


// ==========================================================
// Reset evidence
// ==========================================================

function resetEvidence() {

    evidenceBox.innerHTML = "";
}


// ==========================================================
// Reset dashboard
// ==========================================================

function resetDashboard() {

    dashboardTotal.textContent =
        "0";

    dashboardHigh.textContent =
        "0";

    dashboardAuthFailure.textContent =
        "0";

    dashboardSudo.textContent =
        "0";

    dashboardSources.innerHTML =
        `
        <p class="dashboard-empty">
            No evidence available.
        </p>
        `;

    dashboardEvents.innerHTML =
        `
        <p class="dashboard-empty">
            No evidence available.
        </p>
        `;
}


// ==========================================================
// Display API metadata
// ==========================================================

function displayMetadata(data) {

    const source =
        data.source ||
        null;


    const metadata =
        data.metadata ||
        {};


    // ------------------------------------------------------
    // Source
    // ------------------------------------------------------

    if (source) {

        sourceMetadata.textContent =
            source;

    } else {

        const sources =
            metadata.sources ||
            [];

        if (sources.length > 0) {

            sourceMetadata.textContent =
                sources.join(", ");

        } else {

            sourceMetadata.textContent =
                "All sources";
        }
    }


    // ------------------------------------------------------
    // Log evidence count
    // ------------------------------------------------------

    logsMetadata.textContent =
        String(
            metadata.log_results || 0
        );


    // ------------------------------------------------------
    // Knowledge evidence count
    // ------------------------------------------------------

    knowledgeMetadata.textContent =
        String(
            metadata.knowledge_results || 0
        );
}


// ==========================================================
// Dashboard helpers
// ==========================================================

function createDashboardRow(
    label,
    count,
    total
) {

    const row =
        document.createElement(
            "div"
        );

    row.className =
        "dashboard-row";


    const header =
        document.createElement(
            "div"
        );

    header.className =
        "dashboard-row-header";


    const labelElement =
        document.createElement(
            "span"
        );

    labelElement.className =
        "dashboard-row-label";

    labelElement.textContent =
        label;


    const countElement =
        document.createElement(
            "span"
        );

    countElement.className =
        "dashboard-row-count";

    countElement.textContent =
        String(count);


    header.appendChild(
        labelElement
    );

    header.appendChild(
        countElement
    );


    const track =
        document.createElement(
            "div"
        );

    track.className =
        "dashboard-bar-track";


    const bar =
        document.createElement(
            "div"
        );

    bar.className =
        "dashboard-bar";


    const percentage =
        total > 0
            ? Math.round(
                (count / total) * 100
            )
            : 0;


    bar.style.width =
        `${percentage}%`;


    track.appendChild(
        bar
    );


    row.appendChild(
        header
    );

    row.appendChild(
        track
    );


    return row;
}


// ==========================================================
// Display quantitative dashboard
// ==========================================================

function displayDashboard(data) {

    resetDashboard();


    const evidence =
        Array.isArray(
            data.evidence
        )
            ? data.evidence
            : [];


    // ------------------------------------------------------
    // Basic totals
    // ------------------------------------------------------

    const total =
        evidence.length;


    const highSeverityCount =
        evidence.filter(
            item =>
                String(
                    item.severity || ""
                ).toUpperCase() === "HIGH"
        ).length;


    const authFailureCount =
        evidence.filter(
            item =>
                String(
                    item.event_type || ""
                ).toUpperCase() === "AUTH_FAILURE"
        ).length;


    const sudoCommandCount =
        evidence.filter(
            item =>
                String(
                    item.event_type || ""
                ).toUpperCase() === "SUDO_COMMAND"
        ).length;


    dashboardTotal.textContent =
        String(total);


    dashboardHigh.textContent =
        String(highSeverityCount);


    dashboardAuthFailure.textContent =
        String(authFailureCount);


    dashboardSudo.textContent =
        String(sudoCommandCount);


    // ------------------------------------------------------
    // No evidence
    // ------------------------------------------------------

    if (!evidence.length) {

        return;
    }


    // ------------------------------------------------------
    // Count sources
    // ------------------------------------------------------

    const sourceCounts =
        {};


    evidence.forEach(
        item => {

            const source =
                item.source ||
                "Unknown source";


            sourceCounts[source] =
                (
                    sourceCounts[source] ||
                    0
                ) + 1;
        }
    );


    const sortedSources =
        Object.entries(
            sourceCounts
        ).sort(
            (a, b) =>
                b[1] - a[1]
        );


    sortedSources.forEach(
        ([source, count]) => {

            dashboardSources.appendChild(
                createDashboardRow(
                    source,
                    count,
                    total
                )
            );
        }
    );


    // ------------------------------------------------------
    // Count event types
    // ------------------------------------------------------

    const eventCounts =
        {};


    evidence.forEach(
        item => {

            const eventType =
                item.event_type ||
                "UNKNOWN";


            eventCounts[eventType] =
                (
                    eventCounts[eventType] ||
                    0
                ) + 1;
        }
    );


    const sortedEvents =
        Object.entries(
            eventCounts
        ).sort(
            (a, b) =>
                b[1] - a[1]
        );


    sortedEvents.forEach(
        ([eventType, count]) => {

            dashboardEvents.appendChild(
                createDashboardRow(
                    eventType,
                    count,
                    total
                )
            );
        }
    );
}


// ==========================================================
// Display retrieved log evidence
// ==========================================================

function displayEvidence(data) {

    resetEvidence();


    const evidence =
        data.evidence || [];


    if (!evidence.length) {

        return;
    }


    const heading =
        document.createElement(
            "h3"
        );

    heading.textContent =
        "Log Evidence";


    evidenceBox.appendChild(
        heading
    );


    evidence.forEach(
        (item, index) => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "evidence-card";


            // --------------------------------------------------
            // Header
            // --------------------------------------------------

            const header =
                document.createElement(
                    "div"
                );

            header.className =
                "evidence-header";


            const title =
                document.createElement(
                    "strong"
                );

            title.textContent =
                `Evidence ${index + 1}`;


            header.appendChild(
                title
            );


            const source =
                document.createElement(
                    "span"
                );

            source.className =
                "evidence-source";


            source.textContent =
                item.source ||
                "Unknown source";


            header.appendChild(
                source
            );


            card.appendChild(
                header
            );


            // --------------------------------------------------
            // Main metadata
            // --------------------------------------------------

            const metadata =
                document.createElement(
                    "div"
                );

            metadata.className =
                "evidence-metadata";


            const fields = [
                [
                    "Timestamp",
                    item.timestamp
                ],
                [
                    "Hostname",
                    item.hostname
                ],
                [
                    "Process",
                    item.process
                ],
                [
                    "Severity",
                    item.severity
                ],
                [
                    "Event",
                    item.event
                ],
                [
                    "Event Type",
                    item.event_type
                ],
                [
                    "User",
                    item.user
                ],
                [
                    "IP Address",
                    item.ip
                ],
                [
                    "Port",
                    item.port
                ],
                [
                    "Protocol",
                    item.protocol
                ],
                [
                    "Source File",
                    item.source_file
                ]
            ];


            fields.forEach(
                ([label, value]) => {

                    if (
                        value === null ||
                        value === undefined ||
                        value === ""
                    ) {

                        return;
                    }


                    const row =
                        document.createElement(
                            "div"
                        );

                    row.className =
                        "evidence-row";


                    const labelElement =
                        document.createElement(
                            "span"
                        );

                    labelElement.className =
                        "evidence-label";

                    labelElement.textContent =
                        `${label}:`;


                    const valueElement =
                        document.createElement(
                            "span"
                        );

                    valueElement.className =
                        "evidence-value";

                    valueElement.textContent =
                        String(value);


                    row.appendChild(
                        labelElement
                    );

                    row.appendChild(
                        valueElement
                    );


                    metadata.appendChild(
                        row
                    );
                }
            );


            card.appendChild(
                metadata
            );


            // --------------------------------------------------
            // Original log message
            // --------------------------------------------------

            if (item.message) {

                const messageLabel =
                    document.createElement(
                        "div"
                    );

                messageLabel.className =
                    "evidence-message-label";

                messageLabel.textContent =
                    "Log Message";


                card.appendChild(
                    messageLabel
                );


                const message =
                    document.createElement(
                        "pre"
                    );

                message.className =
                    "evidence-message";

                message.textContent =
                    item.message;


                card.appendChild(
                    message
                );
            }


            evidenceBox.appendChild(
                card
            );
        }
    );
}


// ==========================================================
// Analyse security query
// ==========================================================

async function analyzeSecurity() {

    const query =
        queryInput.value.trim();


    const source =
        sourceInput.value.trim();


    if (!query) {

        statusBox.textContent =
            "Please enter a security query.";


        resultBox.textContent =
            "No query provided.";


        resetMetadata();

        resetEvidence();

        resetDashboard();

        return;
    }


    analyzeButton.disabled =
        true;


    statusBox.textContent =
        "Analysing security query...";


    resultBox.textContent =
        "Please wait while the RAG + LLM pipeline processes your request.";


    resetMetadata();

    resetEvidence();

    resetDashboard();


    // ------------------------------------------------------
    // Build request
    // ------------------------------------------------------

    const requestBody = {
        query: query
    };


    if (source) {

        requestBody.source =
            source;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/analyze`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(
                        requestBody
                    )
                }
            );


        // --------------------------------------------------
        // HTTP error
        // --------------------------------------------------

        if (!response.ok) {

            let message =
                `API request failed: ${response.status}`;


            try {

                const errorData =
                    await response.json();


                if (
                    errorData.detail
                ) {

                    message =
                        errorData.detail;
                }

            } catch (error) {

                console.error(
                    "Unable to parse error response:",
                    error
                );
            }


            throw new Error(
                message
            );
        }


        // --------------------------------------------------
        // Parse response
        // --------------------------------------------------

        const data =
            await response.json();


        // --------------------------------------------------
        // Display analysis
        // --------------------------------------------------

        resultBox.textContent =
            data.answer || "";


        // --------------------------------------------------
        // Display metadata
        // --------------------------------------------------

        displayMetadata(
            data
        );


        // --------------------------------------------------
        // Display quantitative dashboard
        // --------------------------------------------------

        displayDashboard(
            data
        );


        // --------------------------------------------------
        // Display evidence
        // --------------------------------------------------

        displayEvidence(
            data
        );


        statusBox.textContent =
            "Analysis completed successfully.";

    } catch (error) {

        console.error(
            error
        );


        statusBox.textContent =
            "Analysis failed.";


        resultBox.textContent =
            error.message ||
            "Unable to connect to the LogLlamalyzer API. "
            + "Make sure the FastAPI server is running.";


        resetMetadata();

        resetEvidence();

        resetDashboard();

    } finally {

        analyzeButton.disabled =
            false;
    }
}


// ==========================================================
// Button event
// ==========================================================

analyzeButton.addEventListener(
    "click",
    analyzeSecurity
);