"use client";
import { GlassCard, StatusChip } from "@/components/ui";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

interface ProofData {
  artifact_id: string;
  title: string;
  summary: string;
  creator_wallet: string;
  proof_hash: string;
  raw_content_hash: string;
  redacted_content_hash: string;
  evidence_grade: number;
  appraisal: number;
  payment_status: string;
  funding_source: string;
  privacy_status: string;
  disclaimers: string[];
}

export default function ProofPage() {
  const { id } = useParams<{ id: string }>();
  const [proof, setProof] = useState<ProofData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    fetch(`http://localhost:8000/api/proof/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then((data) => setProof(data))
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gradient">Proof Capsule</h1>
        <GlassCard>
          <p className="text-danger text-sm">Error: {error}</p>
        </GlassCard>
      </div>
    );
  }

  if (!proof) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gradient">Proof Capsule</h1>
        <GlassCard>
          <p className="text-text-muted text-sm">Loading proof data...</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gradient">Proof Capsule</h1>
        <StatusChip status={proof.privacy_status === "approved_public" ? "active" : "locked"}>
          {proof.privacy_status}
        </StatusChip>
      </div>
      <GlassCard>
        <h2 className="font-semibold mb-2">{proof.title}</h2>
        <p className="text-sm text-text-muted mb-4">{proof.summary}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div><span className="text-text-muted">Artifact ID:</span> <span className="font-mono">{proof.artifact_id}</span></div>
          <div><span className="text-text-muted">Creator:</span> <span className="font-mono">{proof.creator_wallet}</span></div>
          <div><span className="text-text-muted">Proof Hash:</span> <span className="font-mono">{proof.proof_hash}</span></div>
          <div><span className="text-text-muted">Raw Hash:</span> <span className="font-mono">{proof.raw_content_hash}</span></div>
          <div><span className="text-text-muted">Redacted Hash:</span> <span className="font-mono">{proof.redacted_content_hash}</span></div>
          <div><span className="text-text-muted">Evidence Grade:</span> {proof.evidence_grade}</div>
          <div><span className="text-text-muted">Appraisal:</span> ${proof.appraisal}</div>
          <div><span className="text-text-muted">Payment:</span> {proof.payment_status}</div>
          <div><span className="text-text-muted">Funding:</span> {proof.funding_source}</div>
        </div>
      </GlassCard>
      <GlassCard>
        <h3 className="font-semibold text-sm mb-2">Disclaimers</h3>
        <ul className="list-disc list-inside text-xs text-text-muted space-y-1">
          {proof.disclaimers.map((d, i) => (<li key={i}>{d}</li>))}
        </ul>
      </GlassCard>
    </div>
  );
}
