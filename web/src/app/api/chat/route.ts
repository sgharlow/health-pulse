import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

const SYSTEM_PROMPT = `You are HealthPulse AI, a healthcare performance intelligence assistant. You help users explore quality metrics, equity disparities, and facility performance across 5,400+ US hospitals using real CMS data. Be concise, cite specific numbers, and highlight actionable findings. When users ask about specific states or facilities, use the appropriate tools to get data.`;

const TOOLS: Anthropic.Messages.Tool[] = [
  {
    name: 'get_quality_data',
    description:
      'Get hospital quality data including KPIs (total facilities, average star rating, quality flags, measures tracked), facility list, and quality measures. Optionally filter by US state code (e.g. CA, TX, NY).',
    input_schema: {
      type: 'object' as const,
      properties: {
        state: {
          type: 'string',
          description: 'Two-letter US state code (e.g. CA, TX, NY). Leave empty for nationwide data.',
        },
      },
      required: [],
    },
  },
  {
    name: 'get_briefing',
    description:
      'Get a detailed state-level healthcare briefing including summary stats, star rating distribution, worst facilities by quality flags, top care gaps (readmissions), and equity concerns (high SVI counties). Requires a state code.',
    input_schema: {
      type: 'object' as const,
      properties: {
        state: {
          type: 'string',
          description: 'Two-letter US state code (e.g. CA, TX, FL). Required.',
        },
      },
      required: ['state'],
    },
  },
  {
    name: 'get_equity_analysis',
    description:
      'Get equity analysis showing healthcare disparities between high-SVI (Social Vulnerability Index) and low-SVI communities. Compares average star ratings and facility counts. Optionally filter by state.',
    input_schema: {
      type: 'object' as const,
      properties: {
        state: {
          type: 'string',
          description: 'Two-letter US state code. Leave empty for nationwide analysis.',
        },
      },
      required: [],
    },
  },
  {
    name: 'compare_facilities',
    description:
      'Compare two or more hospitals side by side. Returns facility info (name, state, type, star rating) and detailed quality measures for each. Provide CMS facility IDs (6-character alphanumeric codes).',
    input_schema: {
      type: 'object' as const,
      properties: {
        facility_ids: {
          type: 'array',
          items: { type: 'string' },
          description: 'Array of CMS facility ID codes (e.g. ["050454", "330101"]).',
        },
      },
      required: ['facility_ids'],
    },
  },
  {
    name: 'get_ai_briefing',
    description:
      'Generate an AI-powered executive briefing for a state, with narrative insights, key findings, anomalies, equity insights, and recommended actions. Requires a state code.',
    input_schema: {
      type: 'object' as const,
      properties: {
        state: {
          type: 'string',
          description: 'Two-letter US state code (e.g. FL, CA). Required.',
        },
      },
      required: ['state'],
    },
  },
];

interface ChatMessage {
  role: string;
  content: string;
}

interface ChatRequest {
  message: string;
  history: ChatMessage[];
}

async function callInternalAPI(
  origin: string,
  toolName: string,
  toolInput: Record<string, unknown>
): Promise<{ data: unknown; error: string | null }> {
  try {
    let url: string;
    let method = 'GET';
    let body: string | undefined;

    switch (toolName) {
      case 'get_quality_data': {
        const state = (toolInput.state as string) || '';
        url = `${origin}/api/data${state ? `?state=${state.toUpperCase()}` : ''}`;
        break;
      }
      case 'get_briefing': {
        const state = (toolInput.state as string) || 'CA';
        url = `${origin}/api/briefing?state=${state.toUpperCase()}`;
        break;
      }
      case 'get_equity_analysis': {
        const state = (toolInput.state as string) || '';
        url = `${origin}/api/equity${state ? `?state=${state.toUpperCase()}` : ''}`;
        break;
      }
      case 'compare_facilities': {
        const ids = (toolInput.facility_ids as string[]) || [];
        url = `${origin}/api/compare?ids=${ids.join(',')}`;
        break;
      }
      case 'get_ai_briefing': {
        const state = (toolInput.state as string) || 'CA';
        url = `${origin}/api/ai-briefing`;
        method = 'POST';
        body = JSON.stringify({ state: state.toUpperCase() });
        break;
      }
      default:
        return { data: null, error: `Unknown tool: ${toolName}` };
    }

    const res = await fetch(url, {
      method,
      headers: method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
      body,
    });

    if (!res.ok) {
      const errBody = await res.text();
      return { data: null, error: `API returned ${res.status}: ${errBody}` };
    }

    const data = await res.json();
    return { data, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { data: null, error: `Failed to call internal API: ${message}` };
  }
}

function truncateData(data: unknown): unknown {
  // Truncate large arrays to keep token count manageable
  if (Array.isArray(data)) {
    if (data.length > 20) {
      return [...data.slice(0, 20), `... and ${data.length - 20} more items`];
    }
    return data.map(truncateData);
  }
  if (data && typeof data === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
      result[key] = truncateData(value);
    }
    return result;
  }
  return data;
}

