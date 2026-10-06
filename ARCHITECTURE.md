# EduVault — Architecture Reference

This document covers the full technical architecture of EduVault: module breakdown, technology choices and rationale, directory structures, component responsibilities, data flow, and inter-service communication.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Five-Tier Architecture](#2-five-tier-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Module: Frontend](#4-module-frontend)
5. [Module: Backend API](#5-module-backend-api)
6. [Module: Async Ingestion Pipeline](#6-module-async-ingestion-pipeline)
7. [Module: Storage Layer](#7-module-storage-layer)
8. [Module: RAG Engine](#8-module-rag-engine)
9. [Data Models](#9-data-models)
10. [RAG Pipeline — End-to-End Flow](#10-rag-pipeline--end-to-end-flow)
11. [Authentication & Authorization](#11-authentication--authorization)
12. [Inter-Service Communication](#12-inter-service-communication)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Configuration & Environment](#14-configuration--environment)
15. [Technology Decision Notes](#15-technology-decision-notes)

---

## 1. System Overview

```
                        ┌──────────────────────┐
                        │      Browser         │
                        │  Next.js / React     │
                        └────────┬─────────────┘
                                 │  REST + WebSocket
                        ┌────────▼─────────────┐
                        │   FastAPI Backend     │
                        │  (Uvicorn + Nginx)    │
                        └──┬──────────┬────────┘
                           │          │
              ┌────────────▼──┐  ┌────▼───────────────┐
              │  Celery Worker│  │   RAG Engine        │
              │  (Redis queue)│  │  LangChain + LLM    │
              └──────┬────────┘  └────────┬────────────┘
                     │                    │
        ┌────────────▼────────────────────▼────────────┐
        │                  Storage Layer                │
        │  PostgreSQL  ·  MinIO/S3  ·  ChromaDB/Qdrant  │
        └───────────────────────────────────────────────┘
```

---

## 2. Five-Tier Architecture

| Tier | Name | Responsibilities |
|------|------|-----------------|
| 1 | **Presentation** | Chat UI, admin dashboard, citation drawer, document upload interface |
| 2 | **API & Middleware** | Authentication, routing, REST endpoints, WebSocket streaming, rate limiting |
| 3 | **Async Pipeline** | Non-blocking parsing, chunking, metadata enrichment, embedding, vector indexing |
| 4 | **Storage** | Relational records, raw document blobs, semantic vectors |
| 5 | **Generation** | Context orchestration, safety gates, grounded answer generation, citation assembly |

---

## 3. Directory Structure

```
eduvault/
│
├── frontend/                        # Tier 1 — Next.js application
│   ├── public/
│   ├── src/
│   │   ├── app/                     # Next.js App Router pages
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── chat/
│   │   │   │   ├── [sessionId]/page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── admin/
│   │   │   │   ├── documents/page.tsx
│   │   │   │   ├── users/page.tsx
│   │   │   │   └── logs/page.tsx
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── CitationBadge.tsx
│   │   │   │   ├── CitationDrawer.tsx  # Future
│   │   │   │   └── InputBar.tsx
│   │   │   ├── admin/
│   │   │   │   ├── DocumentUploader.tsx
│   │   │   │   ├── DocumentTable.tsx
│   │   │   │   └── JobStatusPanel.tsx
│   │   │   └── ui/                  # Shared UI primitives (shadcn-style)
│   │   │       ├── Button.tsx
│   │   │       ├── Badge.tsx
│   │   │       ├── Modal.tsx
│   │   │       └── Spinner.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts           # WebSocket + streaming state
│   │   │   ├── useDocuments.ts
│   │   │   └── useAuth.ts
│   │   ├── lib/
│   │   │   ├── api.ts               # Axios/fetch client with auth headers
│   │   │   ├── ws.ts                # WebSocket connection helper
│   │   │   └── utils.ts
│   │   ├── store/
│   │   │   └── authStore.ts         # Zustand global auth state
│   │   └── types/
│   │       ├── chat.ts
│   │       ├── document.ts
│   │       └── user.ts
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                         # Tiers 2–5 — FastAPI application
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, router registration
│   │   ├── config.py                # Pydantic Settings; reads .env
│   │   ├── dependencies.py          # Shared FastAPI Depends (db session, current user)
│   │   │
│   │   ├── api/                     # Tier 2: API layer
│   │   │   └── v1/
│   │   │       ├── router.py        # Mounts all v1 sub-routers
│   │   │       ├── auth.py          # /auth/register, /auth/login, /auth/refresh
│   │   │       ├── documents.py     # /documents/ CRUD + upload trigger
│   │   │       ├── chat.py          # /chat/sessions + /messages (WS streaming)
│   │   │       ├── feedback.py      # /feedback/
│   │   │       └── admin.py         # /admin/logs, /admin/users (role-gated)
│   │   │
│   │   ├── core/                    # Cross-cutting concerns
│   │   │   ├── security.py          # JWT encode/decode, password hashing
│   │   │   ├── exceptions.py        # Custom HTTP exception handlers
│   │   │   └── logging.py           # Structured logging setup
│   │   │
│   │   ├── db/                      # Tier 4a: Relational storage
│   │   │   ├── base.py              # SQLAlchemy declarative base
│   │   │   ├── session.py           # Async engine + session factory
│   │   │   └── models/
│   │   │       ├── user.py
│   │   │       ├── document.py
│   │   │       ├── chunk.py
│   │   │       ├── chat_session.py
│   │   │       ├── message.py
│   │   │       ├── feedback.py
│   │   │       └── system_log.py
│   │   │
│   │   ├── schemas/                 # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   ├── feedback.py
│   │   │   └── admin.py
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py  # Orchestrates upload → S3 → Celery dispatch
│   │   │   ├── chat_service.py      # Calls RAG engine; streams response
│   │   │   └── feedback_service.py
│   │   │
│   │   ├── ingestion/               # Tier 3: Async pipeline
│   │   │   ├── tasks.py             # Celery task definitions
│   │   │   ├── parsers/
│   │   │   │   ├── pdf_parser.py    # PyPDFLoader wrapper
│   │   │   │   ├── docx_parser.py   # Docx2txtLoader wrapper
│   │   │   │   ├── txt_parser.py
│   │   │   │   └── csv_parser.py    # Pandas-based
│   │   │   ├── chunker.py           # RecursiveCharacterTextSplitter (1000/200)
│   │   │   ├── metadata_enricher.py # Attaches file/page/section/timestamp
│   │   │   └── embedder.py          # Calls embedding model; writes to vector DB
│   │   │
│   │   ├── rag/                     # Tier 5: RAG / generation engine
│   │   │   ├── retriever.py         # Vector similarity search; threshold gate
│   │   │   ├── generator.py         # LangChain chain; prompt template; LLM call
│   │   │   ├── citation_builder.py  # Assembles citation objects from chunk metadata
│   │   │   └── prompts.py           # Prompt templates (system, user, fallback)
│   │   │
│   │   ├── storage/                 # Tier 4b/c: Object + vector storage adapters
│   │   │   ├── object_store.py      # S3/MinIO abstraction (boto3)
│   │   │   └── vector_store.py      # ChromaDB / Qdrant / Pgvector abstraction
│   │   │
│   │   └── worker/
│   │       └── celery_app.py        # Celery application instance + broker config
│   │
│   ├── alembic/                     # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker/
│   ├── nginx/
│   │   └── nginx.conf               # Reverse proxy; routes /api → backend, / → frontend
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
│
├── docker-compose.yml               # Orchestrates all services
├── .env.example
├── README.md
└── ARCHITECTURE.md
```

---

## 4. Module: Frontend

### Technology

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Framework | Next.js 14 (App Router) | SSR/SSG for public pages; RSC reduces client JS bundle |
| Language | TypeScript | Type-safe API contracts; IDE tooling |
| Styling | Tailwind CSS | Utility-first; consistent design tokens; no runtime CSS |
| Icons | Lucide React | Lightweight, tree-shakeable icon set |
| State (global) | Zustand | Minimal boilerplate; sufficient for auth token + session state |
| State (server) | TanStack Query | Caching, background refetch, optimistic updates for REST calls |
| WebSocket | Native `WebSocket` API wrapped in `useChat` hook | Full control over streaming chunk assembly |
| HTTP client | Axios | Interceptors for JWT injection and 401 refresh |

### Key Components

#### `ChatWindow`
- Maintains the rendered message list.
- Opens a WebSocket connection via `useChat` on mount.
- Appends streamed tokens to the last assistant message in real time.
- On completion, hydrates `CitationBadge` components from the metadata frame sent at the end of the stream.

#### `MessageBubble`
- Renders markdown (via `react-markdown` + `remark-gfm`).
- Attaches inline `CitationBadge` components for each cited source.

#### `CitationBadge`
- Displays `[Doc Name · p.N]` as a tappable chip.
- On click, opens `CitationDrawer` (future) or scrolls to a source summary panel.

#### `DocumentUploader` (Admin)
- Multipart form upload to `POST /api/v1/documents/upload`.
- Polls `GET /api/v1/documents/{id}/status` every 3 s to show ingestion progress.

### Routing (App Router)

```
/                        → redirect to /chat
/(auth)/login            → login page (unauthenticated)
/(auth)/register         → registration page
/chat                    → session list
/chat/[sessionId]        → active chat view
/admin/documents         → document management (admin role)
/admin/users             → user management (admin role)
/admin/logs              → system logs (admin role)
```

### Auth Flow (Frontend)

1. Login → receives `access_token` (JWT) + `refresh_token`.
2. Tokens stored in `authStore` (Zustand); `access_token` kept in memory, `refresh_token` in an `httpOnly` cookie set by the backend.
3. Axios interceptor attaches `Authorization: Bearer <token>` to every request.
4. On 401, interceptor calls `POST /api/v1/auth/refresh` and retries once.

---

## 5. Module: Backend API

### Technology

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Framework | FastAPI | Async-native; auto OpenAPI docs; Pydantic validation |
| Server | Uvicorn | ASGI server; handles HTTP + WebSocket on same port |
| Auth | python-jose (JWT) · passlib (bcrypt) | Industry-standard; stateless tokens |
| ORM | SQLAlchemy 2.0 (async) · asyncpg | Async queries; full control over schema |
| Migrations | Alembic | Version-controlled schema changes |
| Config | Pydantic Settings | Reads `.env`; validates all config at startup |

### Router Layout (`app/api/v1/`)

```
/auth
  POST /register      → create user account
  POST /login         → return JWT access + refresh tokens
  POST /refresh       → rotate access token

/documents
  POST /upload        → admin: store file in S3, dispatch Celery task
  GET  /              → list documents with metadata
  GET  /{id}          → single document detail
  GET  /{id}/status   → ingestion job status
  DELETE /{id}        → admin: remove document + vectors

/chat
  POST /sessions              → create new chat session
  GET  /sessions              → list user's sessions
  GET  /sessions/{id}         → session metadata
  WS   /sessions/{id}/stream  → WebSocket: streaming Q&A
  GET  /sessions/{id}/messages→ full message history

/feedback
  POST /             → submit rating + comment for a message

/admin
  GET  /logs         → query system logs (admin)
  GET  /users        → list/manage users (admin)
  GET  /stats        → aggregate usage stats (admin)
```

### Middleware Stack (execution order)

1. `CORSMiddleware` — allows frontend origin in development.
2. `TrustedHostMiddleware` — header validation in production.
3. `AuthMiddleware` — validates JWT on protected routes.
4. Route handler.
5. `ExceptionHandlers` — maps domain exceptions to HTTP status codes.

### WebSocket Streaming (`/chat/sessions/{id}/stream`)

```
Client → WS connect (with JWT in query param or first message)
Client → sends JSON: { "question": "..." }
Server → validates session ownership
Server → calls chat_service.stream_answer()
Server → emits JSON frames:
           { "type": "token",    "data": "partial text" }
           { "type": "token",    "data": "..." }
           ...
           { "type": "citation", "data": [ { doc, page, section }, ... ] }
           { "type": "done" }
Client → assembles tokens; renders citations on "done"
```

---

## 6. Module: Async Ingestion Pipeline

### Technology

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Task queue | Celery | Mature, battle-tested; retries, priorities, monitoring |
| Broker + backend | Redis | Low-latency; doubles as result backend |
| PDF parsing | LangChain `PyPDFLoader` | Page-aware extraction; preserves page numbers |
| DOCX parsing | `Docx2txtLoader` | Lightweight; preserves paragraph structure |
| CSV parsing | Pandas | Structured rows converted to natural-language strings |
| Chunking | LangChain `RecursiveCharacterTextSplitter` | Respects sentence boundaries; configurable size/overlap |

### Pipeline Stages

```
[Upload event]
     │
     ▼
[1. Store raw file]          → object_store.put(file)  →  S3 / MinIO
     │
     ▼
[2. Dispatch Celery task]    → tasks.ingest_document.delay(document_id)
     │
     ▼  (runs in worker process)
[3. Fetch file from S3]      → object_store.get(path)
     │
     ▼
[4. Parse]                   → select parser by MIME type
     │                          pdf_parser / docx_parser / txt_parser / csv_parser
     ▼
[5. Chunk]                   → chunker.split(text, size=1000, overlap=200)
     │
     ▼
[6. Metadata enrichment]     → attach {file_name, page, section, upload_ts, doc_id}
     │
     ▼
[7. Embed]                   → embedder.embed_batch(chunks)
     │                          all-MiniLM-L6-v2  or  Gemini Embed API
     ▼
[8. Index]                   → vector_store.upsert(vectors, metadata)
     │
     ▼
[9. Update DB status]        → document.status = "indexed"
```

### Chunking Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `chunk_size` | 1000 characters | Fits comfortably within LLM context; granular enough for precise citation |
| `chunk_overlap` | 200 characters | Preserves cross-boundary context |
| Splitter priority | `\n\n` → `\n` → ` ` → `""` | Prefers paragraph breaks before sentence breaks |

### Parser Behaviour

**PDF** — `PyPDFLoader` extracts text page by page. Page number is stored as `page` in chunk metadata.

**DOCX** — `Docx2txtLoader` extracts paragraph text. Heading paragraphs are detected via style names and stored as `section` in metadata.

**TXT** — Split on newlines; no structural metadata beyond file name.

**CSV** — Each row is serialised as a key-value string: `"Column1: value1 | Column2: value2 ..."`. Useful for timetables and fee structures.

---

## 7. Module: Storage Layer

### PostgreSQL (Relational)

Used for all structured application state: user accounts, document metadata, chat history, feedback, and logs.

**Connection:** `asyncpg` driver via `SQLAlchemy 2.0` async engine.
**Migrations:** Alembic — every schema change is versioned.

### Amazon S3 / MinIO (Object Storage)

Raw uploaded files are stored here before and after processing. MinIO is the default in development (Docker); S3 in production.

**Bucket layout:**
```
eduvault-docs/
├── raw/
│   └── {document_id}/{original_filename}
```

**Client:** `boto3` behind a thin `ObjectStore` abstraction class so S3/MinIO are interchangeable via config.

### Vector Database

Three options are supported via a pluggable `VectorStore` abstraction:

| Option | Best For | Notes |
|--------|----------|-------|
| **ChromaDB** | Local development / small deployments | Zero infrastructure; embedded or server mode |
| **Qdrant** | Production / scalable deployments | Purpose-built; filtering on metadata; gRPC API |
| **Pgvector** | Single-DB simplicity | Reuses existing PostgreSQL; `pgvector` extension |

The `VECTOR_DB` env var selects the backend at startup. The `VectorStore` class exposes three methods: `upsert()`, `query()`, and `delete_by_document_id()`.

### Redis

Serves two roles:
1. **Celery broker** — task queuing.
2. **Celery result backend** — task status polling.

---

## 8. Module: RAG Engine

### Technology

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Orchestration | LangChain | Composable chains; built-in retriever/LLM abstractions |
| LLM (primary) | Gemini 1.5 Flash | Fast, cost-efficient, long context window |
| LLM (alternative) | Groq Llama-3.3-70B | Low latency inference; open-weight model |
| Embeddings | `all-MiniLM-L6-v2` | Lightweight; runs locally; no API cost |
| Embeddings (alt.) | Gemini Embed API | Higher quality for domain-specific content |

### Retriever (`rag/retriever.py`)

```python
def retrieve(query: str, top_k: int = 4, threshold: float = 0.35) -> list[Chunk] | None:
    query_vector = embedder.embed(query)
    results = vector_store.query(query_vector, top_k=top_k)

    # Safety gate: reject if best match is below threshold
    if not results or results[0].distance > threshold:
        return None          # triggers fallback in generator

    return [r for r in results if r.distance <= threshold]
```

Distance metric: **cosine similarity** (lower = more similar in most VectorDB configurations using distance; check per-backend convention).

Threshold `0.35` is the configurable baseline. Lower = stricter (fewer answers); higher = more permissive (more hallucination risk). Adjust via `SIMILARITY_THRESHOLD` env var.

### Generator (`rag/generator.py`)

```
┌─────────────┐    ┌──────────────────┐    ┌────────────────┐
│   Retriever  │───▶│  Prompt Builder  │───▶│   LLM (stream) │
│  top-K chunks│    │ system + context │    │  Gemini/Groq   │
└─────────────┘    └──────────────────┘    └────────┬───────┘
                                                     │
                                            ┌────────▼───────┐
                                            │ Citation Builder│
                                            │ (from metadata) │
                                            └────────────────┘
```

### Prompt Template (`rag/prompts.py`)

```
SYSTEM:
You are EduVault, a university knowledge assistant.
Answer ONLY using the provided context passages.
If the context does not contain the answer, respond with exactly:
"Information not found in the institutional knowledge base."
Do not speculate, infer, or answer from general knowledge.
Always cite the document name and page number when available.

CONTEXT:
{formatted_chunks_with_metadata}

USER QUESTION:
{question}

ANSWER:
```

### Citation Builder (`rag/citation_builder.py`)

Extracts from each retrieved chunk's metadata:
```json
{
  "document_name": "Examination Regulations 2026.pdf",
  "page": 12,
  "section": "3.4 Re-evaluation Policy",
  "chunk_id": "abc123"
}
```
Returns a list of citation objects that are appended to the streamed WebSocket response.

### Fallback Behaviour

When `retriever.retrieve()` returns `None`:
1. Generator skips LLM call entirely.
2. Returns the standardised string: `"Information not found in the institutional knowledge base."`
3. A `system_log` entry is created with `event_type = "unanswerable_query"` for admin review.

---

## 9. Data Models

### User
```
id          UUID (PK)
email       VARCHAR UNIQUE
hashed_pw   VARCHAR
role        ENUM(student, faculty, admin)
created_at  TIMESTAMP
is_active   BOOLEAN
```

### Document
```
id              UUID (PK)
file_name       VARCHAR
storage_path    VARCHAR          ← S3/MinIO object key
mime_type       VARCHAR
status          ENUM(pending, processing, indexed, failed)
uploaded_by     UUID (FK → User)
uploaded_at     TIMESTAMP
chunk_count     INTEGER
```

### DocumentChunk
```
id              UUID (PK)
document_id     UUID (FK → Document)
text            TEXT
page            INTEGER
section         VARCHAR
vector_id       VARCHAR          ← ID in the vector store
created_at      TIMESTAMP
```

### ChatSession
```
id          UUID (PK)
user_id     UUID (FK → User)
title       VARCHAR
created_at  TIMESTAMP
updated_at  TIMESTAMP
```

### Message
```
id              UUID (PK)
session_id      UUID (FK → ChatSession)
role            ENUM(user, assistant)
content         TEXT
citations       JSONB            ← [{document_name, page, section}, ...]
created_at      TIMESTAMP
```

### Feedback
```
id          UUID (PK)
message_id  UUID (FK → Message)
user_id     UUID (FK → User)
rating      SMALLINT             ← 1–5
comment     TEXT
created_at  TIMESTAMP
```

### SystemLog
```
id          UUID (PK)
event_type  VARCHAR              ← e.g. "unanswerable_query", "ingestion_failed"
payload     JSONB
created_at  TIMESTAMP
```

---

## 10. RAG Pipeline — End-to-End Flow

```
Student types:  "What is the minimum attendance to appear for finals?"

1. Frontend  →  WS frame: { "question": "..." }

2. Backend   →  chat_service.stream_answer(session_id, question)
                  └─ calls rag/retriever.retrieve(question, top_k=4)

3. Retriever →  embeds question with all-MiniLM-L6-v2
             →  cosine search against ChromaDB/Qdrant
             →  returns 4 chunks from "Attendance Policy 2026.pdf"
                with distances [0.12, 0.18, 0.22, 0.29]  (all < 0.35 ✓)

4. Generator →  builds prompt:
                  SYSTEM: (grounded constraint)
                  CONTEXT: [chunk1 text | p.4 §2.1], [chunk2 text | p.4 §2.2], ...
                  USER: "What is the minimum attendance..."

             →  calls Gemini 1.5 Flash with streaming=True
             →  yields tokens over WebSocket:
                  { "type": "token", "data": "The minimum attendance required..." }
                  { "type": "token", "data": " is 75% as per Section 2.1..." }
                  ...
             →  assembles citations:
                  { "type": "citation", "data": [
                      { "document_name": "Attendance Policy 2026.pdf",
                        "page": 4, "section": "2.1 Attendance Requirements" }
                  ]}
                  { "type": "done" }

5. Backend   →  persists Message(role=assistant, content=..., citations=...)

6. Frontend  →  assembles streamed tokens into message bubble
             →  renders CitationBadge: [Attendance Policy 2026.pdf · p.4]
```

**Fallback path** (low-confidence retrieval):

```
3. Retriever →  best match distance = 0.61  (> 0.35 threshold ✗)
             →  returns None

4. Generator →  skips LLM call
             →  emits: { "type": "token", "data": "Information not found in the
                         institutional knowledge base." }
                        { "type": "done" }

5. Backend   →  logs SystemLog(event_type="unanswerable_query", payload={question})
```

---

## 11. Authentication & Authorization

### JWT Strategy

- `access_token`: short-lived (15 min), sent in `Authorization: Bearer` header.
- `refresh_token`: long-lived (7 days), sent as `httpOnly` cookie.
- Token payload: `{ sub: user_id, role: "student"|"faculty"|"admin", exp, iat }`.

### Role Guards

```python
# FastAPI dependency
async def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(403, "Insufficient permissions")
    return current_user
```

Applied to: `/documents/upload`, `/documents/{id}` DELETE, all `/admin/*` routes.

### WebSocket Auth

JWT is passed as a query parameter on the initial WS handshake:
```
ws://host/api/v1/chat/sessions/{id}/stream?token=<jwt>
```
The server validates the token before accepting the connection.

---

## 12. Inter-Service Communication

```
Frontend ──────HTTP/REST──────▶ Backend (FastAPI)
Frontend ──────WebSocket────────▶ Backend (FastAPI)
Backend  ──────Task dispatch────▶ Celery Worker (via Redis)
Backend  ──────SQL queries──────▶ PostgreSQL
Backend  ──────S3 API───────────▶ MinIO / Amazon S3
Backend  ──────gRPC/HTTP────────▶ ChromaDB / Qdrant
Celery   ──────S3 API───────────▶ MinIO / Amazon S3
Celery   ──────Embed API────────▶ Gemini / local model
Celery   ──────VectorDB API─────▶ ChromaDB / Qdrant
Nginx    ──────reverse proxy────▶ Frontend (port 3000)
                           └────▶ Backend (port 8000)
```

---

## 13. Deployment Architecture

### Docker Compose Services

```yaml
services:
  frontend:     # Next.js — port 3000
  backend:      # FastAPI / Uvicorn — port 8000
  worker:       # Celery — same image as backend, different command
  db:           # PostgreSQL 15 — port 5432
  redis:        # Redis 7 — port 6379
  minio:        # MinIO — API port 9000, console port 9001
  chromadb:     # ChromaDB server — port 8001
  nginx:        # Reverse proxy — port 80 (443 in production)
```

### Nginx Routing

```nginx
location /api/    { proxy_pass http://backend:8000; }
location /ws/     { proxy_pass http://backend:8000; proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection "upgrade"; }
location /        { proxy_pass http://frontend:3000; }
```

### Production Considerations

- Replace MinIO with Amazon S3 (`MINIO_ENDPOINT` → S3 endpoint).
- Switch `VECTOR_DB=qdrant` and deploy Qdrant with persistent volumes.
- Use a managed PostgreSQL instance (RDS, Neon, Supabase).
- Add Celery Flower for worker monitoring.
- Use `gunicorn -k uvicorn.workers.UvicornWorker` for multi-process backend.
- Put SSL termination at Nginx or a load balancer.

---

## 14. Configuration & Environment

All configuration is centralised in `backend/app/config.py` using `pydantic-settings`:

```python
class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str

    # Object Storage
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "eduvault-docs"

    # Redis
    REDIS_URL: str

    # Vector DB
    VECTOR_DB: Literal["chromadb", "qdrant", "pgvector"] = "chromadb"
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8001
    QDRANT_URL: str = "http://qdrant:6333"

    # Embeddings
    EMBEDDING_MODEL: Literal["all-MiniLM-L6-v2", "gemini"] = "all-MiniLM-L6-v2"

    # LLM
    LLM_PROVIDER: Literal["gemini", "groq"] = "gemini"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # RAG
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.35

    class Config:
        env_file = ".env"
```

---

## 15. Technology Decision Notes

### Why FastAPI over Django/Flask?
- Async-native: non-blocking DB queries and HTTP calls without extra configuration.
- Native WebSocket support.
- Automatic OpenAPI schema generation from type hints.

### Why Celery over FastAPI BackgroundTasks?
- `BackgroundTasks` runs in the same process; a large PDF could delay other requests.
- Celery runs in separate worker processes; supports retries, priorities, and monitoring.
- `BackgroundTasks` is an acceptable alternative for small deployments.

### Why all-MiniLM-L6-v2 as the default embedding model?
- Runs locally — no API cost per document chunk.
- 384-dimensional vectors — fast similarity search.
- Strong general-purpose performance; sufficient for institutional English text.

### Why keep ChromaDB/Qdrant/Pgvector as options rather than picking one?
- ChromaDB: zero-friction local development (no extra service).
- Qdrant: production-grade performance with metadata filtering for future cohort features.
- Pgvector: reduces operational complexity for teams already managing PostgreSQL.
- The `VectorStore` abstraction isolates backend choice to a single config value.

### Why Gemini 1.5 Flash over GPT-4?
- Long context window handles multiple retrieved chunks easily.
- Cost-efficient for high query volume in an institutional setting.
- Groq Llama-3.3-70B provided as an open-weight alternative with lower latency.