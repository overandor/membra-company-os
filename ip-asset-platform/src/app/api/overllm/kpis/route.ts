import { NextRequest, NextResponse } from 'next/server';
import { runCrawl, getSourceList } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';
export const maxDuration = 30;

export async function GET(request: NextRequest) {
  try {
    const snapshot = await runCrawl();
    return NextResponse.json({ success: true, snapshot });
  } catch (error) {
    return NextResponse.json(
      { error: `Crawl failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}
