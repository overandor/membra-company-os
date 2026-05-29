import { NextRequest, NextResponse } from 'next/server';
import { runCrawlCycle } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';
export const maxDuration = 30;

/**
 * Vercel Cron endpoint — called every minute to crawl all sources
 * and store documents in PostgreSQL. Auto-triggers training when
 * enough unused documents accumulate.
 */
export async function GET(request: NextRequest) {
  // Verify cron secret (Vercel sets this header for cron jobs)
  const authHeader = request.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const snapshot = await runCrawlCycle();
    return NextResponse.json({ success: true, snapshot });
  } catch (error) {
    return NextResponse.json(
      { error: `Crawl cycle failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}
