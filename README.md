# LogLlamalyzer

LogLlamalyzer is an AI-powered security log analysis system that combines security log retrieval, security knowledge retrieval, Retrieval-Augmented Generation (RAG), and a local language model to analyse security-related queries.

The system provides a FastAPI backend and a lightweight web frontend for submitting security queries and displaying generated security analysis.

---

## Project Objectives

The main objectives of LogLlamalyzer are to:

- Process and analyse security log data.
- Retrieve relevant log information for a security query.
- Retrieve relevant security knowledge.
- Combine retrieved information into a RAG context.
- Generate a security analysis using an LLM.
- Provide the analysis through a REST API.
- Provide a web interface for interacting with the system.
- Test the system at component, API, frontend, and integration levels.

---

## System Architecture

The system follows the pipeline:

```text
User Query
    |
    v
Frontend
    |
    v
FastAPI API
    |
    v
RAG Context Builder
    |
    +----------------------+
    |                      |
    v                      v
Log Retriever       Knowledge Retriever
    |                      |
    v                      v
ChromaDB            Security Knowledge
    |                      |
    +----------+-----------+
               |
               v
          RAG Context
               |
               v
          RAG Analyzer
               |
               v
        LLM Generation
               |
               v
       Security Analysis
               |
               v
              API
               |
               v
           Frontend