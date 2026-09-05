import { useState, useCallback } from "react";
import { streamChat, ChatEvent } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: { episode: string; guest: string; score: number }[];
  warning?: string;
}

export interface ArtifactData {
  id: string;
  artifact_type: string;
  title: string;
  content: string;
}

export function useChatStream(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [artifacts, setArtifacts] = useState<ArtifactData[]>([]);

  const sendMessage = useCallback(
    async (text: string, mode: string, provider: string) => {
      if (!sessionId || !text.trim()) return;

      const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
      const assistantId = crypto.randomUUID();
      setMessages((prev) => [...prev, userMsg, { id: assistantId, role: "assistant", content: "" }]);
      setIsStreaming(true);

      try {
        for await (const event of streamChat(sessionId, text, mode, provider) as AsyncGenerator<ChatEvent>) {
          if (event.type === "token") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + event.content } : m))
            );
          } else if (event.type === "sources") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, sources: event.content } : m))
            );
          } else if (event.type === "artifact") {
            setArtifacts((prev) => [...prev, ...event.content]);
          } else if (event.type === "warning") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, warning: event.content } : m))
            );
          }
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content + "\n\n[Error: connection lost]" } : m
          )
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId]
  );

  return { messages, sendMessage, isStreaming, artifacts };
}