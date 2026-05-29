/**
 * OverLLM Persistent Crawling & Training Engine
 * Crawls real public APIs, stores in PostgreSQL, triggers OpenAI fine-tuning.
 * Designed to run 24/7 via Vercel Cron.
 */

import { PrismaClient } from '@prisma/client';
import crypto from 'crypto';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };
const prisma = globalForPrisma.prisma || new PrismaClient();
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;

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

interface RawDoc {
  title: string;
  content: string;
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function fetchJson(url: string, timeout = 12000): Promise<any> {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), timeout);
  try {
    const r = await fetch(url, { signal: c.signal, headers: { 'User-Agent': 'OverLLM-Crawler/2.0' } });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } finally { clearTimeout(t); }
}

async function fetchText(url: string, timeout = 12000): Promise<string> {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), timeout);
  try {
    const r = await fetch(url, { signal: c.signal, headers: { 'User-Agent': 'OverLLM-Crawler/2.0' } });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.text();
  } finally { clearTimeout(t); }
}

function contentHash(text: string): string {
  return crypto.createHash('sha256').update(text).digest('hex');
}

// ---------------------------------------------------------------------------
// Source crawlers — each returns raw documents
// ---------------------------------------------------------------------------

const SOURCES: { id: string; name: string; crawl: () => Promise<RawDoc[]> }[] = [
  {
    id: 'wikipedia',
    name: 'Wikipedia (Random Articles)',
    crawl: async () => {
      const docs: RawDoc[] = [];
      for (let i = 0; i < 5; i++) {
        try {
          const d = await fetchJson('https://en.wikipedia.org/api/rest_v1/page/random/summary');
          if (d.extract) docs.push({ title: d.title || 'Untitled', content: d.extract });
        } catch { /* skip */ }
      }
      return docs;
    },
  },
  {
    id: 'arxiv',
    name: 'arXiv (CS/AI Papers)',
    crawl: async () => {
      const xml = await fetchText(
        'https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10'
      );
      const entries = [...xml.matchAll(/<entry>([\s\S]*?)<\/entry>/g)];
      return entries.map(e => {
        const title = e[1].match(/<title>([\s\S]*?)<\/title>/)?.[1]?.trim() || 'Untitled';
        const summary = e[1].match(/<summary>([\s\S]*?)<\/summary>/)?.[1]?.trim() || '';
        return { title, content: `${title}\n\n${summary}` };
      });
    },
  },
  {
    id: 'hackernews',
    name: 'Hacker News (Top Stories)',
    crawl: async () => {
      const ids: number[] = await fetchJson('https://hacker-news.firebaseio.com/v0/topstories.json');
      const docs: RawDoc[] = [];
      await Promise.all(ids.slice(0, 10).map(async (id) => {
        try {
          const item = await fetchJson(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
          if (item?.title) {
            const content = [item.title, item.text || '', item.url || ''].filter(Boolean).join('\n');
            docs.push({ title: item.title, content });
          }
        } catch { /* skip */ }
      }));
      return docs;
    },
  },
  {
    id: 'gutenberg',
    name: 'Project Gutenberg (Books)',
    crawl: async () => {
      const data = await fetchJson('https://gutendex.com/books/?languages=en&sort=popular&page=1');
      return (data.results || []).slice(0, 10).map((b: any) => ({
        title: b.title,
        content: `${b.title} by ${(b.authors || []).map((a: any) => a.name).join(', ')}. Subjects: ${(b.subjects || []).join(', ')}`,
      }));
    },
  },
  {
    id: 'pubmed',
    name: 'PubMed (Medical Abstracts)',
    crawl: async () => {
      const search = await fetchJson(
        'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=10&sort=date&term=machine+learning'
      );
      const ids: string[] = search?.esearchresult?.idlist || [];
      if (!ids.length) return [];
      const summary = await fetchJson(
        `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=${ids.join(',')}`
      );
      const docs: RawDoc[] = [];
      for (const id of ids) {
        const a = summary?.result?.[id];
        if (a?.title) docs.push({ title: a.title, content: JSON.stringify(a) });
      }
      return docs;
    },
  },
  {
    id: 'github-trending',
    name: 'GitHub (Trending Repos)',
    crawl: async () => {
      const data = await fetchJson(
        'https://api.github.com/search/repositories?q=stars:>100+language:python&sort=updated&per_page=10'
      );
      return (data.items || []).map((r: any) => ({
        title: r.full_name,
        content: `${r.full_name}: ${r.description || 'No description'}. Stars: ${r.stargazers_count}. Language: ${r.language || 'Unknown'}. Topics: ${(r.topics || []).join(', ')}`,
      }));
    },
  },
  {
    id: 'stackexchange',
    name: 'StackOverflow (Top Questions)',
    crawl: async () => {
      const data = await fetchJson(
        'https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow&pagesize=10&filter=withbody'
      );
      return (data.items || []).map((q: any) => ({
        title: q.title,
        content: `Q: ${q.title}\n\n${q.body || ''}`,
      }));
    },
  },
  {
    id: 'openlibrary',
    name: 'Open Library (Book Metadata)',
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
// Core: run a full crawl cycle, persist every document to PostgreSQL
// ---------------------------------------------------------------------------

export async function runCrawlCycle(): Promise<CrawlSnapshot> {
  const cycleStart = Date.now();

  const cycle = await prisma.crawlCycle.create({ data: { status: 'running' } });

  const results: CrawlResult[] = await Promise.all(
    SOURCES.map(async (source): Promise<CrawlResult> => {
      const t0 = Date.now();
      try {
        const rawDocs = await source.crawl();
        let bytesCollected = 0;
        let tokensEstimated = 0;
        let stored = 0;
        const titles: string[] = [];

        for (const doc of rawDocs) {
          const ch = contentHash(doc.content);
          const byteSize = Buffer.byteLength(doc.content, 'utf8');
          const tokenEst = Math.round(byteSize / 4);

          try {
            await prisma.crawlDocument.create({
              data: {
                sourceId: source.id,
                sourceName: source.name,
                title: doc.title.slice(0, 500),
                content: doc.content,
                contentHash: ch,
                byteSize,
                tokenEstimate: tokenEst,
              },
            });
            stored++;
          } catch (e: any) {
            if (!e.code || e.code !== 'P2002') throw e;
            // duplicate — already have this content
          }

          bytesCollected += byteSize;
          tokensEstimated += tokenEst;
          titles.push(doc.title);
        }

        return {
          sourceId: source.id, sourceName: source.name, status: 'success',
          documentsCollected: stored, bytesCollected, tokensEstimated,
          crawlTimeMs: Date.now() - t0, sampleTitles: titles.slice(0, 5),
        };
      } catch (err) {
        return {
          sourceId: source.id, sourceName: source.name, status: 'error',
          documentsCollected: 0, bytesCollected: 0, tokensEstimated: 0,
          crawlTimeMs: Date.now() - t0, sampleTitles: [],
          error: err instanceof Error ? err.message : String(err),
        };
      }
    })
  );

  const totalDocs = results.reduce((s, r) => s + r.documentsCollected, 0);
  const totalBytes = results.reduce((s, r) => s + r.bytesCollected, 0);
  const totalTokens = results.reduce((s, r) => s + r.tokensEstimated, 0);
  const succeeded = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'error').length;
  const elapsed = Date.now() - cycleStart;

  await prisma.crawlCycle.update({
    where: { id: cycle.id },
    data: {
      completedAt: new Date(), totalDocuments: totalDocs, totalBytes, totalTokens: totalTokens,
      sourcesSucceeded: succeeded, sourcesFailed: failed, crawlTimeMs: elapsed,
      sourceResults: JSON.parse(JSON.stringify(results)), status: 'completed',
    },
  });

  // Auto-trigger training if enough unused docs
  const unusedCount = await prisma.crawlDocument.count({ where: { usedInTraining: false } });
  const activeTraining = await prisma.overLLMTrainingRun.count({ where: { status: { in: ['preparing', 'training'] } } });
  if (unusedCount >= 100 && activeTraining === 0) {
    try { await triggerTraining(); } catch { /* log but don't fail crawl */ }
  }

  return {
    cycleId: cycle.id, timestamp: new Date().toISOString(),
    totalDocuments: totalDocs, totalBytes, totalTokensEstimated: totalTokens,
    totalCrawlTimeMs: elapsed, sourcesSucceeded: succeeded, sourcesFailed: failed,
    sources: results,
  };
}

// ---------------------------------------------------------------------------
// Training: build JSONL from unused docs, upload to OpenAI, start fine-tune
// ---------------------------------------------------------------------------

export async function triggerTraining(): Promise<{
  runId: string; documentsUsed: number; tokensUsed: number;
  finetunJobId?: string; status: string; message: string;
}> {
  const apiKey = process.env.OPENAI_API_KEY;

  const docs = await prisma.crawlDocument.findMany({
    where: { usedInTraining: false },
    orderBy: { crawledAt: 'asc' },
    take: 500,
  });

  if (docs.length < 10) {
    return { runId: '', documentsUsed: 0, tokensUsed: 0, status: 'waiting',
      message: `Only ${docs.length} unused docs. Need at least 10.` };
  }

  const run = await prisma.overLLMTrainingRun.create({
    data: {
      status: 'preparing',
      documentsUsed: docs.length,
      tokensUsed: docs.reduce((s, d) => s + d.tokenEstimate, 0),
    },
  });

  // Build JSONL
  const jsonlLines = docs.map(doc => JSON.stringify({
    messages: [
      { role: 'system', content: 'You are OverLLM, a knowledgeable AI trained on diverse real-world data.' },
      { role: 'user', content: `Tell me about: ${doc.title}` },
      { role: 'assistant', content: doc.content },
    ],
  }));
  const jsonlContent = jsonlLines.join('\n');

  await prisma.crawlDocument.updateMany({
    where: { id: { in: docs.map(d => d.id) } },
    data: { usedInTraining: true, trainingRunId: run.id },
  });

  if (!apiKey || apiKey === 'your-openai-api-key') {
    await prisma.overLLMTrainingRun.update({
      where: { id: run.id },
      data: { status: 'data_ready', errorMessage: 'OPENAI_API_KEY not set. JSONL ready but fine-tune not submitted.' },
    });
    return { runId: run.id, documentsUsed: docs.length,
      tokensUsed: docs.reduce((s, d) => s + d.tokenEstimate, 0),
      status: 'data_ready', message: `${docs.length} docs ready. Set OPENAI_API_KEY to fine-tune.` };
  }

  try {
    const formData = new FormData();
    formData.append('purpose', 'fine-tune');
    formData.append('file', new Blob([jsonlContent], { type: 'application/jsonl' }), 'overllm-training.jsonl');

    const uploadRes = await fetch('https://api.openai.com/v1/files', {
      method: 'POST', headers: { 'Authorization': `Bearer ${apiKey}` }, body: formData,
    });
    const uploadData = await uploadRes.json();
    if (!uploadRes.ok) throw new Error(`Upload failed: ${JSON.stringify(uploadData)}`);

    const ftRes = await fetch('https://api.openai.com/v1/fine_tuning/jobs', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        training_file: uploadData.id, model: 'gpt-4o-mini-2024-07-18',
        hyperparameters: { n_epochs: 3 }, suffix: 'overllm',
      }),
    });
    const ftData = await ftRes.json();
    if (!ftRes.ok) throw new Error(`Fine-tune failed: ${JSON.stringify(ftData)}`);

    await prisma.overLLMTrainingRun.update({
      where: { id: run.id },
      data: { status: 'training', finetunJobId: ftData.id, trainingFileId: uploadData.id, baseModel: 'gpt-4o-mini-2024-07-18' },
    });

    return { runId: run.id, documentsUsed: docs.length,
      tokensUsed: docs.reduce((s, d) => s + d.tokenEstimate, 0),
      finetunJobId: ftData.id, status: 'training',
      message: `Fine-tuning started. Job: ${ftData.id}` };
  } catch (err) {
    await prisma.overLLMTrainingRun.update({
      where: { id: run.id },
      data: { status: 'failed', errorMessage: err instanceof Error ? err.message : String(err) },
    });
    throw err;
  }
}

