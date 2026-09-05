# The Lenny Growth Assistant

A full-stack, retrieval-augmented generation (RAG) web application that answers product management and growth questions grounded in Lenny's Podcast transcripts, generates Ship 30 for 30-style essays, and produces sandboxed Markdown/HTML artifacts — built for the OOGWAY Forward Deployed Engineer take-home assignment.

## Architecture Overview

- **Backend**: FastAPI (Python 3.11), async SQLAlchemy, PostgreSQL + pgvector for vector search
- **Frontend**: Next.js 14 (App Router, TypeScript), Tailwind CSS, react-markdown, DOMPurify
- **LLM Layer**: Dual-provider — Ollama (local, `llama3.2:3b`) and Anthropic Claude (cloud), switchable per-request
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (local, no API dependency)
- **Deployment**: Docker Compose (db + backend + frontend), verified working end-to-end locally

See `docs/architecture.md` for full technical detail and `docs/design.md` for UI/UX decisions.

## Prerequisites

- Docker Desktop (with Docker Compose v2)
- [Ollama](https://ollama.com) installed locally, with `llama3.2:3b` pulled:
`
ollama pull llama3.2:3b
`

- (Optional) An Anthropic API key, to use the cloud provider

> **Note on local model requirement**: The mandatory local-model demo path requires Ollama running on the host machine. Ollama is not run inside Docker in this setup — the `backend` container reaches it via `host.docker.internal`, so Ollama must be running on your host before starting the stack.

## Setup & Run (one command)

```bash
git clone <this-repo>
cd lenny-growth-assistant
cp .env.example .env
# (optional) add ANTHROPIC_API_KEY to .env if you have one
ollama serve          # if not already running
ollama pull llama3.2:3b

docker-compose up --build
```

Then:
1. Ingest the curated transcript subset (first run only):
```bash
   docker-compose exec backend python scripts/ingest.py
```
2. Open the app: **http://localhost:3000**
3. Check backend health directly: **http://localhost:8000/api/health**

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Enables the cloud provider | empty (Ollama-only if unset) |
| `OLLAMA_BASE_URL` | Where the backend reaches Ollama | `http://host.docker.internal:11434` (in Docker) |
| `OLLAMA_MODEL` | Local model name | `llama3.2:3b` |
| `DEFAULT_LLM_PROVIDER` | Fallback provider if none specified | `ollama` |
| `DATABASE_URL` | Postgres connection string | set automatically by Compose |

No secrets are committed. `.env` is gitignored.

## Data Source & Ingestion

Transcripts are sourced from the public [ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) repository. A curated subset of 30 episodes (growth/PMF/onboarding cluster — e.g. April Dunford, Bob Moesta, Ben Horowitz, Annie Duke) is used rather than the full 303-episode archive; see `docs/PRD.md` §3 (Assumptions) for the rationale.

`backend/scripts/download_transcripts.py` copies the curated subset from a full clone of the source repo into `backend/data/transcripts/`. `backend/scripts/ingest.py` chunks (700 words, 100-word overlap), embeds, and loads them into Postgres/pgvector with an HNSW index.

To re-run ingestion from scratch:
```bash
docker-compose exec backend python scripts/ingest.py
```

## Local Development (without Docker, for faster iteration)

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
docker-compose up -d db            # just the database
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Running Tests

```bash
docker-compose exec backend pytest
```
or locally:
```bash
cd backend
pytest
```

## API Overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | DB, Ollama, and vector index status |
| `/api/sessions` | POST | Create a new chat session |
| `/api/sessions/{id}` | GET | Fetch message history |
| `/api/chat` | POST | Streaming grounded chat (SSE); `mode`: `default` \| `ship30`; `provider`: `ollama` \| `anthropic` |

Full request/response contracts in `docs/architecture.md`.

## Known Limitations (see `docs/PRD.md` for full detail)

1. **Local model fabrication in long-form generation** — `llama3.2:3b` can invent plausible-but-false guest citations in Ship 30 essays and markdown artifacts. Not observed in the short-answer grounded Q&A path. Mitigated by an unverified-citation guardrail (logs + UI warning) and documented as a production recommendation to route long-form generation to the cloud provider.
2. **Artifact tag closure reliability** — the local model doesn't always close the `<artifact>` tag; frontend strips dangling tags as a fallback so raw markup never leaks to the user, but the artifact panel simply won't populate in that case.
3. **No Anthropic API key was available during development** — the cloud-provider code path is implemented and wired through the same provider interface, but not verified end-to-end. Untested, not unimplemented.
4. **Live deployment** — Dockerfiles are production-ready and deployable to Render/Vercel/similar, but full functionality (local Ollama) cannot run on typical PaaS free tiers. A hosted deployment would need to default to the Anthropic provider.

## Project Structure
```
lenny-growth-assistant/
├── docker-compose.yml
├── .env.example
├── docs/ # PRD, architecture, design
├── agent_transcripts/ # AI-assisted build session logs
├── backend/ # FastAPI + RAG + providers
└── frontend/ # Next.js chat UI + artifact viewer
```


## Troubleshooting

- **`asyncpg.exceptions.InvalidPasswordError`** — usually means `.env` isn't being read from the current working directory; ensure a copy exists at `backend/.env` when running outside Docker.
- **Port 5432 conflict** — if you have a native Postgres installation, this project maps the DB container to host port `5433` instead; Docker-internal traffic still uses `5432`.
- **Ollama unreachable from container** — confirm `ollama serve` is running on the host and reachable at `http://localhost:11434` before starting Docker Compose.