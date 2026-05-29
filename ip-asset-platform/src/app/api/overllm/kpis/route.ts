import { NextResponse } from 'next/server';
import { getDashboardStats } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const stats = await getDashboardStats();
    return NextResponse.json({ success: true, stats });
  } catch (error) {
    return NextResponse.json(
      { error: `KPI fetch failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}
