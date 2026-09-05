# Architecture

## Grounding & Citation Strategy

Citation attribution is enforced structurally via a separate `sources`
payload (episode, guest, similarity score) accompanying every response,
rather than relying on the LLM to embed correctly-formatted inline
citations. This guarantees citation accuracy regardless of model
compliance, and is more robust for small local models (e.g.
llama3.2:3b) that may not reliably follow strict formatting
instructions embedded in a system prompt.

The `/api/chat` endpoint streams two event types over SSE:
- `sources` — sent first, containing the retrieved transcript chunks
  (episode title, guest name, cosine similarity score) that were used
  to ground the answer.
- `token` — the model's streamed response text.

The frontend renders `sources` as a distinct citations panel next to
the answer, decoupled from whatever citation format (if any) the
model produces in its prose.

# Architecture

## System Overview

**Request flow:**
1. **Next.js Frontend** sends a chat request to the **FastAPI Backend** and receives a streamed (SSE) response.
2. The **Backend** queries **PostgreSQL + pgvector** for relevant transcript chunks.
3. The **Backend** sends the grounded prompt to either **Ollama (local)** or **Anthropic (cloud)**, based on the request's `provider` field.
4. The model's streamed response, source citations, and any generated artifacts are sent back to the frontend over the same SSE connection.

```
Next.js Frontend  <--SSE-->  FastAPI Backend  -->  PostgreSQL + pgvector
                                    |
                        +-----------+-----------+
                        |                       |
                  Ollama (local)         Anthropic (cloud)
```

## Database Schema

- **sessions**: `id` (UUID, PK), `title`, `created_at`, `updated_at`
- **messages**: `id` (UUID, PK), `session_id` (FK), `role` (`user`|`assistant`), `content`, `sources` (JSONB), `created_at`
- **artifacts**: `id` (UUID, PK), `message_id` (FK), `artifact_type` (`markdown`|`html`), `title`, `content`, `created_at`
- **transcript_chunks**: `id` (serial, PK), `episode_title`, `guest_name`, `chunk_text`, `timestamp_ref`, `embedding` (vector(384), HNSW-indexed, cosine distance)

## API Endpoints

| Endpoint | Method | Request | Response |
|---|---|---|---|
| `/api/health` | GET | — | `{status, database, ollama, vector_index}` |
| `/api/sessions` | POST | `{title}` | `{id, title, created_at}` |
| `/api/sessions/{id}` | GET | — | `[{id, role, content, sources, created_at}, ...]` |
| `/api/chat` | POST | `{session_id, message, mode, provider}` | SSE stream: `sources` then `token` (repeated), then optional `artifact`, then optional `warning`, then `[DONE]` |

## Ingestion & Retrieval Flow

1. `download_transcripts.py` copies a curated 30-episode subset from a cloned source repo into `backend/data/transcripts/`.
2. `ingest.py` parses each transcript's YAML frontmatter (guest, title) and body, chunks the body (700 words, 100-word overlap via word-count splitting), embeds each chunk with MiniLM, and inserts into `transcript_chunks` with an HNSW cosine-similarity index.
3. At query time, `TranscriptRetriever.retrieve_relevant_chunks()` embeds the user's query and runs a pgvector cosine-similarity search, filtered by a similarity threshold (0.35, tuned empirically since MiniLM cosine scores on this corpus run lower than a naive 0.65 threshold would allow) and capped at `top_k` (5 for Q&A, 8 for Ship 30 essays, since longer content benefits from more context).

## Agent Routing / Model Toggle

`LLMProviderInterface` (abstract base, `providers/base.py`) is implemented by `OllamaProvider` and `AnthropicProvider`, both exposing `generate_response()` (async streaming) and `is_available()` (health check). The active provider is selected per-request via the `provider` field in the `/api/chat` request body — no restart or config change needed to switch. `get_provider()` in `chat.py` is the single point of provider instantiation, keeping the rest of the codebase provider-agnostic.

## Grounding & Citation Strategy

Citation attribution is enforced structurally via a separate `sources` SSE event (episode, guest, similarity score) accompanying every response, rather than relying on the LLM to embed correctly-formatted inline citations. This guarantees citation accuracy regardless of model compliance, and is more robust for small local models (e.g. llama3.2:3b) that may not reliably follow strict formatting instructions embedded in a system prompt. Testing confirmed accurate, well-scored citations and correct refusal-on-out-of-domain behavior in this path.

For longer-form generation (Ship 30 essays, artifacts), testing surfaced a real limitation: llama3.2:3b can fabricate plausible-but-nonexistent guest names and timestamps despite explicit grounding instructions. A post-generation guardrail (`flag_unverified_citations()`) checks any `[Episode: Guest, ...]`-style citations in the raw output against the known 30-guest corpus and logs/surfaces a warning (via a `warning` SSE event) when a citation can't be verified — a defense-in-depth measure rather than a fix for the underlying model limitation. See `docs/PRD.md` Risks section for full detail and reproduction evidence.

## Artifact Generation & Security Model

The LLM is instructed (via a prompt suffix) to wrap document-style output in `<artifact type="markdown|html" title="...">...</artifact>` tags. The backend extracts these via regex (`extract_artifacts()`) after the full response streams, persists them as `Artifact` rows linked to the message, and emits their content as a separate `artifact` SSE event. The chat-bubble text has the tag stripped (both server-side for persistence and client-side as a rendering fallback for any dangling/unclosed tags).

**HTML artifacts are treated as untrusted.** The frontend renders them inside a sandboxed iframe using `srcDoc`, with `sandbox="allow-scripts"` and no `allow-same-origin` — this permits the artifact's own JavaScript to run for interactivity, but blocks it from accessing the parent page's cookies, localStorage, or DOM. Content additionally passes through DOMPurify before being injected. Markdown artifacts are rendered via react-markdown with remark-gfm, which does not execute arbitrary HTML by default.

**What this permits**: self-contained interactive HTML/CSS/JS demos.
**What this blocks**: artifact code reading/writing parent-page cookies or storage, navigating the parent frame, or accessing anything outside its own sandboxed context.

## Deployment Topology

Three Docker Compose services:
- `db` — pgvector/pgvector:pg16, exposed on host port 5433 (to avoid conflicting with any native Postgres installation on 5432; container-to-container traffic uses the default 5432 internally)
- `backend` — built from `backend/Dockerfile` (Python 3.11-slim), reaches host-installed Ollama via `host.docker.internal` (Docker's mechanism for containers to reach host-network services)
- `frontend` — multi-stage build (node:20-alpine), builds a production Next.js bundle and serves it with `next start`

All three verified running and healthy together via `docker-compose up --build`, with the frontend successfully completing full round-trip chat, retrieval, and artifact generation through the containerized stack.

**Cloud deployment note**: the Dockerfiles are portable and would deploy to Render/Fly.io/similar as-is. The blocker for a fully-functional hosted deployment is Ollama — it requires a persistent local process, which typical PaaS free tiers don't support well. A hosted deployment would need to default to the Anthropic provider and treat Ollama as local-development-only.

## Resilience

- **Missing Anthropic key**: `AnthropicProvider.generate_response()` yields an inline error message instead of raising.
- **Ollama unreachable**: `OllamaProvider.generate_response()` catches `httpx.ConnectError` and yields a descriptive error instead of crashing the request.
- **Empty retrieval**: the grounded system prompt instructs an explicit refusal string; verified working in testing.
- **Global exception handler**: `main.py` registers a FastAPI exception handler that logs and returns a structured 500 instead of an unhandled stack trace.