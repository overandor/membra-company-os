import { NextResponse } from 'next/server';
import { getOrganismStatus } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({ success: true, ...getOrganismStatus() });
}
