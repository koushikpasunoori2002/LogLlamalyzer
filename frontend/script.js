const API_URL = "http://127.0.0.1:8001";

const queryInput = document.getElementById("query");
const analyzeButton = document.getElementById("analyze-button");
const resultBox = document.getElementById("result");
const statusBox = document.getElementById("status");


async function analyzeSecurity() {

    const query = queryInput.value.trim();

    if (!query) {

        statusBox.textContent =
            "Please enter a security query.";

        resultBox.textContent =
            "No query provided.";

        return;
    }

    analyzeButton.disabled = true;

    statusBox.textContent =
        "Analysing security query...";

    resultBox.textContent =
        "Please wait while the RAG + LLM pipeline processes your request.";

    try {

        const response = await fetch(
            `${API_URL}/analyze`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    query: query
                })
            }
        );


        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        const data = await response.json();


        resultBox.textContent =
            data.answer;

        statusBox.textContent =
            "Analysis completed successfully.";

    } catch (error) {

        console.error(error);

        statusBox.textContent =
            "Analysis failed.";

        resultBox.textContent =
            "Unable to connect to the LogLlamalyzer API. " +
            "Make sure the FastAPI server is running.";

    } finally {

        analyzeButton.disabled = false;
    }
}


analyzeButton.addEventListener(
    "click",
    analyzeSecurity
);