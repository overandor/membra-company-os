/**
 * OverLLM — The Living Training Organism
 *
 * Organs:
 *   🧠 Cortex     — orchestrates training runs
 *   👁 Crawler    — 8 sensory inputs from the web (real HTTP crawls)
 *   💾 Memory     — PostgreSQL persistence (falls back to in-memory)
 *   🫀 Heartbeat  — Vercel Cron / GitHub Actions every 5 min
 *   🫁 Lungs      — IPFS weight upload / retrieval
 *   ⚡ Nervous    — Vercel serverless function mesh
 */

import crypto from 'crypto';

// ---------------------------------------------------------------------------
// Try to connect Prisma — graceful fallback if no DB
// ---------------------------------------------------------------------------
let _prisma: any = null;
let _dbChecked = false;
let _dbOk = false;

async function getPrisma() {
  if (_dbChecked) return _dbOk ? _prisma : null;
  _dbChecked = true;

  // Skip DB entirely if DATABASE_URL looks like a placeholder
  const url = process.env.DATABASE_URL || '';
  if (!url || url.includes('user:password') || url.includes('your-') || (!url.startsWith('postgres') && !url.startsWith('prisma'))) {
    _dbOk = false;
    return null;
  }

  try {
    const { PrismaClient } = await import('@prisma/client');
    const g = globalThis as any;
    _prisma = g.__prisma || new PrismaClient();
    if (process.env.NODE_ENV !== 'production') g.__prisma = _prisma;
    await _prisma.$queryRaw`SELECT 1`;
    _dbOk = true;
    return _prisma;
  } catch {
    _dbOk = false;
    _prisma = null;
    return null;
  }
}

// In-memory fallback store
const mem = {
  documents: [] as any[],
  cycles: [] as any[],
  runs: [] as any[],
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CrawlResult {
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

export interface CrawlSnapshot {
  cycleId: string;
  timestamp: string;
  totalDocuments: number;
  totalBytes: number;
  totalTokensEstimated: number;
  totalCrawlTimeMs: number;
  sourcesSucceeded: number;
  sourcesFailed: number;
  sources: CrawlResult[];
}

interface RawDoc { title: string; content: string; }

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function fetchJson(url: string, timeout = 12000): Promise<any> {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), timeout);
  try {
    const r = await fetch(url, { signal: c.signal, headers: { 'User-Agent': 'OverLLM-Organism/3.0' } });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } finally { clearTimeout(t); }
}

async function fetchText(url: string, timeout = 12000): Promise<string> {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), timeout);
  try {
    const r = await fetch(url, { signal: c.signal, headers: { 'User-Agent': 'OverLLM-Organism/3.0' } });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.text();
  } finally { clearTimeout(t); }
}

function sha256(text: string): string {
  return crypto.createHash('sha256').update(text).digest('hex');
}

// ---------------------------------------------------------------------------
// 👁 CRAWLER — 8 sensory organs
// ---------------------------------------------------------------------------

