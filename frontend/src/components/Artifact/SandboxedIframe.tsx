"use client";
import React, { useMemo } from "react";
import DOMPurify from "dompurify";

export function SandboxedIframe({ content, title }: { content: string; title: string }) {
  const cleanHtml = useMemo(() => {
    return DOMPurify.sanitize(content, {
      WHOLE_DOCUMENT: true,
      ADD_TAGS: ["style"],
      ADD_ATTR: ["target"],
    });
  }, [content]);

  return (
    <div className="flex flex-col h-full border border-neutral-700 rounded-lg overflow-hidden bg-white">
      <div className="bg-neutral-100 border-b border-neutral-300 px-4 py-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-neutral-700 uppercase tracking-wide">
          Artifact: {title}
        </span>
        <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          Sandboxed Preview
        </span>
      </div>
      <iframe
        title={title}
        srcDoc={cleanHtml}
        sandbox="allow-scripts"
        className="w-full h-full border-none flex-1"
      />
    </div>
  );
}