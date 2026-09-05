"use client";
import React from "react";

export function ModelSelector({
  provider,
  setProvider,
  mode,
  setMode,
}: {
  provider: string;
  setProvider: (p: string) => void;
  mode: string;
  setMode: (m: string) => void;
}) {
  return (
    <div className="flex gap-2 items-center text-xs">
      <select
        value={provider}
        onChange={(e) => setProvider(e.target.value)}
        className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-neutral-200"
      >
        <option value="ollama">Ollama (local)</option>
        <option value="anthropic">Anthropic (cloud)</option>
      </select>
      <select
        value={mode}
        onChange={(e) => setMode(e.target.value)}
        className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-neutral-200"
      >
        <option value="default">Grounded Q&A</option>
        <option value="ship30">Ship 30 for 30</option>
      </select>
    </div>
  );
}