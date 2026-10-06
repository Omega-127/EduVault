# EduVault

**AI-Powered University Knowledge & Document Assistant**

EduVault transforms fragmented institutional documentation into a searchable, conversational knowledge layer. Students, faculty, and administrative staff can ask natural-language questions and receive concise, source-grounded answers with document, section, and page-level citations — no more manually scanning multi-page PDFs.

> _"EduVault turns fragmented university documents into a trusted, searchable knowledge assistant that answers questions with evidence, not guesses."_

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running with Docker](#running-with-docker)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

University information is scattered across PDF circulars, Word memos, CSV timetables, and department handbooks. EduVault ingests all of this into a unified semantic knowledge base and exposes it through a conversational chat interface.

Key design principles:

- **Source-grounded generation** — answers are constructed strictly from retrieved institutional content, never fabricated.
- **Explicit citations** — every answer links back to the originating document, section, and page.
- **Safe failure** — when retrieval confidence falls below the configured threshold, the system returns a standardized "Information not found" response rather than a speculative answer.
- **Async ingestion** — large document processing jobs run in the background and never block the API.

---

## Features

| Feature | Description |
|---|---|
| Multi-format ingestion | Upload PDF, DOCX, TXT, and CSV documents via the admin dashboard |
| Semantic RAG pipeline | Chunk → embed → index → retrieve using dense vector search |
| Grounded generation | LLM answers are constrained to retrieved institutional context |
| Page-level citations | Every response exposes document name, section, and page number |
| Unanswerable fallback | Configurable similarity threshold gates generation; returns a safe fallback on low-confidence retrieval |
| Streaming responses | Chat answers stream in real time over WebSockets |
| Role-based access | JWT-authenticated accounts with student, faculty, and admin roles |
| Admin dashboard | Upload documents, monitor ingestion jobs, review unanswered queries |
| Persistent history | Chat sessions, feedback, and system logs stored in PostgreSQL |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js / Next.js · TypeScript · Tailwind CSS · Lucide React |
| Backend | FastAPI · Uvicorn · Python 3.11+ |
| Auth | JWT (python-jose) · bcrypt |
| Database | PostgreSQL · SQLAlchemy · Alembic |
| Object Storage | Amazon S3 / MinIO |
| Async Workers | Celery · Redis |
| Document Parsers | PyPDFLoader · Docx2txtLoader · Pandas |
| Vector Database | ChromaDB / Qdrant / Pgvector |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) / Gemini Embeddings |
| LLM Orchestration | LangChain · Gemini 1.5 Flash / Groq Llama-3.3-70B |
| Deployment | Docker · Docker Compose · Nginx |

---

## Architecture

EduVault follows a five-tier architecture:

```
┌─────────────────────────────────────────────────────┐
│  Presentation  │  React/Next.js  ·  Tailwind CSS     │
├─────────────────────────────────────────────────────┤
│  API Layer     │  FastAPI  ·  JWT  ·  WebSockets      │
├─────────────────────────────────────────────────────┤
│  Async Pipeline│  Celery + Redis / BackgroundTasks    │
├─────────────────────────────────────────────────────┤
│  Storage       │  PostgreSQL  ·  S3/MinIO  ·  VectorDB│
├─────────────────────────────────────────────────────┤
│  Generation    │  LangChain  ·  Gemini / Groq         │
└─────────────────────────────────────────────────────┘
```

