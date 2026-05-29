'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

/* ── helpers ─────────────────────────────────────────── */
const fB = (b: number) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b/1024).toFixed(1)} KB` : b < 1073741824 ? `${(b/1048576).toFixed(1)} MB` : `${(b/1073741824).toFixed(2)} GB`;
const fT = (n: number) => n < 1000 ? String(n) : n < 1e6 ? `${(n/1000).toFixed(1)}K` : `${(n/1e6).toFixed(2)}M`;
const srcIcon: Record<string, string> = { wikipedia: '📚', arxiv: '🔬', hackernews: '🟠', gutenberg: '📖', pubmed: '🏥', github: '🐙', stackoverflow: '💬', openlibrary: '🏛️' };

/* ── styles (orange neumorphic) ──────────────────────── */
const S = {
  bg: '#1a1a2e',
  surface: '#16213e',
  card: 'rgba(255,140,50,0.06)',
  accent: '#ff8c32',
  accentGlow: '#ff6b00',
  accentSoft: 'rgba(255,140,50,0.15)',
  text: '#e8e8e8',
  textDim: '#8892a4',
  success: '#4ade80',
  error: '#f87171',
  warning: '#fbbf24',

  neuCard: {
    background: 'linear-gradient(145deg, #1e2a4a, #141c34)',
    borderRadius: 20,
    boxShadow: '8px 8px 20px rgba(0,0,0,0.5), -4px -4px 12px rgba(255,140,50,0.04), inset 0 1px 0 rgba(255,140,50,0.08)',
    border: '1px solid rgba(255,140,50,0.1)',
    padding: 24,
    transition: 'all 0.3s ease',
  } as React.CSSProperties,

  neuCardHover: {
    boxShadow: '10px 10px 24px rgba(0,0,0,0.6), -6px -6px 16px rgba(255,140,50,0.08), inset 0 1px 0 rgba(255,140,50,0.12)',
  } as React.CSSProperties,

  neuStat: {
    background: 'linear-gradient(145deg, #1e2a4a, #141c34)',
    borderRadius: 16,
    boxShadow: '6px 6px 16px rgba(0,0,0,0.5), -3px -3px 10px rgba(255,140,50,0.04)',
    border: '1px solid rgba(255,140,50,0.08)',
    padding: 20,
    textAlign: 'center' as const,
  },

  neuBtn: (primary = false) => ({
    background: primary ? 'linear-gradient(135deg, #ff8c32, #ff6b00)' : 'linear-gradient(145deg, #1e2a4a, #141c34)',
    borderRadius: 12,
    boxShadow: primary ? '0 4px 15px rgba(255,107,0,0.4)' : '4px 4px 10px rgba(0,0,0,0.5), -2px -2px 8px rgba(255,140,50,0.03)',
    border: primary ? 'none' : '1px solid rgba(255,140,50,0.1)',
    padding: '10px 20px',
    fontWeight: 700,
    color: primary ? '#fff' : '#e8e8e8',
    cursor: 'pointer',
    fontSize: 13,
    transition: 'all 0.2s',
  }),

  neuProgress: {
    background: 'rgba(0,0,0,0.3)',
    borderRadius: 10,
    boxShadow: 'inset 3px 3px 6px rgba(0,0,0,0.4), inset -2px -2px 4px rgba(255,140,50,0.03)',
    height: 10,
    overflow: 'hidden' as const,
  },

  neuProgressFill: (pct: number) => ({
    height: '100%',
    width: `${Math.min(pct, 100)}%`,
    background: 'linear-gradient(90deg, #ff6b00, #ff8c32, #ffb366)',
    borderRadius: 10,
    transition: 'width 0.6s ease',
    boxShadow: '0 0 8px rgba(255,107,0,0.5)',
  }),

  badge: (type: string) => ({
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 700,
    background: type === 'success' ? 'rgba(74,222,128,0.15)' : type === 'error' ? 'rgba(248,113,113,0.15)' : 'rgba(255,140,50,0.15)',
    color: type === 'success' ? '#4ade80' : type === 'error' ? '#f87171' : '#ff8c32',
    border: `1px solid ${type === 'success' ? 'rgba(74,222,128,0.3)' : type === 'error' ? 'rgba(248,113,113,0.3)' : 'rgba(255,140,50,0.3)'}`,
  }),

  glow: {
    position: 'absolute' as const, top: -100, right: -100, width: 300, height: 300,
    background: 'radial-gradient(circle, rgba(255,140,50,0.08) 0%, transparent 70%)',
    borderRadius: '50%', pointerEvents: 'none' as const,
  },
};

function Pulse({ active }: { active: boolean }) {
  return (
    <span style={{
      display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
      background: active ? S.accent : '#555',
      boxShadow: active ? `0 0 8px ${S.accent}, 0 0 16px rgba(255,107,0,0.3)` : 'none',
      animation: active ? 'pulse 2s infinite' : 'none',
      marginRight: 8,
    }} />
  );
}

export default function OverLLMOrganism() {
  const [stats, setStats] = useState<any>(null);
  const [lastCrawl, setLastCrawl] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);
  const [training, setTraining] = useState(false);
  const [trainMsg, setTrainMsg] = useState('');
  const [error, setError] = useState('');
  const [tick, setTick] = useState(0);
  const [secondsToRefresh, setSecondsToRefresh] = useState(60);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch('/api/overllm/kpis');
      const data = await res.json();
      if (data.success) { setStats(data.stats); setError(''); }
      else setError(data.error || 'Unknown');
    } catch (e: any) { setError(e.message); }
    setLoading(false);
    setTick(t => t + 1);
    setSecondsToRefresh(60);
  }, []);

  useEffect(() => { refresh(); const iv = setInterval(refresh, 60000); return () => clearInterval(iv); }, [refresh]);
  useEffect(() => { const iv = setInterval(() => setSecondsToRefresh(s => Math.max(0, s - 1)), 1000); return () => clearInterval(iv); }, []);

  async function doCrawl() {
    setCrawling(true);
    try {
      const res = await fetch('/api/overllm/cron');
      const data = await res.json();
      if (data.success) setLastCrawl(data.snapshot);
      await refresh();
    } catch {}
    setCrawling(false);
  }

  async function doTrain() {
    setTraining(true); setTrainMsg('');
    try {
      const res = await fetch('/api/overllm/training', { method: 'POST' });
      const data = await res.json();
      setTrainMsg(data.message || data.status || JSON.stringify(data));
      await refresh();
    } catch (e: any) { setTrainMsg(e.message); }
    setTraining(false);
  }

  return (
    <div style={{ minHeight: '100vh', background: S.bg, color: S.text, fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <style>{`
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.5 } }
        @keyframes float { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-6px) } }
        @keyframes glow-ring { 0% { box-shadow: 0 0 5px rgba(255,140,50,0.3) } 50% { box-shadow: 0 0 20px rgba(255,140,50,0.6) } 100% { box-shadow: 0 0 5px rgba(255,140,50,0.3) } }
        .organ-card:hover { transform: translateY(-3px) !important; }
        .crawl-btn:active { transform: scale(0.96); }
      `}</style>

      {/* ── HEADER ── */}
      <header style={{ ...S.neuCard, margin: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', overflow: 'hidden' }}>
        <div style={S.glow} />
        <div>
          <div style={{ fontSize: 28, fontWeight: 800, background: 'linear-gradient(135deg, #ff8c32, #ffb366)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            🧬 OverLLM Organism
          </div>
          <div style={{ color: S.textDim, fontSize: 13, marginTop: 4 }}>
            Living self-training AI — 8 sensory organs crawling 24/7
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ textAlign: 'right', fontSize: 11, color: S.textDim }}>
            <div>Refresh in {secondsToRefresh}s · Tick #{tick}</div>
            <div>{stats?.dbConnected ? '🟢 DB Connected' : '🟡 In-Memory Mode'}</div>
          </div>
          <button style={S.neuBtn()} onClick={refresh}>↻ Refresh</button>
          <Link href="/"><button style={S.neuBtn()}>Home</button></Link>
        </div>
      </header>

      <main style={{ maxWidth: 1440, margin: '0 auto', padding: '0 16px 40px' }}>
        {error && (
          <div style={{ ...S.neuCard, marginBottom: 16, borderLeft: '4px solid #f87171', padding: 16 }}>
            <span style={{ color: '#f87171', fontSize: 13 }}>{error}</span>
          </div>
        )}

        {/* ── ORGANISM VITAL SIGNS ── */}
        <section style={{ marginBottom: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
            {[
              { label: '🧬 Documents Crawled', value: stats?.totalDocuments?.toLocaleString() ?? '—', sub: `${stats?.totalCrawlCycles ?? 0} cycles` },
              { label: '⚡ Data Ingested', value: fB(stats?.totalBytes ?? 0), sub: 'stored persistently' },
              { label: '🔥 Tokens Ready', value: fT(stats?.totalTokens ?? 0), sub: `${stats?.unusedDocuments ?? 0} unused` },
              { label: '🧠 Training Runs', value: String(stats?.trainingRuns?.length ?? 0), sub: stats?.trainingRuns?.some((r: any) => r.status === 'training') ? '🟢 Active' : 'auto at 100+ docs' },
            ].map((kpi, i) => (
              <div key={i} style={{ ...S.neuStat, animation: `float 3s ease-in-out ${i * 0.2}s infinite` }} className="organ-card">
                <div style={{ fontSize: 12, color: S.textDim, marginBottom: 6 }}>{kpi.label}</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: S.accent }}>{kpi.value}</div>
                <div style={{ fontSize: 11, color: S.textDim, marginTop: 4 }}>{kpi.sub}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── ORGANISM CORE — BRAIN + HEART ── */}
        <section style={{ marginBottom: 24 }}>
          <div style={{ ...S.neuCard, position: 'relative', overflow: 'hidden', borderLeft: `4px solid ${S.accent}` }}>
            <div style={{ ...S.glow, top: -80, right: -80 }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Pulse active={crawling || training} />
                  <span style={{ fontSize: 18, fontWeight: 700, color: S.accent }}>
                    {crawling ? '👁 Crawling all sources...' : training ? '🧠 Training in progress...' : '🫀 Organism alive — awaiting next heartbeat'}
                  </span>
                </div>
                {trainMsg && <div style={{ fontSize: 13, color: S.textDim, marginTop: 8 }}>{trainMsg}</div>}
                {lastCrawl && (
                  <div style={{ fontSize: 12, color: S.textDim, marginTop: 8 }}>
                    Last crawl: {lastCrawl.totalDocuments} docs · {fB(lastCrawl.totalBytes)} · {lastCrawl.sourcesSucceeded}/{lastCrawl.sources.length} sources · {(lastCrawl.totalCrawlTimeMs/1000).toFixed(1)}s
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button style={S.neuBtn(true)} onClick={doCrawl} disabled={crawling} className="crawl-btn">
                  {crawling ? '⏳ Crawling...' : '👁 Crawl Now'}
                </button>
                <button style={S.neuBtn()} onClick={doTrain} disabled={training}>
                  {training ? '⏳ Training...' : '🧠 Train Now'}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ── 👁 SENSORY ORGANS — per-source breakdown ── */}
        <section style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: S.accent, marginBottom: 12 }}>👁 Sensory Organs (Data Sources)</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {(stats?.sourceBreakdown ?? []).map((src: any) => (
              <div key={src.sourceId} style={{ ...S.neuStat, padding: 16, textAlign: 'left' }} className="organ-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 20 }}>{srcIcon[src.sourceId] || '🌐'}</span>
                  <span style={{ fontWeight: 700, fontSize: 13, color: S.text }}>{src.sourceId}</span>
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, color: S.accent }}>{src.documentCount.toLocaleString()}</div>
                <div style={{ fontSize: 11, color: S.textDim }}>{fB(src.totalBytes)} · {fT(src.totalTokens)} tokens</div>
                <div style={{ ...S.neuProgress, marginTop: 8 }}>
                  <div style={S.neuProgressFill(stats?.totalDocuments ? (src.documentCount / stats.totalDocuments) * 100 * 8 : 0)} />
                </div>
              </div>
            ))}
            {(stats?.sourceBreakdown ?? []).length === 0 && (
              <div style={{ gridColumn: '1/-1', textAlign: 'center', color: S.textDim, padding: 40 }}>
                No data yet — hit "Crawl Now" to activate the sensory organs
              </div>
            )}
          </div>
        </section>

        {/* ── Latest crawl results ── */}
        {lastCrawl && (
          <section style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: S.accent, marginBottom: 12 }}>🔬 Latest Crawl Results</div>
            <div style={S.neuCard}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {lastCrawl.sources.map((src: any) => (
                  <div key={src.sourceId} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderRadius: 12, background: 'rgba(255,140,50,0.04)', border: '1px solid rgba(255,140,50,0.06)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Pulse active={src.status === 'success'} />
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{srcIcon[src.sourceId] || '🌐'} {src.sourceName}</span>
                    </div>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                      <span style={{ fontSize: 12, color: S.textDim }}>{src.crawlTimeMs}ms</span>
                      <span style={S.badge(src.status === 'success' ? 'success' : 'error')}>
                        {src.status === 'success' ? `${src.documentsCollected} docs · ${fB(src.bytesCollected)}` : src.error || 'ERROR'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {lastCrawl.sources.some((s: any) => s.sampleTitles?.length > 0) && (
                <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: 'rgba(0,0,0,0.2)' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: S.accent, marginBottom: 8 }}>📄 Sample titles crawled</div>
                  {lastCrawl.sources.filter((s: any) => s.sampleTitles?.length > 0).slice(0, 4).map((s: any) => (
                    <div key={s.sourceId} style={{ marginBottom: 6 }}>
                      <span style={{ fontSize: 11, color: S.textDim }}>{srcIcon[s.sourceId]} </span>
                      {s.sampleTitles.slice(0, 2).map((t: string, i: number) => (
                        <span key={i} style={{ fontSize: 11, color: S.text }}>{t}{i < 1 && s.sampleTitles.length > 1 ? ' · ' : ''}</span>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── 🧠 Training Runs ── */}
        {(stats?.trainingRuns?.length > 0 || mem_runs_fallback().length > 0) && (
          <section style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: S.accent, marginBottom: 12 }}>🧠 Training Cortex — Run History</div>
            <div style={S.neuCard}>
              {(stats?.trainingRuns ?? []).map((run: any) => (
                <div key={run.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: 12, background: 'rgba(255,140,50,0.04)', border: '1px solid rgba(255,140,50,0.06)', marginBottom: 8 }}>
                  <div>
                    <span style={{ fontWeight: 700, fontSize: 13, color: S.accent }}>{run.id?.slice(0, 16)}...</span>
                    <span style={{ fontSize: 11, color: S.textDim, marginLeft: 10 }}>{new Date(run.startedAt).toLocaleString()}</span>
                    <span style={{ fontSize: 11, color: S.textDim, marginLeft: 10 }}>{run.documentsUsed} docs · {fT(run.tokensUsed)} tokens</span>
                    {run.finetunJobId && <span style={{ fontSize: 11, color: S.textDim, marginLeft: 10 }}>Job: {run.finetunJobId}</span>}
                    {run.ipfsHash && <span style={{ fontSize: 11, color: S.success, marginLeft: 10 }}>IPFS: {run.ipfsHash.slice(0, 12)}...</span>}
                  </div>
                  <span style={S.badge(run.status === 'training' ? 'success' : run.status === 'failed' ? 'error' : 'warning')}>
                    {run.status?.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── 🫀 HEARTBEAT — Recent Crawl Cycles ── */}
        <section style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: S.accent, marginBottom: 12 }}>🫀 Heartbeat — Crawl History</div>
          <div style={{ ...S.neuCard, maxHeight: 350, overflowY: 'auto' }}>
            {(stats?.recentCycles ?? []).length === 0 ? (
              <div style={{ textAlign: 'center', color: S.textDim, padding: 32 }}>No heartbeats yet. Cron activates every 5 min via GitHub Actions.</div>
            ) : (
              <div style={{ fontFamily: 'monospace', fontSize: 12 }}>
                {(stats?.recentCycles ?? []).map((c: any, i: number) => (
                  <div key={c.id || i} style={{ display: 'flex', gap: 16, padding: '6px 0', borderBottom: '1px solid rgba(255,140,50,0.06)' }}>
                    <span style={{ color: S.textDim, whiteSpace: 'nowrap' }}>{new Date(c.startedAt || c.timestamp).toLocaleString()}</span>
                    <Pulse active={c.status === 'completed'} />
                    <span style={{ color: S.accent, fontWeight: 700 }}>{c.totalDocuments} docs</span>
                    <span style={{ color: S.textDim }}>{fB(c.totalBytes || 0)}</span>
                    <span style={{ color: S.textDim }}>{fT(c.totalTokens || c.totalTokensEstimated || 0)} tok</span>
                    <span style={{ color: S.success }}>{c.sourcesSucceeded} OK</span>
                    {c.sourcesFailed > 0 && <span style={{ color: S.error }}>{c.sourcesFailed} fail</span>}
                    <span style={{ color: S.textDim }}>{((c.crawlTimeMs || c.totalCrawlTimeMs || 0)/1000).toFixed(1)}s</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* ── ⚡ NERVOUS SYSTEM — API Endpoints ── */}
        <section>
          <div style={{ fontSize: 18, fontWeight: 700, color: S.accent, marginBottom: 12 }}>⚡ Nervous System — Vercel Function Endpoints</div>
          <div style={{ ...S.neuCard }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              {[
                { path: '/api/overllm/kpis', label: '💾 Memory (Stats)', method: 'GET' },
                { path: '/api/overllm/cron', label: '🫀 Heartbeat (Crawl)', method: 'GET' },
                { path: '/api/overllm/training', label: '🧠 Cortex (Train)', method: 'POST' },
                { path: '/api/overllm/sources', label: '👁 Sensory List', method: 'GET' },
                { path: '/api/overllm/ipfs', label: '🫁 Lungs (IPFS)', method: 'POST' },
                { path: '/api/overllm/status', label: '⚡ Nervous Status', method: 'GET' },
              ].map(ep => (
                <div key={ep.path} style={{ padding: 12, borderRadius: 12, background: 'rgba(255,140,50,0.04)', border: '1px solid rgba(255,140,50,0.08)' }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: S.text }}>{ep.label}</div>
                  <div style={{ fontSize: 11, color: S.accent, fontFamily: 'monospace', marginTop: 4 }}>{ep.method} {ep.path}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function mem_runs_fallback() { return []; }
