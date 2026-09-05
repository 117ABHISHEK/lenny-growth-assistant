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