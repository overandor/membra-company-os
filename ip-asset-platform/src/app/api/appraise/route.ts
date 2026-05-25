import { NextRequest, NextResponse } from 'next/server';
import { appraiseFileWithCloudLLM, getCloudLLMStatus } from '@/lib/cloud-llm';
import { computeFileDNAHash } from '@/lib/cloud-storage';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filePath, fileContent, metadata, llmModel = 'gpt-4' } = body;

    if (!fileContent) {
      return NextResponse.json(
        { error: 'File content is required for cloud deployment' },
        { status: 400 }
      );
    }

    // Check cloud LLM status
    const llmStatus = await getCloudLLMStatus();
    if (!llmStatus.available) {
      return NextResponse.json(
        { error: 'Cloud LLM service is not configured. Please set OPENAI_API_KEY environment variable.' },
        { status: 503 }
      );
    }

    // Compute file DNA hash
    const dnaHash = await computeFileDNAHash(fileContent);
    
    // Appraise file using cloud LLM
    const appraisal = await appraiseFileWithCloudLLM(filePath || 'unknown', fileContent, metadata || {});

    const result = {
      id: `appraisal_${Date.now()}`,
      fileId: Buffer.from(filePath || 'unknown').toString('base64'),
      llmModel: llmStatus.model,
      llmProvider: llmStatus.provider,
      appraisalType: 'FILE',
      appraisal: {
        content_quality_score: appraisal.content_quality_score,
        market_demand_score: appraisal.market_demand_score,
        technical_merit_score: appraisal.technical_merit_score,
        usage_frequency_score: appraisal.usage_frequency_score,
        estimated_value_usd: appraisal.estimated_value_usd,
        notes: appraisal.notes,
        overall_score: appraisal.overall_score
      },
      dnaHash,
      appraisalTimestamp: new Date().toISOString()
    };

    return NextResponse.json({ 
      success: true, 
      appraisal: result 
    });
  } catch (error) {
    console.error('Appraisal error:', error);
    return NextResponse.json(
      { error: `Failed to perform appraisal: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const llmStatus = await getCloudLLMStatus();
    
    return NextResponse.json({ 
      llmStatus 
    });
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to get LLM status: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}