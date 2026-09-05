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
- **Ship 30 for 30 grounding limitation (confirmed via testing)** —
  llama3.2:3b consistently defaults to generic domain knowledge for
  longer-form generation (~1,250 words), even with explicit
  instructions to cite specific guest content and a hard requirement
  to reference 3+ distinct points from the transcript context. This
  held across three prompt-engineering iterations (banning invented
  examples, mandating guest citations). The grounded short-answer
  path (`/api/chat` default mode) does NOT show this problem —
  retrieval and citation work correctly there. The failure is
  specific to the Ship 30 skill's longer output length and
  multi-constraint instructions overwhelming a 3B parameter model.
  Mitigation: the Anthropic cloud provider is architecturally wired
  in via the same provider interface and should resolve this given
  a stronger model — not verified end-to-end in this submission due
  to no Anthropic API key being available during development, but
  the provider toggle and prompt are ready to use with one.
- **Local model fabrication risk in long-form generation (confirmed)** —
  llama3.2:3b reliably fabricates plausible-but-false citations
  (invented guest names, episodes, timestamps not present in the
  retrieved context) when generating longer documents or essays,
  even when explicitly instructed to cite only provided sources.
  This did NOT occur in the short-answer grounded QA path, where
  citation accuracy was correct and refusal behavior worked as
  designed. This is a meaningful, reproducible limitation of small
  local models for extended generation — not a retrieval or
  architecture failure, since the correct chunks were always
  retrieved and available in context. Production mitigation: route
  long-form/document-generation requests to a larger model (cloud
  provider) by default, reserving the local model for short grounded
  Q&A where it performs reliably.
- **Local model fabrication in long-form/document generation (confirmed, reproducible)** —
  llama3.2:3b reliably invents plausible-but-nonexistent guest names,
  episodes, and timestamps when generating documents or essays longer
  than a short Q&A answer — reproduced across 3 separate test runs
  (Ship 30 essay x2, markdown artifact x1), with different fabricated
  names each time (e.g. "Jason Cohen", "Dan Olsen", "Lenny Russell" —
  none present in the 30-episode corpus). This occurred even with
  explicit, repeated instructions to cite only provided context.
  Critically, the short-answer grounded QA path (`/api/chat` default
  mode) did NOT exhibit this problem in testing — retrieval, citation
  accuracy, and refusal-on-out-of-domain all worked correctly there.
  Root cause: a 3B-parameter model cannot reliably sustain grounding
  constraints over long, multi-paragraph generation once retrieved
  context is diluted across a larger output. This is a model-capacity
  limitation, not a retrieval or architecture failure — correct
  chunks were always retrieved and present in context.
  Production mitigation: this project routes short grounded Q&A to
  either provider, but restricts long-form generation (Ship 30 essays,
  markdown/HTML artifacts) to the cloud provider (Anthropic) in
  production; local-only operation should be scoped to short-answer
  QA. Not verified end-to-end with Anthropic due to no API key being
  available during development — the provider interface and prompts
  are ready to test with one.
- **Artifact tag closure reliability** — llama3.2:3b does not always
  close the `</artifact>` tag, causing the artifact extraction to
  miss the content (frontend now strips a dangling open tag as a
  fallback so raw markup never leaks into the chat view; the
  content simply won't populate the artifact viewer in that case).
  A stronger model (Anthropic) or a stricter generation grammar
  would resolve this fully.