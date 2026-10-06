# EduVault — Deployment Guide (Vercel & Render)

This guide walks you through deploying **EduVault** with:
- **Frontend (Next.js 14)** deployed on **Vercel**
- **Backend (FastAPI + ChromaDB + PostgreSQL)** deployed on **Render**

---

## Architecture at a Glance

```
┌─────────────────────────────────┐           ┌───────────────────────────────────┐
│     Vercel (Frontend)           │           │        Render (Backend)           │
│   Next.js 14 App Router         │  HTTPS/WS │   FastAPI Web Service             │
│   https://eduvault.vercel.app   ├───────────►   https://eduvault-api.onrender.com│
└─────────────────────────────────┘           └──────────────┬────────────────────┘
                                                             │
                                              ┌──────────────▼────────────────────┐
                                              │    Render Managed PostgreSQL      │
                                              │    ChromaDB Vector Store          │
                                              └───────────────────────────────────┘
```

---

## Part 1: Deploy Backend on Render

Render hosts the FastAPI API, WebSockets streaming server, and managed PostgreSQL database.

### Option A: 1-Click Blueprint (Recommended)

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository (`EduVault`).
4. Render will automatically detect [`render.yaml`](./render.yaml).
5. It will provision:
   - **`eduvault-backend`**: Python Web Service
   - **`eduvault-db`**: Managed PostgreSQL Database
6. Enter the missing secret environment variables when prompted:
   - `GEMINI_API_KEY` (or `GROQ_API_KEY`)
7. Click **Apply**.
8. Once deployment finishes, copy your Render service URL (e.g. `https://eduvault-backend.onrender.com`).

---

### Option B: Manual Service Creation on Render

If you prefer manual configuration without Blueprints:

#### 1. Create PostgreSQL Database
1. Go to **New +** &rarr; **PostgreSQL**.
2. Name: `eduvault-db`
3. Database: `eduvault`
4. User: `eduvault`
5. Plan: **Free** (or Starter)
6. Once provisioned, copy the **Internal Database URL** (or External URL).

#### 2. Create FastAPI Web Service
1. Go to **New +** &rarr; **Web Service**.
2. Connect your repository.
3. Configure the service settings:
   - **Name**: `eduvault-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add the following **Environment Variables**:

| Variable | Value / Description |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | *(Generate a 32+ character random string)* |
| `DATABASE_URL` | *(Paste your Render PostgreSQL connection string)* |
| `CORS_ORIGINS` | `https://*.vercel.app,http://localhost:3000` |
| `LLM_PROVIDER` | `gemini` *(or `groq`)* |
| `GEMINI_API_KEY` | *(Your Google Gemini API Key)* |
| `GROQ_API_KEY` | *(Your Groq API Key, if using Groq)* |
| `VECTOR_DB` | `chromadb` |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_data` |
| `RETRIEVAL_TOP_K` | `4` |
| `SIMILARITY_THRESHOLD` | `0.35` |

5. Click **Create Web Service**.
6. When deployment completes, note your backend URL (e.g. `https://eduvault-backend.onrender.com`). Verify it by opening `https://eduvault-backend.onrender.com/health`.

---

## Part 2: Deploy Frontend on Vercel

Vercel natively optimizes Next.js App Router applications with edge routing and automatic asset optimization.

### Step 1: Import Project to Vercel
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** &rarr; **Project**.
3. Select your `EduVault` repository from GitHub.

### Step 2: Configure Build & Root Directory
1. In the **Configure Project** screen:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click **Edit** and select `frontend`.
2. Leave Build Command and Output Directory as default (Vercel automatically detects them via Next.js).

### Step 3: Add Environment Variables
Expand the **Environment Variables** section and add:

| Name | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://eduvault-backend.onrender.com` | Your Render backend URL (no trailing slash) |

> [!NOTE]
> The WebSocket client automatically derives `wss://eduvault-backend.onrender.com` from `NEXT_PUBLIC_API_URL`.

### Step 4: Deploy
1. Click **Deploy**.
2. Vercel will run `npm run build` and output the production build.
3. Once deployed, you will receive your live URL (e.g. `https://eduvault-frontend.vercel.app`).

---

## Part 3: Verify the Deployment

### 1. Default Admin Credentials
The backend automatically seeds a default administrator on initial database startup:
- **Email**: `admin@eduvault.edu`
- **Password**: `Admin@123`

### 2. Verification Checklist
- [ ] Visit `https://your-frontend.vercel.app` &rarr; Landing page loads cleanly with dark palette and solid surfaces.
- [ ] Click **Sign In** and log in with `admin@eduvault.edu` / `Admin@123`.
- [ ] Navigate to **Admin &rarr; Documents** &rarr; Upload a university PDF, Word, or CSV document.
- [ ] Confirm the document parses into chunks and its status transitions to `indexed`.
- [ ] Navigate to **Chat** &rarr; Ask questions about the uploaded document.
- [ ] Check that answers stream in real time over WebSockets and render verified citations `[DocName · Page X]`.
- [ ] Ask a completely unrelated query &rarr; Verify the anti-hallucination guardrail triggers: *"Information not found in the institutional knowledge base."*

---

## Troubleshooting

### CORS Errors
- If you see `Cross-Origin Request Blocked`, make sure `CORS_ORIGINS` in your Render backend settings includes your exact Vercel domain (e.g. `https://your-project.vercel.app`). The backend also supports wildcard subdomains via `allow_origin_regex=r"https://.*\.vercel\.app"`.

### Database Connection on Render
- Render provides connection strings starting with `postgres://`. The backend automatically converts this to `postgresql+asyncpg://` to support asynchronous SQLAlchemy and AsyncPG.

### WebSockets on Render
- WebSockets work out of the box on Render with standard HTTPS (`wss://`). Ensure your frontend variable `NEXT_PUBLIC_API_URL` uses `https://` (not `http://`).
