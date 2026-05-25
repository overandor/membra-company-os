/**
 * Cloud LLM Service
 * Provides integration with cloud LLM providers (OpenAI, Anthropic, etc.)
 */

interface LLMRequest {
  prompt: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

interface LLMResponse {
  content: string;
  model: string;
  tokensUsed: number;
  costUsd: number;
}

interface LLMAppraisal {
  content_quality_score: number;
  market_demand_score: number;
  technical_merit_score: number;
  usage_frequency_score: number;
  estimated_value_usd: number;
  notes: string;
  overall_score: number;
}

const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

/**
 * Call OpenAI API for LLM operations
 */
export async function callOpenAI(request: LLMRequest): Promise<LLMResponse> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY environment variable is not set');
  }

  const model = request.model || process.env.LLM_MODEL || 'gpt-4';
  const maxTokens = request.maxTokens || 1000;
  const temperature = request.temperature || 0.7;

  try {
    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: 'system',
            content: 'You are an expert file analyst and IP asset appraiser. Provide detailed, accurate assessments.'
          },
          {
            role: 'user',
            content: request.prompt
          }
        ],
        max_tokens: maxTokens,
        temperature,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`OpenAI API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const content = data.choices[0].message.content;
    const tokensUsed = data.usage.total_tokens;

    // Calculate cost (approximate GPT-4 pricing)
    const costPerToken = 0.00003; // ~$0.03 per 1K tokens
    const costUsd = tokensUsed * costPerToken;

    return {
      content,
      model,
      tokensUsed,
      costUsd
    };
  } catch (error) {
    console.error('Error calling OpenAI:', error);
    throw new Error(`Failed to call OpenAI: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Appraise a file using cloud LLM
 */
export async function appraiseFileWithCloudLLM(
  filePath: string,
  fileContent: string,
  metadata: any
): Promise<LLMAppraisal> {
  const prompt = `
Analyze this file for IP asset valuation:

File Path: ${filePath}
File Type: ${metadata.fileType}
File Size: ${metadata.fileSize} bytes
Metadata: ${JSON.stringify(metadata, null, 2)}

File Content:
${fileContent.substring(0, 5000)} ${fileContent.length > 5000 ? '... (truncated)' : ''}

Please provide:
1. Content Quality Score (0-1): Assess code quality, documentation, structure
2. Market Demand Score (0-1): Evaluate market need and demand
3. Technical Merit Score (0-1): Assess technical excellence and innovation
4. Usage Frequency Score (0-1): Estimate how often this would be used
5. Estimated Value (USD): Provide a realistic market value
6. Notes: Detailed justification for your scores

Respond in JSON format:
{
  "content_quality_score": number,
  "market_demand_score": number,
  "technical_merit_score": number,
  "usage_frequency_score": number,
  "estimated_value_usd": number,
  "notes": string
}
`;

  try {
    const response = await callOpenAI({
      prompt,
      model: 'gpt-4',
      maxTokens: 1500,
      temperature: 0.7
    });

    // Parse JSON response
    const jsonMatch = response.content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('Failed to parse LLM response as JSON');
    }

    const appraisal = JSON.parse(jsonMatch[0]);
    
    // Calculate overall score
    const overallScore = (
      appraisal.content_quality_score * 0.3 +
      appraisal.market_demand_score * 0.25 +
      appraisal.technical_merit_score * 0.25 +
      appraisal.usage_frequency_score * 0.2
    );

    return {
      ...appraisal,
      overall_score: overallScore
    };
  } catch (error) {
    console.error('Error in cloud LLM appraisal:', error);
    throw new Error(`Failed to appraise file with cloud LLM: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get LLM provider status
 */
export async function getCloudLLMStatus(): Promise<{
  available: boolean;
  provider: string;
  model: string;
}> {
  const apiKey = process.env.OPENAI_API_KEY;
  const provider = process.env.LLM_PROVIDER || 'openai';
  const model = process.env.LLM_MODEL || 'gpt-4';

  return {
    available: !!apiKey,
    provider,
    model
  };
}