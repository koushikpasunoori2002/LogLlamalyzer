# LogLlamalyzer

LogLlamalyzer is an AI-powered cybersecurity log analysis system that processes security logs from multiple sources, retrieves relevant evidence using semantic search, and generates security-focused analysis using Retrieval-Augmented Generation (RAG) and a locally hosted Large Language Model (LLM).

The system combines multi-server log synchronization, structured log preprocessing, vector retrieval with ChromaDB, security knowledge retrieval, source-aware analysis, incremental processing, a FastAPI backend, and a web-based frontend.

---

## Table of Contents

1. [Features](#1-features)
2. [Prerequisites & Dependencies](#2-prerequisites--dependencies)
3. [Installation & Setup](#3-installation--setup)
4. [Usage Guide](#4-usage-guide)
5. [System Architecture](#5-system-architecture)
6. [API Documentation](#6-api-documentation)
7. [Testing & Evaluation](#7-testing--evaluation)
8. [Academic Integrity & Credits](#8-academic-integrity--credits)

---

# 1. Features

- **Multi-server log synchronization**
  Supports multiple configured log sources and synchronizes their logs using rsync over SSH.

- **Automated log preprocessing**
  Detects, reads, parses, and normalises security logs into structured `LogRecord` objects.

- **Semantic vector retrieval**
  Converts log chunks and queries into embeddings and uses ChromaDB for semantic similarity search.

- **Retrieval-Augmented Generation (RAG)**
  Combines retrieved log evidence with relevant security knowledge before LLM analysis.

- **Source-aware retrieval**
  Supports optional source selection and source-filtered retrieval for configured sources such as `server-a`, `server-b`, and `server-c`.

- **Structured security analysis**
  Parses LLM output into threat assessment, evidence, interpretation, severity, recommended actions, limitations, and metadata.

- **Incremental processing**
  Detects previously indexed records and avoids generating duplicate embeddings and vectors.

- **Local LLM inference**
  Uses Ollama with the `llama3.1:8b` model for local security analysis.

- **FastAPI backend**
  Exposes security analysis and health/status functionality through HTTP endpoints.

- **Web frontend**
  Provides a browser-based interface for entering security queries, selecting sources, and viewing analysis results and metadata.

- **Automated evaluation**
  Includes retrieval, performance, reliability, incremental-processing, multi-source, regression, integration, and end-to-end validation.

---

# 2. Prerequisites & Dependencies

## 2.1 Software Requirements

- Python 3.13
- Ollama
- Git
- Rsync with SSH access for multi-server synchronization
- A modern web browser

## 2.2 Python Dependencies

The project dependencies are listed in `requirements.txt`:

```text
fastapi
uvicorn
pydantic
chromadb
sentence-transformers
numpy
requests
```

## 2.3 Local LLM

The project uses Ollama for local LLM inference.
```text
Model: llama3.1:8b
Base URL: http://localhost:11434
Generation limit: 256 tokens
Keep-alive: 10m
```
The required model must be available in the local Ollama installation.

You can verify the locally available models with:

```powershell
ollama list
```

---

# 3. Installation & Setup

## 3.1 Clone the Repository

```powershell
git clone https://github.com/koushikpasunoori2002/LogLlamalyzer.git
cd LogLlamalyzer
```

## 3.2 Create a Python Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3.3 Install Dependencies

```powershell
pip install -r requirements.txt
```

## 3.4 Prepare Ollama

Make sure Ollama is running and the llama3.1:8b model is available locally.

Verify the installation with:
```powershell
ollama list
```
The project expects Ollama at:
```text
http://localhost:11434
```

## 3.5 Dataset

The repository contains raw and processed log data under:
```text
dataset/
├── raw/
└── processed/
```

The raw dataset contains examples from several log categories, including:
```text
auth
syslog
kern
dmesg
dpkg
apport
```
Processed outputs are available in:
```text
dataset/processed/
├── logs.csv
├── logs.db
└── logs.json
```

## 3.6 Start the FastAPI Backend

From the project root:
```powershell
uvicorn backend.api.app:app --host 127.0.0.1 --port 8001
```

The backend will then be available at:
```text
http://127.0.0.1:8001
```

## 3.7 Multi-Server Synchronization

The synchronization subsystem is configured programmatically using 'SynchronizationConfig' and 'LogSource' objects.

Each configured source contains:
```text
source_id
hostname
log_paths
```
The synchronization layer uses rsync over SSH and supports multiple configured sources independently.

The default synchronization destination is:
```text
data/synchronized
```
The default synchronization interval is:
```text
60 seconds
```
A complete synchronization and RAG ingestion cycle is coordinated by 'SynchronizedRAGApplication.run_once()'.

---

# 4. Usage Guide

## 4.1 Start the Required Services

Start the following:
```text
Ollama
FastAPI backend
```
Then open the frontend located at:
```text
frontend/index.html
```

## 4.2 Enter a Security Query

Example:
```text
failed SSH authentication brute force attack
```

A source can optionally be selected:
```text
server-a
```

The available sources used by the validated multi-source workflow include:
```text
server-a
server-b
server-c
```

## 4.3 Submit the Query

The frontend sends the analysis request to:
```text
POST /analyze
```

Example request:

```json
{
  "query": "failed SSH authentication brute force attack",
  "source": "server-a"
}
```
The 'source' field is optional.

A query-only request is also supported:

```json
{
  "query": "failed SSH authentication brute force attack"
}
```

## 4.4 Request Processing

After submission, the request follows the analysis pipeline:
```text
User Query
    ↓
Frontend
    ↓
JavaScript
    ↓
FastAPI /analyze
    ↓
Query Validation
    ↓
Query Embedding
    ↓
Log Retrieval
    ↓
Security Knowledge Retrieval
    ↓
RAG Context Construction
    ↓
LLM Analysis
    ↓
Structured Analysis
    ↓
API Response
    ↓
Frontend Display
```

## 4.5 Example Queries

The evaluation suite includes queries such as:
```text
failed SSH authentication brute force attack
repeated failed login credential attack
sudo privilege escalation elevated privileges
suspicious executable malware execution
network scanning suspicious connections
```

## 4.6 Result

The frontend displays the generated security analysis together with source and evidence metadata.

Example response structure:
```json
{
  "query": "failed SSH authentication brute force attack",
  "answer": "Security analysis...",
  "source": "server-a",
  "metadata": {
    "sources": ["server-a"],
    "log_results": 2,
    "knowledge_results": 0
  }
}
```

---

# 5. System Architecture

LogLlamalyzer uses a modular architecture consisting of two connected processing flows:
1. Log ingestion and indexing
2. Query analysis

## 5.1 Log Ingestion and Indexing

```text
Multiple Log Sources
        ↓
Multi-Server Synchronization
        ↓
Synchronized Log Files
        ↓
Synchronized Log Processor
        ↓
Preprocessing Pipeline
        ↓
Detection / Reading / Parsing
        ↓
Normalisation
        ↓
LogRecord
        ↓
Synchronized Log Ingestor
        ↓
ChunkManager
        ↓
Log Chunks
        ↓
EmbeddingManager
        ↓
Vector Embeddings
        ↓
ChromaDB
        ↓
Searchable Log Database
```

## 5.2 Query Analysis

```text
User
 ↓
Frontend
 ↓
JavaScript
 ↓
FastAPI /analyze
 ↓
Query Validation
 ↓
Query Embedding
 ↓
Source-Aware Log Retrieval
 ↓
+-----------------------+
| Log Evidence          |
| + Security Knowledge |
+-----------------------+
 ↓
ContextBuilder
 ↓
RAGContext
 ↓
RAGAnalyzer
 ↓
PromptBuilder
 ↓
Ollama
 ↓
LLM Response
 ↓
Analysis Parser
 ↓
Structured SecurityAnalysis
 ↓
API Response
 ↓
Frontend
```

## 5.3 Major Backend Components

| Component       | Responsibility                                                               |
| --------------- | ---------------------------------------------------------------------------- |
| API             | Provides HTTP endpoints and request/response schemas                         |
| Database        | Stores vectors, documents, IDs, and metadata using ChromaDB                  |
| Knowledge       | Ingests and retrieves security knowledge                                     |
| LLM             | Handles embeddings, prompt construction, generation, and structured analysis |
| Preprocessing   | Detects, reads, parses, and normalises raw logs                              |
| RAG             | Handles chunking, retrieval, source filtering, and context construction      |
| Synchronization | Synchronizes logs from multiple configured sources                           |


## 5.4 Source-Aware Processing

Source information is preserved through the processing pipeline:
```text
Source
  ↓
Synchronized File
  ↓
LogRecord
  ↓
Chunk Metadata
  ↓
ChromaDB
  ↓
Retriever
  ↓
Source Filter
  ↓
RAG Context
  ↓
API Response
  ↓
Frontend
```
This allows source-specific analysis while maintaining support for query-only requests.

## 5.5 Incremental Processing

Previously indexed records can be skipped during repeated ingestion.
```text
New Record
    ↓
Chunk Identification
    ↓
Already Indexed?
   /       \
 Yes       No
  ↓         ↓
Skip      Embed
            ↓
          Index
```
This avoids unnecessary duplicate embedding generation and vector insertion.

---

# 6. API Documentation

## 6.1 Endpoints

| Method | Endpoint   | Description                            |
| ------ | ---------- | -------------------------------------- |
| `GET`  | `/`        | Returns basic application information  |
| `GET`  | `/health`  | Returns API health status              |
| `GET`  | `/status`  | Returns application operational status |
| `POST` | `/analyze` | Performs RAG-based security analysis   |

## 6.2 POST /analyze

Request
```json
{
  "query": "failed SSH authentication brute force attack",
  "source": "server-a"
}
```
The source field is optional.

Query-only requests remain supported:
```json
{
  "query": "failed SSH authentication brute force attack"
}
```

## 6.3 Response

```json
{
  "query": "failed SSH authentication brute force attack",
  "answer": "Security analysis...",
  "source": "server-a",
  "metadata": {
    "sources": ["server-a"],
    "log_results": 2,
    "knowledge_results": 0
  }
}
```

## 6.4 Response Fields

| Field      | Description                                        |
| ---------- | -------------------------------------------------- |
| `query`    | Original submitted query                           |
| `answer`   | Generated security analysis                        |
| `source`   | Selected source, or `null` for query-only requests |
| `metadata` | Retrieved sources and evidence counts              |

## 6.5 Input Validation

The API validates:
```text
Empty query   → HTTP 400
Empty source  → HTTP 400
Missing query → HTTP 422
```

---

# 7. Testing & Evaluation

The project contains unit, integration, evaluation, regression, performance, reliability, and end-to-end tests.

## 7.1 Test Categories
```text
Unit Tests
API Tests
Retrieval Evaluation
Security Analysis Evaluation
Performance Evaluation
Reliability Testing
Incremental Processing
Multi-Source Validation
Frontend Integration
Regression Testing
End-to-End Validation
Final Quantitative Evaluation
```
The repository organises these tests under the backend component test directories and the central backend/tests/ directory.

## 7.2 Running the Test Suite

Run the general pytest suite with:
```powershell
pytest
```
Individual evaluation scripts can also be executed directly.

For example:
```powershell
python backend\tests\evaluation\test_final_quantitative_evaluation.py
```

## 7.3 Final System Validation

The final system validation covered:
```text
Database setup
Embedding generation
Chunking
Basic retrieval
Source-aware retrieval
Security classification
Severity preservation
Multi-source access
RAG context construction
Structured security analysis
Retriever API compatibility
Server-A API integration
Server-B API integration
Server-C API integration
Query-only API compatibility
Response schema
Response metadata
API input validation
Health endpoints
```
The final validation passed all checks.

## 7.4 Retrieval Results

The final quantitative evaluation reported:

| Metric                      |  Result |
| --------------------------- | ------: |
| Hit@1                       | 100.00% |
| Hit@3                       | 100.00% |
| MRR                         |  1.0000 |
| Classification Preservation | 100.00% |
| Severity Preservation       | 100.00% |
| Source Filtering Accuracy   | 100.00% |

## 7.5 Reliability Results

The reliability evaluation passed:
```text
12 / 12 checks
```
The reliability tests included input validation, Ollama connection failure handling, timeout handling, request failure handling, empty-response handling, Retriever validation, recovery behaviour, and repeated requests.

## 7.6 Incremental Processing Results

The incremental processing evaluation confirmed that:
```text
Initial records are indexed
Duplicate records are skipped
New records are indexed
Mixed batches are handled correctly
Repeated batches do not create duplicates
Incremental statistics are maintained
```

## 7.7 Multi-Source Validation

The multi-source validation confirmed:
```text
Server-A support
Server-B support
Server-C support
Source isolation
Shared multi-source access
Source leak prevention
API source preservation
Evidence metadata preservation
Frontend/API source integration
```
The final multi-source validation passed all checks.

## 7.8 Regression Testing

Regression testing covered:
```text
Embedding
Retrieval
Ranking
Context construction
LLM analysis
LLM configuration
Failure handling
Repeated retrieval
Source filtering
Incremental processing
API integration
API validation
Health endpoints
Source leak prevention
```
The final full-regression validation passed all checks.

## 7.9 Performance Results

The final quantitative evaluation measured the following average processing times:

| Stage                | Average Time |
| -------------------- | -----------: |
| Query Embedding      |     0.0167 s |
| Retrieval            |     0.0178 s |
| Context Construction |     0.0256 s |
| LLM Analysis         |    44.0326 s |
| Total Processing     |    44.0997 s |

The main measured bottleneck is the local LLM analysis stage.

## 7.10 Analysis Reliability

The final quantitative evaluation reported:

| Metric                 |  Result |
| ---------------------- | ------: |
| Successful Analyses    |     5/5 |
| Analysis Success Rate  | 100.00% |
| Validation Reliability | 100.00% |

## 7.11 Evaluation Output

The final quantitative results are stored in:
```text
outputs/results/final_quantitative_evaluation.json
```

---

# 8. Academic Integrity & Credits

**Author**: Koushik Pasunoori

**Project**: LogLlamalyzer

**Professor**: Dr. Jose Maria Alcaraz Calero

**Declaration**: I declare that this submission is my own work individual project.

The project uses third-party open-source technologies and libraries, including:
{
    Python
    FastAPI
    Uvicorn
    Pydantic
    ChromaDB
    Sentence Transformers
    NumPy
    Requests
    Ollama
    Rsync
}
Third-party libraries, models, documentation, datasets, and development tools should be acknowledged in accordance with the applicable university academic-integrity requirements.
