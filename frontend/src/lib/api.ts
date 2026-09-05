const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createSession(title: string = "New Chat") {
  const res = await fetch(`${API_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${API_URL}/api/health`);
  return res.json();
}

export type ChatEvent =
  | { type: "sources"; content: { episode: string; guest: string; score: number }[] }
  | { type: "token"; content: string }
  | { type: "artifact"; content: { id: string; artifact_type: string; title: string; content: string }[] }
  | { type: "warning"; content: string };

export async function* streamChat(
  sessionId: string,
  message: string,
  mode: string,
  provider: string
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, mode, provider }),
  });

  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") return;
      try {
        yield JSON.parse(payload) as ChatEvent;
      } catch {
        // skip malformed chunk
      }
    }
  }
}