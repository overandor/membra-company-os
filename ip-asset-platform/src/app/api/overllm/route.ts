import { NextRequest, NextResponse } from 'next/server';
import { callOpenAI, getCloudLLMStatus } from '@/lib/cloud-llm';

/**
 * OverLLM API - Advanced LLM Orchestration
 * Provides multi-step reasoning, chain-of-thought, and advanced inference
 */

export const runtime = 'edge';
export const maxDuration = 60;

interface OverLLMRequest {
  task: string;
  context?: string;
  reasoningType?: 'chain-of-thought' | 'tree-of-thoughts' | 'multi-step' | 'single-shot';
  complexity?: 'low' | 'medium' | 'high';
  outputFormat?: 'json' | 'text' | 'structured';
  maxSteps?: number;
}

interface OverLLMResponse {
  result: any;
  reasoning: string[];
  steps: any[];
  tokensUsed: number;
  costUsd: number;
  processingTimeMs: number;
  model: string;
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    const body: OverLLMRequest = await request.json();
    const { 
      task, 
      context = '', 
      reasoningType = 'chain-of-thought',
      complexity = 'medium',
      outputFormat = 'json',
      maxSteps = 5 
    } = body;

    if (!task) {
      return NextResponse.json(
        { error: 'Task is required' },
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

    let result: OverLLMResponse;
    let totalTokensUsed = 0;
    let totalCostUsd = 0;
    const reasoning: string[] = [];
    const steps: any[] = [];

    switch (reasoningType) {
      case 'chain-of-thought':
        result = await chainOfThought(task, context, complexity, outputFormat, llmStatus.model);
        break;
      case 'tree-of-thoughts':
        result = await treeOfThoughts(task, context, complexity, outputFormat, maxSteps, llmStatus.model);
        break;
      case 'multi-step':
        result = await multiStepReasoning(task, context, complexity, outputFormat, maxSteps, llmStatus.model);
        break;
      case 'single-shot':
      default:
        result = await singleShot(task, context, outputFormat, llmStatus.model);
        break;
    }

    const processingTimeMs = Date.now() - startTime;

    return NextResponse.json({ 
      success: true, 
      overllm: {
        ...result,
        processingTimeMs,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('OverLLM error:', error);
    return NextResponse.json(
      { error: `OverLLM failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}

async function chainOfThought(
  task: string, 
  context: string, 
  complexity: string, 
  outputFormat: string,
  model: string
): Promise<OverLLMResponse> {
  const startTime = Date.now();
  
  const systemPrompt = `You are an expert reasoning system. Think step-by-step and explain your reasoning process. ${complexity === 'high' ? 'Consider multiple perspectives and edge cases.' : ''}`;
  
  const prompt = `Task: ${task}\nContext: ${context}\n\nPlease think through this step-by-step and provide your final answer in ${outputFormat} format.`;

  const response = await callOpenAI({
    prompt,
    model,
    maxTokens: complexity === 'high' ? 2000 : 1000,
    temperature: 0.7
  });

  return {
    result: parseOutput(response.content, outputFormat),
    reasoning: [response.content],
    steps: [{ type: 'chain-of-thought', content: response.content }],
    tokensUsed: response.tokensUsed,
    costUsd: response.costUsd,
    processingTimeMs: Date.now() - startTime,
    model: response.model
  };
}

async function treeOfThoughts(
  task: string, 
  context: string, 
  complexity: string, 
  outputFormat: string,
  maxSteps: number,
  model: string
): Promise<OverLLMResponse> {
  const startTime = Date.now();
  const reasoning: string[] = [];
  const steps: any[] = [];
  let totalTokensUsed = 0;
  let totalCostUsd = 0;

  // Generate initial thoughts
  const thoughtsPrompt = `Task: ${task}\nContext: ${context}\n\nGenerate 3-5 different approaches or perspectives to solve this task. Be creative and diverse.`;
  
  const thoughtsResponse = await callOpenAI({
    prompt: thoughtsPrompt,
    model,
    maxTokens: 1000,
    temperature: 0.8
  });

  reasoning.push(thoughtsResponse.content);
  steps.push({ type: 'thought-generation', content: thoughtsResponse.content });
  totalTokensUsed += thoughtsResponse.tokensUsed;
  totalCostUsd += thoughtsResponse.costUsd;

  // Evaluate and select best approach
  const evaluationPrompt = `Task: ${task}\n\nPossible approaches:\n${thoughtsResponse.content}\n\nEvaluate these approaches and select the best one. Explain your reasoning.`;
  
  const evaluationResponse = await callOpenAI({
    prompt: evaluationPrompt,
    model,
    maxTokens: 1000,
    temperature: 0.5
  });

  reasoning.push(evaluationResponse.content);
  steps.push({ type: 'evaluation', content: evaluationResponse.content });
  totalTokensUsed += evaluationResponse.tokensUsed;
  totalCostUsd += evaluationResponse.costUsd;

  // Generate final solution
  const solutionPrompt = `Task: ${task}\nContext: ${context}\n\nSelected approach: ${evaluationResponse.content}\n\nBased on this approach, provide the final solution in ${outputFormat} format.`;
  
  const solutionResponse = await callOpenAI({
    prompt: solutionPrompt,
    model,
    maxTokens: 1500,
    temperature: 0.6
  });

  reasoning.push(solutionResponse.content);
  steps.push({ type: 'solution', content: solutionResponse.content });
  totalTokensUsed += solutionResponse.tokensUsed;
  totalCostUsd += solutionResponse.costUsd;

  return {
    result: parseOutput(solutionResponse.content, outputFormat),
    reasoning,
    steps,
    tokensUsed: totalTokensUsed,
    costUsd: totalCostUsd,
    processingTimeMs: Date.now() - startTime,
    model
  };
}

async function multiStepReasoning(
  task: string, 
  context: string, 
  complexity: string, 
  outputFormat: string,
  maxSteps: number,
  model: string
): Promise<OverLLMResponse> {
  const startTime = Date.now();
  const reasoning: string[] = [];
  const steps: any[] = [];
  let totalTokensUsed = 0;
  let totalCostUsd = 0;

  let currentContext = context;
  const actualSteps = Math.min(maxSteps, 5); // Limit to 5 steps max

  for (let i = 0; i < actualSteps; i++) {
    const stepPrompt = `Task: ${task}\nStep ${i + 1}/${actualSteps}\nContext: ${currentContext}\n\nWhat should be done in this step? Provide your analysis and action.`;
    
    const stepResponse = await callOpenAI({
      prompt: stepPrompt,
      model,
      maxTokens: 800,
      temperature: 0.7
    });

    reasoning.push(`Step ${i + 1}: ${stepResponse.content}`);
    steps.push({ step: i + 1, content: stepResponse.content });
    totalTokensUsed += stepResponse.tokensUsed;
    totalCostUsd += stepResponse.costUsd;

    currentContext += `\n\nStep ${i + 1} result: ${stepResponse.content}`;
  }

  // Generate final answer
  const finalPrompt = `Task: ${task}\n\nCompleted steps:\n${reasoning.join('\n')}\n\nBased on these steps, provide the final answer in ${outputFormat} format.`;
  
  const finalResponse = await callOpenAI({
    prompt: finalPrompt,
    model,
    maxTokens: 1500,
    temperature: 0.6
  });

  reasoning.push(`Final Answer: ${finalResponse.content}`);
  steps.push({ type: 'final', content: finalResponse.content });
  totalTokensUsed += finalResponse.tokensUsed;
  totalCostUsd += finalResponse.costUsd;

  return {
    result: parseOutput(finalResponse.content, outputFormat),
    reasoning,
    steps,
    tokensUsed: totalTokensUsed,
    costUsd: totalCostUsd,
    processingTimeMs: Date.now() - startTime,
    model
  };
}

async function singleShot(
  task: string, 
  context: string, 
  outputFormat: string,
  model: string
): Promise<OverLLMResponse> {
  const startTime = Date.now();
  
  const prompt = `Task: ${task}\nContext: ${context}\n\nProvide a direct answer in ${outputFormat} format.`;

  const response = await callOpenAI({
    prompt,
    model,
    maxTokens: 1000,
    temperature: 0.7
  });

  return {
    result: parseOutput(response.content, outputFormat),
    reasoning: [`Direct answer: ${response.content}`],
    steps: [{ type: 'single-shot', content: response.content }],
    tokensUsed: response.tokensUsed,
    costUsd: response.costUsd,
    processingTimeMs: Date.now() - startTime,
    model: response.model
  };
}

function parseOutput(content: string, format: string): any {
  try {
    if (format === 'json') {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    }
    return content;
  } catch {
    return content;
  }
}

export async function GET(request: NextRequest) {
  try {
    const llmStatus = await getCloudLLMStatus();
    
    return NextResponse.json({ 
      status: 'operational',
      service: 'overllm',
      capabilities: {
        reasoningTypes: ['chain-of-thought', 'tree-of-thoughts', 'multi-step', 'single-shot'],
        complexityLevels: ['low', 'medium', 'high'],
        outputFormats: ['json', 'text', 'structured']
      },
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