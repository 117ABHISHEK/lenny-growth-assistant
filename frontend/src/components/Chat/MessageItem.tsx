"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/hooks/useChatStream";

function stripArtifactTags(text: string): string {
  // Handles properly closed artifact blocks
  let cleaned = text.replace(
    /<artifact type="(markdown|html)" title="([^"]*)">([\s\S]*?)<\/artifact>/g,
    "*[Artifact generated — see viewer on the right]*"
  );
  // Handles a dangling/unclosed opening tag if the model forgot to close it
  cleaned = cleaned.replace(/<artifact type="(markdown|html)" title="([^"]*)">/g, "");
  return cleaned;
}

export function MessageItem({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const displayContent = isUser ? message.content : stripArtifactTags(message.content);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
          isUser ? "bg-blue-600 text-white" : "bg-neutral-800 text-neutral-100"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent || "…"}</ReactMarkdown>
          </div>
        )}

        {message.warning && (
          <div className="mt-2 text-xs bg-amber-900/40 border border-amber-700 text-amber-300 rounded px-2 py-1">
            ⚠ {message.warning}
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-neutral-700">
            <p className="text-xs text-neutral-400 mb-1">Sources:</p>
            <ul className="text-xs text-neutral-400 space-y-0.5">
              {message.sources.map((s, i) => (
                <li key={i}>
                  {s.guest} — {s.episode} <span className="text-neutral-600">({s.score})</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}