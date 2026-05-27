/**
 * OverLLM Real Crawling Engine
 * Actually fetches data from public APIs and aggregates results.
 */

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
  timestamp: string;
  totalDocuments: number;
  totalBytes: number;
  totalTokensEstimated: number;
  totalCrawlTimeMs: number;
  sourcesSucceeded: number;
  sourcesFailed: number;
  sources: CrawlResult[];
}

interface SourceDef {
  id: string;
  name: string;
  crawl: () => Promise<{ documents: number; bytes: number; titles: string[] }>;
}

async function fetchJson(url: string, timeout = 10000): Promise<any> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': 'OverLLM-Crawler/1.0' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

async function fetchText(url: string, timeout = 10000): Promise<string> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': 'OverLLM-Crawler/1.0' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(timer);
  }
}

const SOURCES: SourceDef[] = [
  {
    id: 'wikipedia',
    name: 'Wikipedia (Random Articles)',
    crawl: async () => {
      const titles: string[] = [];
      let totalBytes = 0;
      let docs = 0;
      // Fetch 5 random articles
      for (let i = 0; i < 5; i++) {
        try {
          const data = await fetchJson('https://en.wikipedia.org/api/rest_v1/page/random/summary');
          titles.push(data.title || 'Untitled');
          const text = data.extract || '';
          totalBytes += new TextEncoder().encode(text).length;
          docs++;
        } catch { /* skip */ }
      }
      return { documents: docs, bytes: totalBytes, titles };
    },
  },
  {
    id: 'arxiv',
    name: 'arXiv (CS/AI Papers)',
    crawl: async () => {
      const xml = await fetchText(
        'https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10'
      );
      const titleMatches = [...xml.matchAll(/<title>([\s\S]*?)<\/title>/g)];
      const summaryMatches = [...xml.matchAll(/<summary>([\s\S]*?)<\/summary>/g)];
      const titles = titleMatches.slice(1).map(m => m[1].trim()).slice(0, 10);
      let totalBytes = 0;
      for (const m of summaryMatches) {
        totalBytes += new TextEncoder().encode(m[1]).length;
      }
      return { documents: titles.length, bytes: totalBytes, titles };
    },
  },
  {
    id: 'hackernews',
    name: 'Hacker News (Top Stories)',
    crawl: async () => {
      const ids: number[] = await fetchJson('https://hacker-news.firebaseio.com/v0/topstories.json');
      const topIds = ids.slice(0, 10);
      const titles: string[] = [];
      let totalBytes = 0;
      let docs = 0;
      await Promise.all(
        topIds.map(async (id) => {
          try {
            const item = await fetchJson(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
            if (item?.title) {
              titles.push(item.title);
              const text = JSON.stringify(item);
              totalBytes += new TextEncoder().encode(text).length;
              docs++;
            }
          } catch { /* skip */ }
        })
      );
      return { documents: docs, bytes: totalBytes, titles };
    },
  },
  {
    id: 'gutenberg',
    name: 'Project Gutenberg (Books)',
    crawl: async () => {
      const data = await fetchJson('https://gutendex.com/books/?languages=en&sort=popular&page=1');
      const books = data.results || [];
      const titles = books.map((b: any) => b.title).slice(0, 10);
      const totalBytes = new TextEncoder().encode(JSON.stringify(books)).length;
      return { documents: books.length, bytes: totalBytes, titles };
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
      if (ids.length === 0) return { documents: 0, bytes: 0, titles: [] };
      const summaryUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=${ids.join(',')}`;
      const summary = await fetchJson(summaryUrl);
      const titles: string[] = [];
      let totalBytes = 0;
      for (const id of ids) {
        const article = summary?.result?.[id];
        if (article?.title) {
          titles.push(article.title);
          totalBytes += new TextEncoder().encode(JSON.stringify(article)).length;
        }
      }
      return { documents: titles.length, bytes: totalBytes, titles };
    },
  },
  {
    id: 'github-trending',
    name: 'GitHub (Trending Repos)',
    crawl: async () => {
      const data = await fetchJson(
        'https://api.github.com/search/repositories?q=stars:>100+language:python&sort=updated&per_page=10'
      );
      const repos = data.items || [];
      const titles = repos.map((r: any) => `${r.full_name}: ${r.description || ''}`).slice(0, 10);
      const totalBytes = new TextEncoder().encode(JSON.stringify(repos)).length;
      return { documents: repos.length, bytes: totalBytes, titles };
    },
  },
  {
    id: 'stackexchange',
    name: 'StackOverflow (Top Questions)',
    crawl: async () => {
      const data = await fetchJson(
        'https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow&pagesize=10&filter=withbody'
      );
      const questions = data.items || [];
      const titles = questions.map((q: any) => q.title).slice(0, 10);
      let totalBytes = 0;
      for (const q of questions) {
        totalBytes += new TextEncoder().encode(q.body || q.title || '').length;
      }
      return { documents: questions.length, bytes: totalBytes, titles };
    },
  },
  {
    id: 'openlibrary',
    name: 'Open Library (Book Metadata)',
    crawl: async () => {
      const data = await fetchJson('https://openlibrary.org/subjects/science.json?limit=10');
      const works = data.works || [];
      const titles = works.map((w: any) => w.title).slice(0, 10);
      const totalBytes = new TextEncoder().encode(JSON.stringify(works)).length;
      return { documents: works.length, bytes: totalBytes, titles };
    },
  },
];

/**
 * Run a real crawl across all enabled sources in parallel.
 * Each source makes real HTTP requests to public APIs.
 */
export async function runCrawl(enabledSourceIds?: string[]): Promise<CrawlSnapshot> {
  const startTime = Date.now();
  const activeSources = enabledSourceIds
    ? SOURCES.filter(s => enabledSourceIds.includes(s.id))
    : SOURCES;

  const results: CrawlResult[] = await Promise.all(
    activeSources.map(async (source): Promise<CrawlResult> => {
      const t0 = Date.now();
      try {
        const { documents, bytes, titles } = await source.crawl();
        return {
          sourceId: source.id,
          sourceName: source.name,
          status: 'success',
          documentsCollected: documents,
          bytesCollected: bytes,
          tokensEstimated: Math.round(bytes / 4), // ~4 bytes per token
          crawlTimeMs: Date.now() - t0,
          sampleTitles: titles.slice(0, 5),
        };
      } catch (err) {
        return {
          sourceId: source.id,
          sourceName: source.name,
          status: 'error',
          documentsCollected: 0,
          bytesCollected: 0,
          tokensEstimated: 0,
          crawlTimeMs: Date.now() - t0,
          sampleTitles: [],
          error: err instanceof Error ? err.message : String(err),
        };
      }
    })
  );

  const totalDocuments = results.reduce((s, r) => s + r.documentsCollected, 0);
  const totalBytes = results.reduce((s, r) => s + r.bytesCollected, 0);
  const totalTokens = results.reduce((s, r) => s + r.tokensEstimated, 0);

  return {
    timestamp: new Date().toISOString(),
    totalDocuments,
    totalBytes,
    totalTokensEstimated: totalTokens,
    totalCrawlTimeMs: Date.now() - startTime,
    sourcesSucceeded: results.filter(r => r.status === 'success').length,
    sourcesFailed: results.filter(r => r.status === 'error').length,
    sources: results,
  };
}

export function getSourceList() {
  return SOURCES.map(s => ({ id: s.id, name: s.name }));
}
