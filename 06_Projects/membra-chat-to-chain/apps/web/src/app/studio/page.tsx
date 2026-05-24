"use client";
import { GlassCard, StatusChip, TerminalPanel } from "@/components/ui";
import { useState } from "react";

export default function StudioPage() {
  const [artifactType, setArtifactType] = useState("chat");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gradient">Studio</h1>
        <StatusChip status="active">Session Active</StatusChip>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button onClick={() => setArtifactType("chat")} className={`p-4 rounded-lg border text-left transition-colors ${artifactType === "chat" ? "border-primary-orange/50 bg-primary-orange/5" : "border-white/5 bg-background-100"}`}>
          <p className="font-semibold text-sm">Chat Artifact</p>
          <p className="text-xs text-text-muted mt-1">Prompt + response pair</p>
        </button>
        <button onClick={() => setArtifactType("build")} className={`p-4 rounded-lg border text-left transition-colors ${artifactType === "build" ? "border-primary-orange/50 bg-primary-orange/5" : "border-white/5 bg-background-100"}`}>
          <p className="font-semibold text-sm">Build Epoch</p>
          <p className="text-xs text-text-muted mt-1">Files + tests + output</p>
        </button>
        <button onClick={() => setArtifactType("image")} className={`p-4 rounded-lg border text-left transition-colors ${artifactType === "image" ? "border-primary-orange/50 bg-primary-orange/5" : "border-white/5 bg-background-100"}`}>
          <p className="font-semibold text-sm">Visual Asset</p>
          <p className="text-xs text-text-muted mt-1">Image hash + metadata</p>
        </button>
      </div>
      <GlassCard>
        <h2 className="font-semibold mb-4">Create Artifact</h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-text-muted block mb-1">Title</label>
            <input className="w-full bg-background border border-white/10 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary-orange/50" placeholder="Artifact title" />
          </div>
          <div>
            <label className="text-xs text-text-muted block mb-1">Content</label>
            <textarea className="w-full bg-background border border-white/10 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary-orange/50 min-h-[120px]" placeholder="Enter content..." />
          </div>
          <button className="bg-primary-orange text-background font-medium px-4 py-2 rounded-md text-sm hover:bg-primary-orange/90 transition-colors">
            Stage Artifact
          </button>
        </div>
      </GlassCard>
      <TerminalPanel lines={[{ type: "prompt", text: "membra-studio --type=" + artifactType }, { type: "output", text: "Ready to stage artifact. Awaiting input." }]} />
    </div>
  );
}
