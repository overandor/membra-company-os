import { NextRequest, NextResponse } from 'next/server';
import { callOpenAI, getCloudLLMStatus } from '@/lib/cloud-llm';

/**
 * Cloud Inference API
 * Optimized for Vercel serverless deployment
 */

export const runtime = 'edge';
export const maxDuration = 30;

interface InferenceRequest {
  prompt: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
}

interface InferenceResponse {
  content: string;
  model: string;
  tokensUsed: number;
  costUsd: number;
  processingTimeMs: number;
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    const body: InferenceRequest = await request.json();
    const { prompt, model, maxTokens = 1000, temperature = 0.7, systemPrompt } = body;

    if (!prompt) {
      return NextResponse.json(
        { error: 'Prompt is required' },
        { status: 400 }
      );
    }

    // Check cloud LLM status
    const llmStatus = await getCloudLLMStatus();
    if (!llmStatus.available) {
      return NextResponse.json(
        { error: 'Cloud LLM service is not configured' },
        { status: 503 }
      );
    }

    // Prepare the full prompt with system instruction if provided
    let fullPrompt = prompt;
    if (systemPrompt) {
      fullPrompt = `${systemPrompt}\n\n${prompt}`;
    }

    // Call the LLM
    const response = await callOpenAI({
      prompt: fullPrompt,
      model: model || llmStatus.model,
      maxTokens,
      temperature
    });

    const processingTimeMs = Date.now() - startTime;

    const result: InferenceResponse = {
      content: response.content,
      model: response.model,
      tokensUsed: response.tokensUsed,
      costUsd: response.costUsd,
      processingTimeMs
    };

    return NextResponse.json({ 
      success: true, 
      inference: result 
    });
  } catch (error) {
    console.error('Inference error:', error);
    return NextResponse.json(
      { error: `Inference failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const llmStatus = await getCloudLLMStatus();
    
    return NextResponse.json({ 
      status: 'operational',
      llm: llmStatus,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return NextResponse.json(
      { error: `Status check failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}