export async function POST(request: Request) {
  // Check for API key
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      {
        error: 'Configure ANTHROPIC_API_KEY to enable chat',
      },
      { status: 503 }
    );
  }

  let body: ChatRequest;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { message, history = [] } = body;

  if (!message || typeof message !== 'string') {
    return NextResponse.json({ error: 'Message is required' }, { status: 400 });
  }

  const origin = new URL(request.url).origin;
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  // Build messages from history + current message
  const messages: Anthropic.Messages.MessageParam[] = [
    ...history
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
    { role: 'user', content: message },
  ];

  try {
    // First call: let Claude decide which tool to use (or answer directly)
    let response = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      tools: TOOLS,
      messages,
    });

    let toolUsed: string | null = null;
    let dataSummary: unknown = null;

    // Handle tool use loop (Claude may call a tool)
    while (response.stop_reason === 'tool_use') {
      const toolUseBlock = response.content.find(
        (block): block is Anthropic.Messages.ToolUseBlock => block.type === 'tool_use'
      );

      if (!toolUseBlock) break;

      toolUsed = toolUseBlock.name;
      const toolInput = toolUseBlock.input as Record<string, unknown>;

      // Call the internal API
      const { data, error } = await callInternalAPI(origin, toolUseBlock.name, toolInput);

      if (error) {
        // Feed error back to Claude
        const toolMessages: Anthropic.Messages.MessageParam[] = [
          ...messages,
          { role: 'assistant', content: response.content },
          {
            role: 'user',
            content: [
              {
                type: 'tool_result',
                tool_use_id: toolUseBlock.id,
                content: JSON.stringify({ error }),
                is_error: true,
              },
            ],
          },
        ];

        response = await client.messages.create({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 4096,
          system: SYSTEM_PROMPT,
          tools: TOOLS,
          messages: toolMessages,
        });
      } else {
        // Truncate data for the summary and for Claude's context
        const truncated = truncateData(data);
        dataSummary = truncated;

        const toolMessages: Anthropic.Messages.MessageParam[] = [
          ...messages,
          { role: 'assistant', content: response.content },
          {
            role: 'user',
            content: [
              {
                type: 'tool_result',
                tool_use_id: toolUseBlock.id,
                content: JSON.stringify(truncated),
              },
            ],
          },
        ];

        response = await client.messages.create({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 4096,
          system: SYSTEM_PROMPT,
          tools: TOOLS,
          messages: toolMessages,
        });
      }
    }

    // Extract the final text response
    const textBlock = response.content.find(
      (block): block is Anthropic.Messages.TextBlock => block.type === 'text'
    );

    const responseText = textBlock?.text || 'I was unable to generate a response. Please try again.';

    return NextResponse.json({
      response: responseText,
      tool_used: toolUsed,
      data_summary: dataSummary
        ? {
            type: toolUsed,
            has_data: true,
          }
        : null,
    });
  } catch (err) {
    if (err instanceof Anthropic.RateLimitError) {
      return NextResponse.json(
        { error: 'Rate limit exceeded. Please try again in a moment.' },
        { status: 429 }
      );
    }
    if (err instanceof Anthropic.AuthenticationError) {
      return NextResponse.json(
        { error: 'Invalid ANTHROPIC_API_KEY. Check your configuration.' },
        { status: 401 }
      );
    }
    const message = err instanceof Error ? err.message : 'Unknown error';
    console.error('Chat API error:', message);
    return NextResponse.json(
      { error: 'Failed to process chat message', detail: message },
      { status: 500 }
    );
  }
}
