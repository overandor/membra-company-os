'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

function fmtBytes(b: number) {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1073741824) return `${(b / 1048576).toFixed(1)} MB`;
  return `${(b / 1073741824).toFixed(2)} GB`;
}

function fmtTokens(n: number) {
  if (n < 1000) return String(n);
  if (n < 1e6) return `${(n / 1000).toFixed(1)}K`;
  return `${(n / 1e6).toFixed(2)}M`;
}

function Dot({ ok }: { ok: boolean }) {
  return <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: ok ? '#22c55e' : '#ef4444', marginRight: 6 }} />;
}

export default function OverLLMDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggeringTraining, setTriggeringTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<string | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/overllm/kpis');
      const data = await res.json();
      if (data.success) { setStats(data.stats); setError(null); }
      else setError(data.error || 'Unknown error');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Fetch failed');
    }
    setLoading(false);
    setRefreshCount(c => c + 1);
  }, []);

  useEffect(() => {
    fetchStats();
    const iv = setInterval(fetchStats, 60000);
    return () => clearInterval(iv);
  }, [fetchStats]);

  async function handleTriggerTraining() {
    setTriggeringTraining(true);
    setTrainResult(null);
    try {
      const res = await fetch('/api/overllm/training', { method: 'POST' });
      const data = await res.json();
      setTrainResult(data.message || data.error || JSON.stringify(data));
      fetchStats();
    } catch (e) {
      setTrainResult(e instanceof Error ? e.message : 'Failed');
    }
    setTriggeringTraining(false);
  }

  if (loading && !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="neu-card p-8"><div className="neu-pulse text-xl font-semibold">Loading OverLLM Pipeline...</div></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="neu-card m-4 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold neu-heading">OverLLM Training Dashboard</h1>
            <p className="neu-text">24/7 multi-source crawling &amp; continuous fine-tuning pipeline</p>
          </div>
          <div className="flex gap-3 items-center">
            <span className="text-xs neu-text">Auto-refresh 60s &middot; #{refreshCount}</span>
            <button className="neu-button" onClick={fetchStats}>Refresh</button>
            <Link href="/"><button className="neu-button">Home</button></Link>
          </div>
        </div>
      </header>

      <main className="neu-container">
        {error && (
          <div className="neu-card p-4 mb-4" style={{ borderLeft: '4px solid #ef4444' }}>
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {stats && (
          <>
            {/* Top KPIs — persistent totals from DB */}
            <section className="mb-6">
              <h2 className="text-xl font-bold neu-heading mb-4">Pipeline Totals (all time)</h2>
              <div className="neu-grid neu-grid-4">
                <div className="neu-stat-card">
                  <div className="neu-subheading text-sm">Documents Crawled</div>
                  <div className="text-3xl font-bold neu-text-primary">{stats.totalDocuments.toLocaleString()}</div>
                  <div className="text-xs neu-text mt-1">{stats.totalCrawlCycles} crawl cycles</div>
                </div>
                <div className="neu-stat-card">
                  <div className="neu-subheading text-sm">Total Data</div>
                  <div className="text-3xl font-bold neu-text-primary">{fmtBytes(stats.totalBytes)}</div>
                  <div className="text-xs neu-text mt-1">stored in PostgreSQL</div>
                </div>
                <div className="neu-stat-card">
                  <div className="neu-subheading text-sm">Tokens Estimated</div>
                  <div className="text-3xl font-bold neu-text-primary">{fmtTokens(stats.totalTokens)}</div>
                  <div className="text-xs neu-text mt-1">{stats.unusedDocuments.toLocaleString()} unused for training</div>
                </div>
                <div className="neu-stat-card">
                  <div className="neu-subheading text-sm">Training Runs</div>
                  <div className="text-3xl font-bold neu-text-primary">{stats.trainingRuns.length}</div>
                  <div className="text-xs neu-text mt-1">
                    {stats.trainingRuns.filter((r: any) => r.status === 'training').length > 0 ? '🟢 Training active' : 'Auto-triggers at 100+ docs'}
                  </div>
                </div>
              </div>
            </section>

            {/* Training Control */}
            <section className="mb-6">
              <div className="neu-card p-6" style={{ borderLeft: '4px solid #3b82f6' }}>
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-bold neu-text-primary text-lg">Training Pipeline</div>
                    <div className="text-sm neu-text mt-1">
                      {stats.unusedDocuments} documents ready for training.
                      Auto-triggers when 100+ unused docs accumulate.
                    </div>
                    {trainResult && <div className="text-sm mt-2 neu-text-primary">{trainResult}</div>}
                  </div>
                  <button className="neu-button primary" onClick={handleTriggerTraining} disabled={triggeringTraining}>
                    {triggeringTraining ? 'Starting...' : 'Trigger Training Now'}
                  </button>
                </div>
              </div>
            </section>

            {/* Training Runs */}
            {stats.trainingRuns.length > 0 && (
              <section className="mb-6">
                <h2 className="text-xl font-bold neu-heading mb-4">Training Runs</h2>
                <div className="neu-card p-6">
                  <div className="space-y-2">
                    {stats.trainingRuns.map((run: any) => (
                      <div key={run.id} className="neu-card p-3 flex justify-between items-center">
                        <div>
                          <span className="font-semibold neu-text-primary">{run.id.slice(0, 12)}...</span>
                          <span className="text-xs neu-text ml-2">{new Date(run.startedAt).toLocaleString()}</span>
                          <span className="text-xs neu-text ml-2">{run.documentsUsed} docs · {fmtTokens(run.tokensUsed)} tokens</span>
                          {run.finetunJobId && <span className="text-xs neu-text ml-2">Job: {run.finetunJobId}</span>}
                        </div>
                        <span className={`neu-badge ${run.status === 'training' ? 'success' : run.status === 'failed' ? 'error' : 'warning'}`}>
                          {run.status.toUpperCase()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {/* Source Breakdown */}
            <section className="mb-6">
              <h2 className="text-xl font-bold neu-heading mb-4">Source Breakdown (all time)</h2>
              <div className="neu-card p-6">
                <div className="space-y-2">
                  {stats.sourceBreakdown.map((src: any) => (
                    <div key={src.sourceId} className="neu-card p-3 flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <Dot ok={true} />
                        <span className="font-semibold neu-text-primary">{src.sourceId}</span>
                      </div>
                      <div className="flex gap-4 text-sm">
                        <span className="neu-text">{src.documentCount.toLocaleString()} docs</span>
                        <span className="neu-text">{fmtBytes(src.totalBytes)}</span>
                        <span className="neu-text">{fmtTokens(src.totalTokens)} tokens</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Recent Crawl Cycles */}
            <section className="mb-8">
              <h2 className="text-xl font-bold neu-heading mb-4">Recent Crawl Cycles</h2>
              <div className="neu-card p-6" style={{ maxHeight: 400, overflowY: 'auto' }}>
                <div className="space-y-1 font-mono text-xs">
                  {stats.recentCycles.map((c: any) => (
                    <div key={c.id} className="flex gap-4 items-center">
                      <span className="neu-text whitespace-nowrap">{new Date(c.startedAt).toLocaleString()}</span>
                      <Dot ok={c.status === 'completed'} />
                      <span className="neu-text-primary">{c.totalDocuments} docs</span>
                      <span className="neu-text">{fmtBytes(c.totalBytes)}</span>
                      <span className="neu-text">{fmtTokens(c.totalTokens)} tokens</span>
                      <span className="text-green-400">{c.sourcesSucceeded} OK</span>
                      {c.sourcesFailed > 0 && <span className="text-red-400">{c.sourcesFailed} fail</span>}
                      <span className="neu-text">{(c.crawlTimeMs / 1000).toFixed(1)}s</span>
                    </div>
                  ))}
                  {stats.recentCycles.length === 0 && (
                    <div className="neu-text text-center py-4">No crawl cycles yet. Cron runs every minute.</div>
                  )}
                </div>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
