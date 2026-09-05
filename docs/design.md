# Design

## UI/UX Principles

- **Two-pane layout, Claude Artifacts-inspired**: chat on the left, generated documents/HTML on the right. The split keeps the conversational flow separate from reusable output, so a generated artifact doesn't get lost in scrollback.
- **Streaming-first**: tokens render as they arrive (SSE) rather than waiting for the full response — matches user expectations set by modern LLM chat products and gives immediate feedback that the system is working, especially important given local-model latency.
- **Transparency over polish**: citations and similarity scores are shown plainly under each answer rather than hidden — a PM evaluating grounding quality needs to see the evidence, not just trust the prose.
- **Guardrail visibility**: the unverified-citation warning surfaces directly in the chat UI (amber banner), not just in server logs — a user-facing safety signal, not just a developer one.

## Information Architecture

**Layout: two-pane split**

- **Left pane (chat)**
  - Header: app title + provider selector + mode selector
  - Message history (user messages right-aligned, assistant messages left-aligned, with sources and warnings shown inline under each assistant message)
  - Input box + Send button at the bottom

- **Right pane (artifact viewer)**
  - Tabs across the top if multiple artifacts exist in the session
  - Markdown artifacts render as formatted text
  - HTML artifacts render inside a sandboxed iframe

## Key Interaction States

- **Session initializing**: "Starting session..." placeholder while `POST /api/sessions` resolves — prevents sending a message before a session ID exists.
- **Empty chat**: prompts the user toward the kind of question the assistant answers well ("Ask a product or growth question grounded in Lenny's Podcast transcripts").
- **Empty artifact panel**: gives a concrete example prompt to try, rather than a blank space — reduces the discovery gap for a feature the user might not know to ask for.
- **Streaming**: Send button disables and shows "..." during an active response, preventing duplicate concurrent requests.
- **Citation warning**: rendered as a distinct amber-bordered banner within the assistant's message bubble, visually separated from both the answer text and the source list.

## Responsive Behavior

The two-pane layout is built with Tailwind's flex utilities (`w-1/2` per pane); at narrower viewports this degrades to stacked panes rather than a hard breakpoint redesign, given time constraints — documented here as a known simplification rather than left silent. Production hardening would add a `md:` breakpoint to stack panes vertically on mobile and add a toggle to switch between chat/artifact views.

## Accessibility Considerations

- Semantic HTML elements (`<form>`, `<button>`, `<select>`) used throughout rather than div-based fake controls, preserving native keyboard and screen-reader behavior.
- Color is not the sole signal for the citation warning — it's also prefixed with a ⚠ symbol and explicit text.
- **Not yet addressed** (documented, not hidden): focus management on new messages, ARIA live regions for streamed content, and color contrast audit — reasonable next steps beyond this assignment's time box.

## Design Decisions Worth Noting

- **No artifact auto-detection heuristics** — the system relies on explicit `<artifact>` tags from the LLM rather than trying to infer "this looks like a document" from response length/structure. Simpler and more predictable, at the cost of the local model sometimes not using the tag reliably (documented limitation).
- **Sources shown per-message, not globally** — since sessions can span multiple grounded queries, attaching citations to the specific message they support (rather than a running sidebar) keeps evidence traceable to the exact claim.