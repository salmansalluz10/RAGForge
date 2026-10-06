# RAGForge — AI-Powered Document Intelligence & RAG Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-0.3+-336791?style=flat-square)](https://github.com/pgvector/pgvector)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

**RAGForge** is an enterprise-grade document intelligence platform that transforms unstructured business documents (**PDF, DOCX, TXT**) into high-dimensional vector embeddings, enabling **grounded semantic search** and **conversational question-answering with exact source citations**.

Unlike naive chatbots that stuff entire documents into LLM context windows, RAGForge implements a **true Production RAG pipeline**: text extraction with page preservation, recursive semantic chunking, batch vector embeddings, cosine distance similarity search in PostgreSQL via `pgvector`, and strict anti-hallucination prompting.

---

## Table of Contents
- [1. Key Features](#1-key-features)
- [2. Gemini Embeddings](#2-gemini-embeddings)
- [3. System Architecture](#3-system-architecture)
- [4. RAG Pipeline Explained (Interview Guide)](#4-rag-pipeline-explained-interview-guide)
- [5. Technology Stack](#5-technology-stack)
- [6. Project Directory Structure](#6-project-directory-structure)
- [7. Database Architecture](#7-database-architecture)
- [8. Environment Variables](#8-environment-variables)
- [9. Local Development Setup](#9-local-development-setup)
- [10. Docker & Containerized Deployment](#10-docker--containerized-deployment)
- [11. API Documentation](#11-api-documentation)
- [12. Security & Multi-Tenancy](#12-security--multi-tenancy)
- [13. Screenshots Placeholder](#13-screenshots-placeholder)
- [14. Future Roadmap](#14-future-roadmap)

---

## 1. Key Features

- **Authentication & Multi-Tenant Isolation**: Secure bcrypt password hashing, JWT token lifecycle management, and strict database-level isolation ensuring zero cross-tenant data leakage.
- **Multi-Format Document Ingestion**:
  - **PDF**: Page-by-page text extraction via `pypdf`, preserving exact 1-indexed page coordinates.
  - **DOCX**: Body paragraph and table extraction via `python-docx`.
  - **TXT**: Automatic character encoding detection (`UTF-8`, `UTF-8-SIG`, `Latin-1`, `CP1252`).
- **Configurable Recursive Chunking**: Natural boundary text splitting (`\n\n` $\rightarrow$ `\n` $\rightarrow$ sentence terminators $\rightarrow$ words) with configurable chunk size and semantic overlap.
- **pgvector Vector Database**: Native PostgreSQL vector search using the `<=>` cosine distance operator with an in-memory cosine fallback for SQLite testing.
- **Provider-Agnostic AI Engines**:
  - **Embeddings**: Native **Google Gemini** (`gemini-embedding-001`, 768-dim, with `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` task types), OpenAI (`text-embedding-3-small`, 1536-dim), and deterministic offline mock vectors.
  - **LLMs**: Configurable between OpenAI (`gpt-4o-mini`, `gpt-4o`) and offline grounded reasoning engines.
- **Verifiable Source Citations**: Every RAG answer provides structured citations containing document names, page numbers, similarity scores, and context snippets.
- **ChatGPT-Style Document Chat**: Persistent conversation threads, multi-turn dialogue, auto-generated thread titles, and inline citation drawers.
- **Knowledge Collections**: Group related documents into domains (e.g., "Financials", "Legal", "Engineering") for scoped retrieval.
- **Executive Analytics Dashboard**: Live counters for documents, collections, conversations, vector chunks, and real-time processing statuses (`COMPLETED`, `PROCESSING`, `UPLOADED`, `FAILED`).

---

## 2. Gemini Embeddings

RAGForge features native integration with Google's state-of-the-art embedding engine via the official `google-genai` SDK:

- **Model**: `gemini-embedding-001`
- **Output Dimensionality**: `768` floats (optimized for dense pgvector retrieval)
- **Task Types**:
  - `RETRIEVAL_DOCUMENT`: Applied automatically during text extraction and chunk ingestion.
  - `RETRIEVAL_QUERY`: Applied automatically during user semantic search queries and RAG retrieval.
- **API Key**: Requires a Google AI Studio API key (`GEMINI_API_KEY` or `EMBEDDING_API_KEY`).
- **Free-Tier Friendly**: Generous rate limits and quotas suitable for production testing.
- **Provider Switching & Re-embedding**: If switching from OpenAI (1536 dimensions) to Gemini (768 dimensions), RAGForge automatically updates the underlying pgvector column type on startup and resets affected documents so they can be cleanly re-processed.

### Configuration

Set the following in your `.env` file:

```env
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768
EMBEDDING_API_KEY=YOUR_GEMINI_API_KEY
# Alternatively:
# GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend (React 18 + Vite + Tailwind CSS)"]
        UI["Modern Dashboard / Chat / Collections / Documents"]
        AxiosClient["Axios API Client (JWT Interceptor)"]
        UI --> AxiosClient
    end

    subgraph Gateway ["Nginx / API Layer"]
        Nginx["Reverse Proxy (Port 80)"]
        FastAPI["FastAPI App (Port 8000)"]
        Nginx -->|/api/*| FastAPI
        Nginx -->|/*| UI
    end

    subgraph Processing ["Ingestion & RAG Engine"]
        Extractor["Extractors (PDF, DOCX, TXT)"]
        Splitter["Recursive Character Text Splitter"]
        Embedder["Embedding Service (OpenAI / Mock)"]
        LLM["LLM Service (GPT-4o-mini / Grounded Mock)"]
    end

    subgraph Storage ["Database & Storage"]
        Postgres[("PostgreSQL 16 + pgvector")]
        DiskStorage[("Persistent Storage (/app/storage/uploads)")]
    end

    FastAPI --> Extractor
    Extractor --> Splitter
    Splitter --> Embedder
    Embedder --> Postgres
    FastAPI --> LLM
    FastAPI --> Postgres
    FastAPI --> DiskStorage
```

---

## 4. RAG Pipeline Explained (Interview Guide)

When discussing RAGForge in a technical interview, use the following mental model:

```
[Document Ingestion]
File (PDF/DOCX/TXT) 
  → Clean & Normalize Text 
  → Recursive Chunking (e.g., 800 chars, 150 overlap)
  → Vector Embedding (e.g., 768-dim float vector via Gemini)
  → Stored in PostgreSQL with pgvector

[Retrieval & Generation Query]
User Question 
  → Query Embedding (Same vector space via RETRIEVAL_QUERY)
  → Cosine Distance Similarity Search (<=> operator)
  → Top-K Relevant Document Chunks (Filtered by User & Collection)
  → Context Assembly with Source Citations
  → LLM Prompting with Anti-Hallucination Guardrails
  → Grounded Answer + Verifiable Source References
```

### Key Technical Concepts to Highlight in Interviews:
1. **Why Chunk Documents?**
   LLMs have token limits, and sending whole documents degrades attention and inflates latency/cost. Chunking segments text into semantically cohesive units while preserving page and position metadata.
2. **Why Overlap?**
   A boundary split might bisect a crucial sentence or fact. Configurable overlap (e.g., 150 characters) ensures continuity across adjacent chunks.
3. **Why pgvector over dedicated vector databases?**
   Keeping relational data (Users, Collections, Permissions, Timestamps) in the exact same database as vector embeddings enables **single-query transactional operations**, ACID guarantees, and unified security policies without synchronizing across disparate databases.
4. **Anti-Hallucination Guardrails**:
   The system prompt explicitly commands the model to decline answering if the retrieved chunks do not contain sufficient evidence, preventing fabricated assertions.

---

## 5. Technology Stack

- **Frontend**: React 18, Vite, JavaScript, Tailwind CSS, React Router v6, Axios, Lucide React icons.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn.
- **Vector Database**: PostgreSQL 16 with `pgvector` extension (and SQLite JSON vector fallback for standalone testing).
- **Document Extractors**: `pypdf` (page-aware PDF extraction), `python-docx` (paragraphs & tables), pure-Python robust text decoders.
- **AI & Embedding SDKs**: `google-genai` (Gemini embeddings), `openai` (GPT-4o completions & optional embeddings).
- **Security**: JWT (`PyJWT`), `bcrypt` password hashing, CORS, Defensive Security Headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`).
- **Containerization**: Docker, multi-stage Dockerfiles, Docker Compose, Nginx reverse proxy.
- **Testing**: `pytest`, `pytest-asyncio`, `httpx` TestClient (44 automated tests).

---

## 6. Project Directory Structure

```
RAGForge/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py             # Auth & admin dependency guards
│   │   │   └── v1/
│   │   │       ├── auth.py         # /register, /login, /me
│   │   │       ├── chat.py         # /conversations, /messages
│   │   │       ├── collections.py  # /collections CRUD & document membership
│   │   │       ├── dashboard.py    # /dashboard/stats
│   │   │       ├── documents.py    # /documents upload, listing, chunks, process
│   │   │       ├── health.py       # /health diagnostic check
│   │   │       └── search.py       # /search semantic vector query
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings configuration
│   │   │   ├── database.py         # SQLAlchemy engine, SessionLocal, pgvector init
│   │   │   └── security.py         # bcrypt hashing & JWT token encoder/decoder
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── collection.py
│   │   │   ├── conversation.py
│   │   │   ├── document.py
│   │   │   └── user.py
│   │   ├── rag/                    # RAG Engine core
│   │   │   ├── embeddings.py       # Abstract EmbeddingService (Gemini, OpenAI, Mock)
│   │   │   ├── extractors.py       # PDF, DOCX, TXT extractors & normalizer
│   │   │   ├── llm.py              # Abstract LLMService (OpenAI & Mock)
│   │   │   ├── prompts.py          # Grounded system & user prompt templates
│   │   │   ├── text_splitter.py    # RecursiveCharacterTextSplitter
│   │   │   └── vector_store.py     # Dual-dialect VectorStore (pgvector & SQLite)
│   │   ├── schemas/                # Pydantic v2 schemas
│   │   ├── services/               # Business logic services
│   │   └── utils/
│   │       └── file_utils.py       # Path traversal sanitization & storage helpers
│   ├── tests/                      # 44 automated unit & integration tests
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/             # ProtectedRoute, UploadModal, DetailsModal
│   │   ├── contexts/               # AuthContext (JWT session persistence)
│   │   ├── layouts/                # DashboardLayout with responsive sidebar
│   │   ├── pages/                  # Dashboard, Documents, Collections, Chat, Auth
│   │   └── services/               # Centralized Axios API services
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   └── init-pgvector.sql
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 7. Database Architecture

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns
    USERS ||--o{ COLLECTIONS : creates
    USERS ||--o{ CONVERSATIONS : conducts
    COLLECTIONS ||--o{ DOCUMENTS : groups
    COLLECTIONS ||--o{ CONVERSATIONS : scopes
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : contains
    CONVERSATIONS ||--o{ MESSAGES : has

    USERS {
        string id PK
        string name
        string email UK
        string password_hash
        string role
        datetime created_at
    }

    COLLECTIONS {
        string id PK
        string user_id FK
        string name
        string description
        datetime created_at
    }

    DOCUMENTS {
        string id PK
        string user_id FK
        string collection_id FK
        string original_filename
        string stored_filename UK
        string file_type
        bigint file_size
        string processing_status
        int page_count
        text error_message
        datetime created_at
    }

    DOCUMENT_CHUNKS {
        string id PK
        string document_id FK
        int chunk_index
        text content
        json chunk_metadata
        vector embedding
        datetime created_at
    }

    CONVERSATIONS {
        string id PK
        string user_id FK
        string collection_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    MESSAGES {
        string id PK
        string conversation_id FK
        string role
        text content
        json sources
        datetime created_at
    }
```

---

## 8. Environment Variables

Copy `.env.example` to `.env` in the root and in `backend/.env`:

```bash
cp .env.example .env
```

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string with psycopg driver | `postgresql+psycopg://postgres:postgres@localhost:5432/ragforge` |
| `JWT_SECRET` | Secret key used for signing JWT tokens | `min_32_characters_random_secret` |
| `JWT_ALGORITHM` | Encryption algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session expiration window | `1440` (24 hours) |
| `CORS_ORIGINS` | Permitted origins | `["http://localhost:5173","http://localhost:80"]` |
| `UPLOAD_DIR` | Filesystem path for uploaded files | `./storage/uploads` |
| `MAX_FILE_SIZE_BYTES` | Maximum upload size per document | `26214400` (25 MB) |
| `CHUNK_SIZE` | Target character count per semantic chunk | `800` |
| `CHUNK_OVERLAP` | Character overlap between adjacent chunks | `150` |
| `TOP_K` | Number of chunks retrieved per question | `5` |
| `SIMILARITY_THRESHOLD` | Minimum cosine similarity score | `0.65` |
| `EMBEDDING_PROVIDER` | Embedding provider (`gemini`, `openai`, or mock fallback) | `gemini` |
| `EMBEDDING_MODEL` | Embedding model name | `gemini-embedding-001` |
| `EMBEDDING_DIMENSIONS` | Vector dimensionality | `768` |
| `EMBEDDING_API_KEY` | API key for configured embedding provider | `AIzaSy...` or `sk-...` |
| `GEMINI_API_KEY` | Dedicated Google AI Studio key (alternative to EMBEDDING_API_KEY) | `AIzaSy...` |
| `LLM_PROVIDER` | LLM provider (`openai` or empty for mock) | `openai` |
| `LLM_MODEL` | LLM model name | `gpt-4o-mini` |
| `LLM_API_KEY` | OpenAI API key for chat completions | `sk-...` |
| `LLM_TEMPERATURE` | Generation randomness | `0.2` |

> **Note**: If `GEMINI_API_KEY`, `EMBEDDING_API_KEY`, and `LLM_API_KEY` are left blank, RAGForge automatically operates in **Deterministic Mock Mode**, allowing all APIs, tests, and UI features to run without cloud accounts.

---

## 9. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 16+ with pgvector (optional for local SQLite mode)

### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Linux/macOS)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run test suite
pytest -v

# Start development server
uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000`
Interactive Swagger Docs: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
Frontend Web UI will be accessible at: `http://localhost:5173`

---

## 10. Docker & Containerized Deployment

Run the complete multi-container stack (**Frontend**, **FastAPI Backend**, and **PostgreSQL with pgvector**) with one command:

```bash
docker compose up --build
```

### Containers Started:
1. `ragforge-postgres`: PostgreSQL 16 with `pgvector` pre-configured via `init-pgvector.sql` on port `5432`.
2. `ragforge-backend`: FastAPI application on port `8000`.
3. `ragforge-frontend`: Production Nginx web server on port `80` serving the compiled React SPA and proxying `/api/*` to the backend.

Open your browser to: **`http://localhost`**

---

## 11. API Documentation

Interactive OpenAPI / Swagger documentation is automatically available at:
`http://localhost:8000/docs`

### Core Endpoints Overview:
- `POST /api/v1/auth/register` — Create account and receive JWT bearer token.
- `POST /api/v1/auth/login` — Authenticate and receive token.
- `GET  /api/v1/auth/me` — Retrieve authenticated user profile.
- `POST /api/v1/documents/upload` — Multipart document upload with file validation.
- `GET  /api/v1/documents` — Search, filter, and list user documents.
- `POST /api/v1/documents/{id}/process` — Trigger chunking, vector embedding, and storage.
- `GET  /api/v1/documents/{id}/chunks` — Inspect extracted chunks and metadata.
- `DELETE /api/v1/documents/{id}` — Permanently delete document, chunks, and disk storage.
- `POST /api/v1/search` — Pure semantic vector search query returning ranked chunks.
- `POST /api/v1/rag/query` — End-to-end RAG question answering with verified citations.
- `GET  /api/v1/conversations` — List conversation threads.
- `POST /api/v1/conversations/{id}/messages` — Multi-turn dialogue with RAG citations.
- `GET  /api/v1/dashboard/stats` — Aggregated system analytics and pipeline health.

---

## 12. Security & Multi-Tenancy

- **Password Security**: Passwords are never stored in plaintext; salted and hashed using `bcrypt`.
- **JWT Protection**: Signed with `HS256`, strictly validated on all protected endpoints, with automatic 401 handling on the frontend.
- **Path Traversal Defense**: All filenames are stripped of directory traversal characters and stored as collision-resistant UUIDs within an absolute checked directory path.
- **Multi-Tenant Data Privacy**: Every query, retrieval, and deletion explicitly filters on `user_id = current_user.id`. Users can never retrieve or query another user's documents.
- **Defensive Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`.
- **Safe Error Responses**: Server exceptions are caught by a global middleware that logs internal stack traces securely while returning clean JSON error responses to clients.

---

## 13. Screenshots Placeholder

| Executive Dashboard | Document Chat & Citations |
| :---: | :---: |
| *(Dashboard view showing real-time statistics and processing status)* | *(ChatGPT-style chat interface with interactive source citation pills)* |

| Document Management & Chunk Inspector | Knowledge Collections |
| :---: | :---: |
| *(Document table with status badges and extracted chunks viewer)* | *(Collections management with domain-scoped document assignment)* |

---

## 14. Future Roadmap

- [ ] **Hybrid Search**: Combine BM25 keyword search with dense pgvector semantic embeddings (Reciprocal Rank Fusion).
- [ ] **Streaming Responses**: Server-Sent Events (SSE) for streaming LLM tokens in the chat UI.
- [ ] **Reranking**: Cross-encoder reranker (e.g., Cohere Rerank or BGE-Reranker) for improved Top-K precision.
- [ ] **OCR Support**: Ingestion of scanned PDFs and images using Tesseract or AWS Textract.
- [ ] **Role-Based Access Control (RBAC)**: Team-level workspaces and permissions (Viewer, Editor, Admin).

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