// ---------------------------------------------------------------------------
// Dashboard stats from PostgreSQL
// ---------------------------------------------------------------------------

export async function getDashboardStats() {
  const [totalDocs, totalCycles, recentCycles, trainingRuns, docsBySource, aggTokens, aggBytes, unusedDocs] = await Promise.all([
    prisma.crawlDocument.count(),
    prisma.crawlCycle.count(),
    prisma.crawlCycle.findMany({ orderBy: { startedAt: 'desc' }, take: 30 }),
    prisma.overLLMTrainingRun.findMany({ orderBy: { startedAt: 'desc' }, take: 10 }),
    prisma.crawlDocument.groupBy({ by: ['sourceId'], _count: true, _sum: { byteSize: true, tokenEstimate: true } }),
    prisma.crawlDocument.aggregate({ _sum: { tokenEstimate: true } }),
    prisma.crawlDocument.aggregate({ _sum: { byteSize: true } }),
    prisma.crawlDocument.count({ where: { usedInTraining: false } }),
  ]);

  return {
    totalDocuments: totalDocs,
    totalCrawlCycles: totalCycles,
    totalTokens: aggTokens._sum.tokenEstimate || 0,
    totalBytes: aggBytes._sum.byteSize || 0,
    unusedDocuments: unusedDocs,
    recentCycles,
    trainingRuns,
    sourceBreakdown: docsBySource.map(s => ({
      sourceId: s.sourceId, documentCount: s._count,
      totalBytes: s._sum.byteSize || 0, totalTokens: s._sum.tokenEstimate || 0,
    })),
  };
}

export function getSourceList() {
  return SOURCES.map(s => ({ id: s.id, name: s.name }));
}
