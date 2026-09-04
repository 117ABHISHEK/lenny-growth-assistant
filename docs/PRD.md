# Product Requirements Document — The Lenny Growth Assistant

## 1. User & Problem

**Primary user:** A Growth PM or product leader who wants tactical,
proven advice from world-class operators without listening to 200+
hours of podcast audio.

**Job to be done:** Ask a specific product/growth question and get
a grounded, source-cited answer in under a minute — with the option
to turn that answer into a polished, shareable write-up.

**Pain removed:** Manually searching/skimming podcast transcripts
for relevant advice, and the risk of generic (non-cited, possibly
hallucinated) AI answers that can't be trusted or verified.

## 2. Success Metric

**Primary metric:** Retrieval Citation Accuracy ≥ 90% — every
factual claim in a grounded answer traces back to a retrieved
transcript chunk with a valid [Episode: Guest, Timestamp/Topic]
citation, verified against a manual test set of 15-20 sample
questions.

**Secondary metric (operational):** Local inference latency
< 4s to first token on Ollama (llama3.2:3b), verified manually
during the demo.

## 3. Assumptions

- Using a curated ~30-episode subset of the 303-episode transcript
  archive (topic-clustered around growth, PMF, and onboarding —
  e.g. episodes featuring guests like Annie Duke, April Dunford,
  Ben Horowitz, Bob Moesta), not the full corpus — a deliberate
  scope cut for the evaluation window, not a data limitation.
- Embeddings generated locally via `sentence-transformers/all-MiniLM-L6-v2`
  — no external embedding API dependency, keeps ingestion
  reproducible offline.
- Single cloud provider integrated: Anthropic Claude. OpenAI support
  omitted as redundant for evaluation purposes.
- No authentication/authorization layer — single-tenant local/demo
  deployment, as the brief specifies an internal evaluator tool.
- Transcript refresh is a one-time manual ingest, not a scheduled
  job — acceptable for a static demo archive.

## 4. Scope Choices

**In scope:**
- Grounded RAG chat over the curated transcript subset, with
  citations and an explicit "insufficient information" fallback.
- Ship 30 for 30 content-generation skill as a distinct tool.
- Markdown/HTML artifact generation with a sandboxed in-app viewer.
- Dual LLM provider toggle (Ollama local / Anthropic cloud).
- Docker Compose one-command startup.
- Core automated tests (retrieval, provider switching, refusal
  behavior) plus a manual UI test plan.

**Out of scope (and why):**
- Multi-user authentication — not needed for a single evaluator
  demo session.
- Full 303-episode ingestion — time-boxed; a topic-clustered
  subset demonstrates the same retrieval/grounding behavior.
- OpenAI provider — Anthropic alone satisfies the "at least one
  cloud provider" requirement; adding a second provider doesn't
  change the architecture story.
- Scheduled/automatic transcript refresh — a one-time ingest
  script is sufficient for a static demo dataset.
- Fine-grained access control on sessions — sessions are
  identified by ID only, no ownership model.

## 5. Risks & Trade-offs

- **Hallucination risk** — mitigated by a similarity-score
  threshold on retrieval and an explicit refusal prompt
  ("I do not have sufficient information in Lenny's podcast
  archive to answer this") when no chunk clears the bar.
- **Local model reasoning limits** — llama3.2:3b trades reasoning
  depth for demo responsiveness; this is precisely why the
  dual-provider toggle exists, so the evaluator can compare
  local vs. cloud output on the same question.
- **Unsafe artifact rendering (XSS)** — generated HTML is treated
  as untrusted: rendered in a sandboxed iframe with
  `sandbox="allow-scripts"` and no `allow-same-origin`, plus
  DOMPurify sanitization before injection.
- **Latency vs. quality trade-off** — smaller local models respond
  faster but may need more retrieved context to stay grounded;
  cloud fallback is available when quality matters more than cost.
- **Cost** — cloud provider calls are opt-in per session, not
  default, to keep the required local-demo path free to run.