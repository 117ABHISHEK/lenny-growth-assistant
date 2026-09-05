"use client";
import React, { useState, useRef, useEffect } from "react";
import { MessageItem } from "./MessageItem";
import { ModelSelector } from "./ModelSelector";
import type { ChatMessage } from "@/hooks/useChatStream";

export function ChatPane({
  messages,
  onSend,
  isStreaming,
}: {
  messages: ChatMessage[];
  onSend: (text: string, mode: string, provider: string) => void;
  isStreaming: boolean;
}) {
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState("ollama");
  const [mode, setMode] = useState("default");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSend(input, mode, provider);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-neutral-800 flex items-center justify-between">
        <h1 className="text-sm font-semibold">Lenny Growth Assistant</h1>
        <ModelSelector provider={provider} setProvider={setProvider} mode={mode} setMode={setMode} />
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-neutral-500 text-sm text-center mt-8">
            Ask a product or growth question grounded in Lenny&apos;s Podcast transcripts.
          </div>
        )}
        {messages.map((m) => (
          <MessageItem key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-3 border-t border-neutral-800 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about product growth, positioning, onboarding..."
          className="flex-1 bg-neutral-800 border border-neutral-700 rounded px-3 py-2 text-sm text-neutral-100 placeholder-neutral-500"
          disabled={isStreaming}
        />
        <button
          type="submit"
          disabled={isStreaming}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded"
        >
          {isStreaming ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}