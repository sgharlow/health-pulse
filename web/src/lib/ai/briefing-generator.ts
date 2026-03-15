import Anthropic from '@anthropic-ai/sdk';

export interface AIBriefingInput {
  state: string;
  summary: {
    totalFacilities: number;
    avgStarRating: number;
    qualityFlags: number;
    careGapCount: number;
    highSVICounties: number;
  };
  starDistribution: Record<string, string | number>;
  worstFacilities: Array<{
    facility_id: string;
    name: string;
    count: number;
  }>;
  topCareGaps: Array<{
    facility_id: string;
    facility_name: string;
    measure_name: string;
    excess_readmission_ratio: string;
  }>;
  equityConcerns: Array<{
    county_fips: string;
    svi_score: string;
    poverty_rate: string;
    uninsured_rate: string;
    minority_pct: string;
  }>;
}

export interface AIBriefingOutput {
  executive_summary: string;
  key_findings: string[];
  anomalies_and_alerts: string[];
  equity_insights: string[];
  recommended_actions: string[];
}

const SYSTEM_PROMPT = `You are a healthcare quality analyst for a hospital network. Analyze the following quality metrics and generate an executive briefing. Focus on actionable insights, not just data recitation. Flag anomalies, equity concerns, and recommended interventions.

You MUST respond with valid JSON matching this exact structure:
{
  "executive_summary": "A 2-3 sentence high-level summary for hospital executives",
  "key_findings": ["finding1", "finding2", ...],
  "anomalies_and_alerts": ["alert1", "alert2", ...],
  "equity_insights": ["insight1", "insight2", ...],
  "recommended_actions": ["action1", "action2", ...]
}

Each array should have 3-5 items. Be specific and reference actual numbers from the data. Use clear, professional language suitable for a healthcare executive audience.`;

export async function generateAIBriefing(
  data: AIBriefingInput
): Promise<AIBriefingOutput> {
  const apiKey = process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY is not configured');
  }

  const client = new Anthropic({ apiKey });

  const userMessage = `Analyze these healthcare quality metrics for ${data.state} and generate an executive briefing:

${JSON.stringify(data, null, 2)}`;

  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: userMessage,
        },
      ],
    });

    // Extract text content from the response
    const textBlock = response.content.find((block) => block.type === 'text');
    if (!textBlock || textBlock.type !== 'text') {
      throw new Error('No text content in AI response');
    }

    // Parse the JSON response - handle potential markdown code blocks
    let jsonText = textBlock.text.trim();
    if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '');
    }

    const parsed: AIBriefingOutput = JSON.parse(jsonText);

    // Validate required fields
    if (
      !parsed.executive_summary ||
      !Array.isArray(parsed.key_findings) ||
      !Array.isArray(parsed.anomalies_and_alerts) ||
      !Array.isArray(parsed.equity_insights) ||
      !Array.isArray(parsed.recommended_actions)
    ) {
      throw new Error('AI response missing required fields');
    }

    return parsed;
  } catch (error: unknown) {
    if (error instanceof Anthropic.RateLimitError) {
      throw new Error('AI rate limit exceeded. Please try again in a moment.');
    }
    if (error instanceof Anthropic.AuthenticationError) {
      throw new Error('Invalid ANTHROPIC_API_KEY. Please check your configuration.');
    }
    if (error instanceof SyntaxError) {
      throw new Error('AI returned invalid JSON. Please try again.');
    }
    throw error;
  }
}