For a detailed breakdown of each module, directory structure, and component-level design decisions, see [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Getting Started

### Prerequisites

- Docker & Docker Compose v2+
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- A Gemini API key **or** a Groq API key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/eduvault.git
cd eduvault

# 2. Copy and fill in environment variables
cp .env.example .env

# 3. Start all services
docker compose up --build
```

The application will be available at:
- **Frontend** → `http://localhost:3000`
- **Backend API** → `http://localhost:8000`
- **API Docs (Swagger)** → `http://localhost:8000/docs`
- **MinIO Console** → `http://localhost:9001`

### Environment Variables

Create a `.env` file at the project root. A full template is provided in `.env.example`.

```env
# --- Application ---
APP_ENV=development
SECRET_KEY=your-secret-key-here

# --- Database ---
DATABASE_URL=postgresql://eduvault:password@db:5432/eduvault

# --- Object Storage ---
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=eduvault-docs

# --- Redis / Celery ---
REDIS_URL=redis://redis:6379/0

# --- Vector Database ---
VECTOR_DB=chromadb               # chromadb | qdrant | pgvector
CHROMA_HOST=chromadb
CHROMA_PORT=8001

# --- Embeddings ---
EMBEDDING_MODEL=all-MiniLM-L6-v2  # or gemini

# --- LLM ---
LLM_PROVIDER=gemini               # gemini | groq
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

# --- RAG ---
RETRIEVAL_TOP_K=4
SIMILARITY_THRESHOLD=0.35
```

### Running with Docker

```bash
# Start all services (frontend, backend, db, redis, minio, chromadb)
docker compose up

# Run in detached mode
docker compose up -d

# View logs for a specific service
docker compose logs -f backend

# Stop all services
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v
```

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Celery Worker:**
```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info
```

---

## Usage

### Admin: Upload a Document

1. Log in with an admin account.
2. Navigate to **Admin → Documents → Upload**.
3. Select a PDF, DOCX, TXT, or CSV file and submit.
4. The ingestion pipeline runs asynchronously — monitor progress in the **Jobs** panel.

### Student / Faculty: Ask a Question

1. Log in and open any chat session (or start a new one).
2. Type a natural-language question, e.g.:
   - _"What is the minimum attendance required to sit for exams?"_
   - _"When is the last date to apply for a re-evaluation?"_
   - _"Which scholarship requires a minimum CGPA of 8.0?"_
3. EduVault retrieves the most relevant passages and generates a grounded answer with inline citations.
4. If no sufficiently relevant content is found, it responds: **"Information not found in the institutional knowledge base."**

---

## Project Structure

```
eduvault/
├── frontend/                  # Next.js application
├── backend/                   # FastAPI application
├── docker/                    # Dockerfiles per service
├── docker-compose.yml
├── .env.example
├── README.md
└── ARCHITECTURE.md
```

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full expanded directory tree.

---

## API Reference

Interactive API documentation is auto-generated by FastAPI:

- **Swagger UI** → `http://localhost:8000/docs`
- **ReDoc** → `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Obtain JWT access token |
| `POST` | `/api/v1/documents/upload` | Upload an institutional document (admin) |
| `GET` | `/api/v1/documents/` | List all indexed documents |
| `POST` | `/api/v1/chat/sessions` | Create a new chat session |
| `POST` | `/api/v1/chat/sessions/{id}/messages` | Send a question and receive a streamed answer |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | Retrieve chat history |
| `POST` | `/api/v1/feedback/` | Submit feedback on a response |
| `GET` | `/api/v1/admin/logs` | View system and query logs (admin) |

---

## Roadmap

- [ ] **Interactive Citation Drawer** — open a cited PDF at the exact supporting page with passage highlighting
- [ ] **Hybrid Router-RAG** — route tabular queries (schedules, fees) to SQL/Pandas while policy questions use vector retrieval
- [ ] **Cohort Metadata Filtering** — filter retrieval by department, year, or degree programme
- [ ] **Attendance & Policy Calculators** — combine extracted policies with dynamic calculations
- [ ] **Policy Conflict Detector** — surface contradictions between newer circulars and older policy documents
- [ ] **Admin Analytics Dashboard** — identify documentation gaps from unanswered and negatively-rated queries

---

## Contributing

Contributions are welcome. Please open an issue first to discuss significant changes.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
# Open a pull request
```

Please follow the existing code style — `ruff` for Python, `eslint` + `prettier` for TypeScript.

---

## License

This project is licensed under the [MIT License](./LICENSE).
