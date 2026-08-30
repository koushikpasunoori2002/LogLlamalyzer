const API_URL = "http://127.0.0.1:8001";

const queryInput =
    document.getElementById("query");

const sourceInput =
    document.getElementById("source");

const analyzeButton =
    document.getElementById("analyze-button");

const resultBox =
    document.getElementById("result");

const statusBox =
    document.getElementById("status");

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


// ----------------------------------------------------------
// Reset metadata
// ----------------------------------------------------------

function resetMetadata() {

    sourceMetadata.textContent =
        "All sources";

    logsMetadata.textContent =
        "0";

    knowledgeMetadata.textContent =
        "0";
}


// ----------------------------------------------------------
// Display API metadata
// ----------------------------------------------------------

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
    // Log evidence
    // ------------------------------------------------------

    logsMetadata.textContent =
        String(
            metadata.log_results || 0
        );

    // ------------------------------------------------------
    // Knowledge evidence
    // ------------------------------------------------------

    knowledgeMetadata.textContent =
        String(
            metadata.knowledge_results || 0
        );
}


// ----------------------------------------------------------
// Analyse security query
// ----------------------------------------------------------

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

        return;
    }

    analyzeButton.disabled = true;

    statusBox.textContent =
        "Analysing security query...";

    resultBox.textContent =
        "Please wait while the RAG + LLM pipeline processes your request.";

    resetMetadata();

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
            (
                "Unable to connect to the "
                + "LogLlamalyzer API. "
                + "Make sure the FastAPI server "
                + "is running."
            );

        resetMetadata();

    } finally {

        analyzeButton.disabled =
            false;
    }
}


// ----------------------------------------------------------
// Button event
// ----------------------------------------------------------

analyzeButton.addEventListener(
    "click",
    analyzeSecurity
);