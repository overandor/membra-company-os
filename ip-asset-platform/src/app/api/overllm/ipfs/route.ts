import { NextRequest, NextResponse } from 'next/server';
import { uploadWeightsToIPFS } from '@/lib/overllm-training';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const result = await uploadWeightsToIPFS(body);
    return NextResponse.json({ success: true, ...result });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status: 500 });
  }
}
