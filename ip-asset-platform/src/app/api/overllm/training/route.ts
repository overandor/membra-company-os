import { NextRequest, NextResponse } from 'next/server';
import { runCrawl } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';
export const maxDuration = 30;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const { sourceIds } = body as { sourceIds?: string[] };
    const snapshot = await runCrawl(sourceIds);
    return NextResponse.json({ success: true, snapshot });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
