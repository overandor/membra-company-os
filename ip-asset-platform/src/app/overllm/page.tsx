'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

interface CrawlResult {
  sourceId: string;
  sourceName: string;
  status: 'success' | 'error';
  documentsCollected: number;
  bytesCollected: number;
  tokensEstimated: number;
  crawlTimeMs: number;
  sampleTitles: string[];
  error?: string;
}

interface CrawlSnapshot {
  timestamp: string;
  totalDocuments: number;
  totalBytes: number;
  totalTokensEstimated: number;
  totalCrawlTimeMs: number;
  sourcesSucceeded: number;
  sourcesFailed: number;
  sources: CrawlResult[];
}

function fmtBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
}

function fmtTokens(n: number) {
  if (n < 1000) return String(n);
  if (n < 1000000) return `${(n / 1000).toFixed(1)}K`;
  return `${(n / 1000000).toFixed(2)}M`;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      backgroundColor: ok ? '#22c55e' : '#ef4444', marginRight: 6,
    }} />
  );
}

export default function OverLLMDashboard() {
  const [latest, setLatest] = useState<CrawlSnapshot | null>(null);
  const [history, setHistory] = useState<CrawlSnapshot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Accumulated totals across all crawl cycles
  const totalDocs = history.reduce((s, h) => s + h.totalDocuments, 0);
  const totalBytes = history.reduce((s, h) => s + h.totalBytes, 0);
  const totalTokens = history.reduce((s, h) => s + h.totalTokensEstimated, 0);
  const totalCrawls = history.length;

  const doCrawl = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/overllm/kpis');
      const data = await res.json();
      if (data.success && data.snapshot) {
        setLatest(data.snapshot);
        setHistory(prev => [data.snapshot, ...prev].slice(0, 100));
        setRefreshCount(c => c + 1);
        setLastRefresh(new Date());
      } else {
        setError(data.error || 'Unknown error');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Fetch failed');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    doCrawl();
    const interval = setInterval(doCrawl, 60000);
    return () => clearInterval(interval);
  }, [doCrawl]);

  return (
    <div className="min-h-screen">
      <header className="neu-card m-4 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold neu-heading">OverLLM Training Dashboard</h1>
            <p className="neu-text">Real-time multi-source data crawling pipeline</p>
          </div>
          <div className="flex gap-3 items-center">
            <span className="text-xs neu-text">
              Auto-crawl every 60s &middot; Cycle #{refreshCount}
              {lastRefresh && <> &middot; {lastRefresh.toLocaleTimeString()}</>}
            </span>
            <button className="neu-button" onClick={doCrawl} disabled={loading}>
              {loading ? 'Crawling...' : 'Crawl Now'}
            </button>
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

        {/* Status Banner */}
        <section className="mb-6">
          <div className="neu-card p-6" style={{ borderLeft: `4px solid ${loading ? '#eab308' : latest ? '#22c55e' : '#6b7280'}` }}>
            <div className="flex items-center gap-3">
              <StatusDot ok={!loading && !!latest} />
              <span className="text-lg font-bold neu-text-primary">
                {loading ? 'Crawling all sources...' : latest
                  ? `Last crawl: ${latest.sourcesSucceeded}/${latest.sources.length} sources OK in ${(latest.totalCrawlTimeMs / 1000).toFixed(1)}s`
                  : 'Initializing...'}
              </span>
            </div>
          </div>
        </section>

        {/* Cumulative KPIs */}
        <section className="mb-6">
          <h2 className="text-xl font-bold neu-heading mb-4">Cumulative Totals (this session)</h2>
          <div className="neu-grid neu-grid-4">
            <div className="neu-stat-card neu-slide-in">
              <div className="neu-subheading text-sm">Total Documents</div>
              <div className="text-3xl font-bold neu-text-primary">{totalDocs.toLocaleString()}</div>
              <div className="text-xs neu-text mt-1">{totalCrawls} crawl cycles</div>
            </div>
            <div className="neu-stat-card neu-slide-in" style={{ animationDelay: '0.1s' }}>
              <div className="neu-subheading text-sm">Total Data</div>
              <div className="text-3xl font-bold neu-text-primary">{fmtBytes(totalBytes)}</div>
              <div className="text-xs neu-text mt-1">raw bytes crawled</div>
            </div>
            <div className="neu-stat-card neu-slide-in" style={{ animationDelay: '0.2s' }}>
              <div className="neu-subheading text-sm">Tokens Estimated</div>
              <div className="text-3xl font-bold neu-text-primary">{fmtTokens(totalTokens)}</div>
              <div className="text-xs neu-text mt-1">~4 bytes/token</div>
            </div>
            <div className="neu-stat-card neu-slide-in" style={{ animationDelay: '0.3s' }}>
              <div className="neu-subheading text-sm">Sources Active</div>
              <div className="text-3xl font-bold neu-text-primary">{latest?.sourcesSucceeded ?? 0}/{latest?.sources.length ?? 8}</div>
              <div className="text-xs neu-text mt-1">{latest?.sourcesFailed ?? 0} failed</div>
            </div>
          </div>
        </section>

        {/* Latest Crawl - Per Source */}
        {latest && (
          <section className="mb-6">
            <h2 className="text-xl font-bold neu-heading mb-4">Latest Crawl Results</h2>
            <div className="neu-card p-6">
              <div className="space-y-3">
                {latest.sources.map(src => (
                  <div key={src.sourceId} className="neu-card p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <StatusDot ok={src.status === 'success'} />
                        <span className="font-semibold neu-text-primary">{src.sourceName}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs neu-text">{src.crawlTimeMs}ms</span>
                        <span className={`neu-badge ${src.status === 'success' ? 'success' : 'error'}`}>
                          {src.status === 'success'
                            ? `${src.documentsCollected} docs · ${fmtBytes(src.bytesCollected)} · ${fmtTokens(src.tokensEstimated)} tokens`
                            : src.error || 'ERROR'}
                        </span>
                      </div>
                    </div>
                    {src.sampleTitles.length > 0 && (
                      <div className="ml-4 space-y-1">
                        {src.sampleTitles.map((title, i) => (
                          <div key={i} className="text-xs neu-text truncate">
                            &bull; {title}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Crawl History Timeline */}
        {history.length > 1 && (
          <section className="mb-8">
            <h2 className="text-xl font-bold neu-heading mb-4">Crawl History</h2>
            <div className="neu-card p-6" style={{ maxHeight: 400, overflowY: 'auto' }}>
              <div className="space-y-2 font-mono text-xs">
                {history.map((snap, i) => (
                  <div key={i} className="flex gap-4 items-center">
                    <span className="neu-text whitespace-nowrap">{new Date(snap.timestamp).toLocaleTimeString()}</span>
                    <span className="neu-text-primary">
                      {snap.totalDocuments} docs
                    </span>
                    <span className="neu-text">{fmtBytes(snap.totalBytes)}</span>
                    <span className="neu-text">{fmtTokens(snap.totalTokensEstimated)} tokens</span>
                    <span className="text-green-400">{snap.sourcesSucceeded} OK</span>
                    {snap.sourcesFailed > 0 && <span className="text-red-400">{snap.sourcesFailed} failed</span>}
                    <span className="neu-text">{(snap.totalCrawlTimeMs / 1000).toFixed(1)}s</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