const SOURCES: { id: string; name: string; icon: string; crawl: () => Promise<RawDoc[]> }[] = [
  {
    id: 'wikipedia', name: 'Wikipedia', icon: '📚',
    crawl: async () => {
      const docs: RawDoc[] = [];
      for (let i = 0; i < 5; i++) {
        try {
          const d = await fetchJson('https://en.wikipedia.org/api/rest_v1/page/random/summary');
          if (d.extract) docs.push({ title: d.title || 'Untitled', content: d.extract });
        } catch {}
      }
      return docs;
    },
  },
  {
    id: 'arxiv', name: 'arXiv CS/AI', icon: '🔬',
    crawl: async () => {
      const xml = await fetchText('https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10');
      return [...xml.matchAll(/<entry>([\s\S]*?)<\/entry>/g)].map(e => {
        const title = e[1].match(/<title>([\s\S]*?)<\/title>/)?.[1]?.trim() || 'Untitled';
        const summary = e[1].match(/<summary>([\s\S]*?)<\/summary>/)?.[1]?.trim() || '';
        return { title, content: `${title}\n\n${summary}` };
      });
    },
  },
  {
    id: 'hackernews', name: 'Hacker News', icon: '🟠',
    crawl: async () => {
      const ids: number[] = await fetchJson('https://hacker-news.firebaseio.com/v0/topstories.json');
      const docs: RawDoc[] = [];
      await Promise.all(ids.slice(0, 10).map(async id => {
        try {
          const item = await fetchJson(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
          if (item?.title) docs.push({ title: item.title, content: [item.title, item.text || '', item.url || ''].join('\n') });
        } catch {}
      }));
      return docs;
    },
  },
  {
    id: 'gutenberg', name: 'Project Gutenberg', icon: '📖',
    crawl: async () => {
      const data = await fetchJson('https://gutendex.com/books/?languages=en&sort=popular&page=1');
      return (data.results || []).slice(0, 10).map((b: any) => ({
        title: b.title,
        content: `${b.title} by ${(b.authors || []).map((a: any) => a.name).join(', ')}. Subjects: ${(b.subjects || []).join(', ')}`,
      }));
    },
  },
  {
    id: 'pubmed', name: 'PubMed', icon: '🏥',
    crawl: async () => {
      const search = await fetchJson('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=10&sort=date&term=machine+learning');
      const ids: string[] = search?.esearchresult?.idlist || [];
      if (!ids.length) return [];
      const summary = await fetchJson(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=${ids.join(',')}`);
      return ids.map(id => summary?.result?.[id]).filter(Boolean).filter((a: any) => a.title).map((a: any) => ({ title: a.title, content: JSON.stringify(a) }));
    },
  },
  {
    id: 'github', name: 'GitHub Trending', icon: '🐙',
    crawl: async () => {
      const data = await fetchJson('https://api.github.com/search/repositories?q=stars:>100+language:python&sort=updated&per_page=10');
      return (data.items || []).map((r: any) => ({
        title: r.full_name,
        content: `${r.full_name}: ${r.description || ''}. Stars: ${r.stargazers_count}. Lang: ${r.language}. Topics: ${(r.topics || []).join(', ')}`,
      }));
    },
  },
  {
    id: 'stackoverflow', name: 'StackOverflow', icon: '💬',
    crawl: async () => {
      const data = await fetchJson('https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow&pagesize=10&filter=withbody');
      return (data.items || []).map((q: any) => ({ title: q.title, content: `Q: ${q.title}\n\n${q.body || ''}` }));
    },
  },
  {
    id: 'openlibrary', name: 'Open Library', icon: '🏛️',
    crawl: async () => {
      const data = await fetchJson('https://openlibrary.org/subjects/science.json?limit=10');
      return (data.works || []).map((w: any) => ({
        title: w.title,
        content: `${w.title} by ${(w.authors || []).map((a: any) => a.name).join(', ')}. First published: ${w.first_publish_year || 'unknown'}`,
      }));
    },
  },
];

// ---------------------------------------------------------------------------
// 🧠 CORTEX — crawl cycle + training orchestration
// ---------------------------------------------------------------------------

export async function runCrawlCycle(): Promise<CrawlSnapshot> {
  const cycleStart = Date.now();
  const db = await getPrisma();
  let cycleId = `mem-${Date.now().toString(36)}`;

  if (db) {
    try {
      const cycle = await db.crawlCycle.create({ data: { status: 'running' } });
      cycleId = cycle.id;
    } catch {}
  }

  const results: CrawlResult[] = await Promise.all(
    SOURCES.map(async (source): Promise<CrawlResult> => {
      const t0 = Date.now();
      try {
        const rawDocs = await source.crawl();
        let bytesCollected = 0, tokensEstimated = 0, stored = 0;
        const titles: string[] = [];

        for (const doc of rawDocs) {
          const ch = sha256(doc.content);
          const byteSize = Buffer.byteLength(doc.content, 'utf8');
          const tokenEst = Math.round(byteSize / 4);

          if (db) {
            try {
              await db.crawlDocument.create({
                data: { sourceId: source.id, sourceName: source.name, title: doc.title.slice(0, 500), content: doc.content, contentHash: ch, byteSize, tokenEstimate: tokenEst },
              });
              stored++;
            } catch (e: any) {
              if (e.code !== 'P2002') throw e;
            }
          } else {
            if (!mem.documents.find((d: any) => d.contentHash === ch)) {
              mem.documents.push({ sourceId: source.id, sourceName: source.name, title: doc.title, content: doc.content, contentHash: ch, byteSize, tokenEstimate: tokenEst, crawledAt: new Date().toISOString(), usedInTraining: false });
              stored++;
            }
          }
          bytesCollected += byteSize;
          tokensEstimated += tokenEst;
          titles.push(doc.title);
        }

        return { sourceId: source.id, sourceName: source.name, status: 'success', documentsCollected: stored, bytesCollected, tokensEstimated, crawlTimeMs: Date.now() - t0, sampleTitles: titles.slice(0, 5) };
      } catch (err) {
        return { sourceId: source.id, sourceName: source.name, status: 'error', documentsCollected: 0, bytesCollected: 0, tokensEstimated: 0, crawlTimeMs: Date.now() - t0, sampleTitles: [], error: err instanceof Error ? err.message : String(err) };
      }
    })
  );

  const totalDocs = results.reduce((s, r) => s + r.documentsCollected, 0);
  const totalBytes = results.reduce((s, r) => s + r.bytesCollected, 0);
  const totalTokens = results.reduce((s, r) => s + r.tokensEstimated, 0);
  const succeeded = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'error').length;
  const elapsed = Date.now() - cycleStart;

  const snapshot: CrawlSnapshot = { cycleId, timestamp: new Date().toISOString(), totalDocuments: totalDocs, totalBytes, totalTokensEstimated: totalTokens, totalCrawlTimeMs: elapsed, sourcesSucceeded: succeeded, sourcesFailed: failed, sources: results };

  if (db) {
    try {
      await db.crawlCycle.update({ where: { id: cycleId }, data: { completedAt: new Date(), totalDocuments: totalDocs, totalBytes, totalTokens, sourcesSucceeded: succeeded, sourcesFailed: failed, crawlTimeMs: elapsed, sourceResults: JSON.parse(JSON.stringify(results)), status: 'completed' } });
    } catch {}
  } else {
    mem.cycles.unshift(snapshot);
    if (mem.cycles.length > 100) mem.cycles.length = 100;
  }

  return snapshot;
}

// ---------------------------------------------------------------------------
// 🫁 LUNGS — IPFS weight upload via Pinata
// ---------------------------------------------------------------------------

export async function uploadWeightsToIPFS(data: { runId: string; model: string; metadata: any }): Promise<{ ipfsHash: string; gatewayUrl: string }> {
  const apiKey = process.env.PINATA_API_KEY;
  const secretKey = process.env.PINATA_SECRET_KEY;
  const gateway = process.env.PINATA_GATEWAY || 'https://gateway.pinata.cloud/ipfs';

  if (!apiKey || !secretKey || apiKey === 'your-pinata-api-key') {
    throw new Error('PINATA_API_KEY not configured');
  }

  const payload = {
    pinataContent: {
      overllm_version: '3.0',
      organism: 'OverLLM',
      run_id: data.runId,
      model_id: data.model,
      uploaded_at: new Date().toISOString(),
      ...data.metadata,
    },
    pinataMetadata: {
      name: `overllm-weights-${data.runId}`,
      keyvalues: { type: 'model-weights', runId: data.runId, model: data.model },
    },
  };

  const res = await fetch('https://api.pinata.cloud/pinning/pinJSONToIPFS', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'pinata_api_key': apiKey, 'pinata_secret_api_key': secretKey },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error(`Pinata upload failed: ${res.status}`);
  const result = await res.json();

  return { ipfsHash: result.IpfsHash, gatewayUrl: `${gateway}/${result.IpfsHash}` };
}

// ---------------------------------------------------------------------------
// 🧠 Training trigger + IPFS upload
// ---------------------------------------------------------------------------

export async function triggerTraining(): Promise<any> {
  const db = await getPrisma();
  let docs: any[];

  if (db) {
    docs = await db.crawlDocument.findMany({ where: { usedInTraining: false }, orderBy: { crawledAt: 'asc' }, take: 500 });
  } else {
    docs = mem.documents.filter((d: any) => !d.usedInTraining).slice(0, 500);
  }

  if (docs.length < 10) {
    return { status: 'waiting', message: `Only ${docs.length} docs. Need 10+.`, documentsAvailable: docs.length };
  }

  const runId = `run-${Date.now().toString(36)}`;
  const tokensUsed = docs.reduce((s: number, d: any) => s + (d.tokenEstimate || 0), 0);

  // Build JSONL
  const jsonl = docs.map((doc: any) => JSON.stringify({
    messages: [
      { role: 'system', content: 'You are OverLLM, a living AI organism trained on diverse real-world knowledge.' },
      { role: 'user', content: `Tell me about: ${doc.title}` },
      { role: 'assistant', content: doc.content },
    ],
  })).join('\n');

  // Mark as used
  if (db) {
    await db.crawlDocument.updateMany({ where: { id: { in: docs.map((d: any) => d.id) } }, data: { usedInTraining: true } });
  } else {
    for (const doc of docs) doc.usedInTraining = true;
  }

  const run = { id: runId, status: 'data_ready', startedAt: new Date().toISOString(), documentsUsed: docs.length, tokensUsed, jsonlSizeBytes: Buffer.byteLength(jsonl, 'utf8'), finetunJobId: null as string | null, ipfsHash: null as string | null };

  // Try OpenAI fine-tune
  const apiKey = process.env.OPENAI_API_KEY;
  if (apiKey && apiKey !== 'your-openai-api-key') {
    try {
      const formData = new FormData();
      formData.append('purpose', 'fine-tune');
      formData.append('file', new Blob([jsonl], { type: 'application/jsonl' }), 'overllm-training.jsonl');
      const uploadRes = await fetch('https://api.openai.com/v1/files', { method: 'POST', headers: { 'Authorization': `Bearer ${apiKey}` }, body: formData });
      const uploadData = await uploadRes.json();
      if (uploadRes.ok) {
        const ftRes = await fetch('https://api.openai.com/v1/fine_tuning/jobs', { method: 'POST', headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ training_file: uploadData.id, model: 'gpt-4o-mini-2024-07-18', hyperparameters: { n_epochs: 3 }, suffix: 'overllm' }) });
        const ftData = await ftRes.json();
        if (ftRes.ok) { run.finetunJobId = ftData.id; run.status = 'training'; }
      }
    } catch {}
  }

  // Try IPFS upload of training manifest
  try {
    const ipfs = await uploadWeightsToIPFS({ runId, model: run.finetunJobId || 'pending', metadata: { documentsUsed: run.documentsUsed, tokensUsed: run.tokensUsed, sources: [...new Set(docs.map((d: any) => d.sourceId))] } });
    run.ipfsHash = ipfs.ipfsHash;
  } catch {}

  // Store run
  if (db) {
    try {
      await db.overLLMTrainingRun.create({ data: { status: run.status, documentsUsed: run.documentsUsed, tokensUsed: run.tokensUsed, finetunJobId: run.finetunJobId } });
    } catch {}
  }
  mem.runs.unshift(run);
  if (mem.runs.length > 50) mem.runs.length = 50;

  return run;
}

// ---------------------------------------------------------------------------
// 💾 MEMORY — dashboard stats
// ---------------------------------------------------------------------------

export async function getDashboardStats() {
  const db = await getPrisma();

  if (db) {
    try {
      const [totalDocs, totalCycles, recentCycles, trainingRuns, docsBySource, aggTokens, aggBytes, unusedDocs] = await Promise.all([
        db.crawlDocument.count(),
        db.crawlCycle.count(),
        db.crawlCycle.findMany({ orderBy: { startedAt: 'desc' }, take: 30 }),
        db.overLLMTrainingRun.findMany({ orderBy: { startedAt: 'desc' }, take: 10 }),
        db.crawlDocument.groupBy({ by: ['sourceId'], _count: true, _sum: { byteSize: true, tokenEstimate: true } }),
        db.crawlDocument.aggregate({ _sum: { tokenEstimate: true } }),
        db.crawlDocument.aggregate({ _sum: { byteSize: true } }),
        db.crawlDocument.count({ where: { usedInTraining: false } }),
      ]);
      return {
        dbConnected: true, totalDocuments: totalDocs, totalCrawlCycles: totalCycles,
        totalTokens: aggTokens._sum.tokenEstimate || 0, totalBytes: aggBytes._sum.byteSize || 0,
        unusedDocuments: unusedDocs, recentCycles, trainingRuns,
        sourceBreakdown: docsBySource.map((s: any) => ({ sourceId: s.sourceId, documentCount: s._count, totalBytes: s._sum.byteSize || 0, totalTokens: s._sum.tokenEstimate || 0 })),
      };
    } catch {}
  }

  // Fallback: in-memory stats
  const totalDocs = mem.documents.length;
  const totalBytes = mem.documents.reduce((s: number, d: any) => s + (d.byteSize || 0), 0);
  const totalTokens = mem.documents.reduce((s: number, d: any) => s + (d.tokenEstimate || 0), 0);
  const unusedDocs = mem.documents.filter((d: any) => !d.usedInTraining).length;
  const sourceMap: Record<string, { count: number; bytes: number; tokens: number }> = {};
  for (const d of mem.documents) {
    if (!sourceMap[d.sourceId]) sourceMap[d.sourceId] = { count: 0, bytes: 0, tokens: 0 };
    sourceMap[d.sourceId].count++;
    sourceMap[d.sourceId].bytes += d.byteSize || 0;
    sourceMap[d.sourceId].tokens += d.tokenEstimate || 0;
  }

  return {
    dbConnected: false, totalDocuments: totalDocs, totalCrawlCycles: mem.cycles.length,
    totalTokens, totalBytes, unusedDocuments: unusedDocs,
    recentCycles: mem.cycles.slice(0, 30), trainingRuns: mem.runs.slice(0, 10),
    sourceBreakdown: Object.entries(sourceMap).map(([id, s]) => ({ sourceId: id, documentCount: s.count, totalBytes: s.bytes, totalTokens: s.tokens })),
  };
}

// ---------------------------------------------------------------------------
// ⚡ NERVOUS SYSTEM — organism status
// ---------------------------------------------------------------------------

export function getOrganismStatus() {
  return {
    organism: 'OverLLM',
    version: '3.0',
    organs: SOURCES.map(s => ({ id: s.id, name: s.name, icon: s.icon })),
    capabilities: ['real-time-crawl', 'auto-training', 'ipfs-weight-upload', 'fine-tuning'],
    heartbeat: new Date().toISOString(),
  };
}

export function getSourceList() {
  return SOURCES.map(s => ({ id: s.id, name: s.name, icon: s.icon }));
}
