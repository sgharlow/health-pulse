import { NextResponse } from 'next/server';
import { generateAIBriefing } from '@/lib/ai/briefing-generator';

export async function POST(request: Request) {
  // Check for API key before doing any work
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      {
        error: 'AI briefing unavailable',
        detail: 'ANTHROPIC_API_KEY is not configured. Add it to your .env.local file to enable AI-generated narratives.',
      },
      { status: 503 }
    );
  }

  try {
    const body = await request.json();
    const { state } = body;

    if (!state || !/^[A-Z]{2}$/.test(state)) {
      return NextResponse.json(
        { error: 'Invalid or missing state code' },
        { status: 400 }
      );
    }

    // Fetch briefing data from the existing internal API
    const origin = new URL(request.url).origin;
    const briefingRes = await fetch(`${origin}/api/briefing?state=${state}`);

    if (!briefingRes.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch briefing data' },
        { status: 502 }
      );
    }

    const briefingData = await briefingRes.json();

    // Generate AI narrative
    const narrative = await generateAIBriefing(briefingData);

    return NextResponse.json({
      state,
      narrative,
      generated_at: new Date().toISOString(),
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('AI briefing error:', message);

    // Return specific error messages for known issues
    if (message.includes('rate limit')) {
      return NextResponse.json({ error: message }, { status: 429 });
    }
    if (message.includes('ANTHROPIC_API_KEY')) {
      return NextResponse.json({ error: message }, { status: 503 });
    }

    return NextResponse.json(
      { error: 'Failed to generate AI briefing', detail: message },
      { status: 500 }
    );
  }
}
