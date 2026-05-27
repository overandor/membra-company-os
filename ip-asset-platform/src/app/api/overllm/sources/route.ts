import { NextResponse } from 'next/server';
import { getSourceList } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({ success: true, sources: getSourceList() });
}
