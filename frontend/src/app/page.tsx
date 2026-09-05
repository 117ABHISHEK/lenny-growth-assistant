"use client";
import React, { useEffect, useState } from "react";
import { ChatPane } from "@/components/Chat/ChatPane";
import { ArtifactViewer } from "@/components/Artifact/ArtifactViewer";
import { useChatStream } from "@/hooks/useChatStream";
import { createSession } from "@/lib/api";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { messages, sendMessage, isStreaming, artifacts } = useChatStream(sessionId);

  useEffect(() => {
    createSession("New Chat").then((s) => setSessionId(s.id));
  }, []);

  return (
    <main className="h-screen flex">
      <div className="w-1/2 border-r border-neutral-800">
        {sessionId ? (
          <ChatPane messages={messages} onSend={sendMessage} isStreaming={isStreaming} />
        ) : (
          <div className="flex items-center justify-center h-full text-neutral-500 text-sm">
            Starting session...
          </div>
        )}
      </div>
      <div className="w-1/2">
        <ArtifactViewer artifacts={artifacts} />
      </div>
    </main>
  );
}