"use client";
import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SandboxedIframe } from "./SandboxedIframe";
import type { ArtifactData } from "@/hooks/useChatStream";

export function ArtifactViewer({ artifacts }: { artifacts: ArtifactData[] }) {
  const [activeIndex, setActiveIndex] = useState(0);

  if (artifacts.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-neutral-500 text-sm p-6 text-center">
        Generated documents and HTML snippets will appear here.
        <br />
        Try: &quot;Create a markdown summary of April Dunford&apos;s positioning framework&quot;
      </div>
    );
  }

  const active = artifacts[activeIndex];

  return (
    <div className="flex flex-col h-full">
      {artifacts.length > 1 && (
        <div className="flex gap-1 p-2 border-b border-neutral-800 overflow-x-auto">
          {artifacts.map((a, i) => (
            <button
              key={a.id}
              onClick={() => setActiveIndex(i)}
              className={`text-xs px-3 py-1 rounded whitespace-nowrap ${
                i === activeIndex ? "bg-neutral-700 text-white" : "bg-neutral-800 text-neutral-400"
              }`}
            >
              {a.title}
            </button>
          ))}
        </div>
      )}
      <div className="flex-1 overflow-auto p-4">
        {active.artifact_type === "html" ? (
          <SandboxedIframe content={active.content} title={active.title} />
        ) : (
          <div className="bg-white text-black rounded-lg p-6 prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{active.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}