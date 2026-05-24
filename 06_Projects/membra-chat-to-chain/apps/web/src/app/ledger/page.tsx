"use client";
import { GlassCard, MetricCard } from "@/components/ui";
import { useEffect, useState } from "react";

interface LedgerEntry {
  action: string;
  artifact_id?: string;
  status?: string;
  ts: string;
}

export default function LedgerPage() {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [count, setCount] = useState(0);

  useEffect(() => {
    fetch("http://localhost:8000/api/ledger")
      .then((r) => r.json())
      .then((data) => {
        setEntries(data.ledger || []);
        setCount(data.count || 0);
      })
      .catch(() => {
        setEntries([]);
        setCount(0);
      });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gradient">Ledger</h1>
      <MetricCard label="Total Entries" value={String(count)} />
      <div className="space-y-2">
        {entries.length === 0 && (
          <GlassCard>
            <p className="text-sm text-text-muted">No ledger entries yet. Create an artifact to see activity.</p>
          </GlassCard>
        )}
        {entries.map((e, i) => (
          <GlassCard key={i} className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{e.action}</p>
              {e.artifact_id && <p className="text-xs text-text-muted">{e.artifact_id}</p>}
            </div>
            <div className="text-right">
              {e.status && <span className="text-xs text-primary-orange">{e.status}</span>}
              <p className="text-xs text-text-muted">{e.ts}</p>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}
