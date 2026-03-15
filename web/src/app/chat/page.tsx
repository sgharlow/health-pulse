'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  tool_used?: string | null;
}

interface ChatResponse {
  response: string;
  tool_used: string | null;
  data_summary: object | null;
  error?: string;
}

const SUGGESTED_QUERIES = [
  'What are the worst quality hospitals in California?',
  'Show me equity disparities in Texas',
  'Compare UCSF Medical Center (050454) vs Cleveland Clinic (330101)',
  'Generate an executive briefing for Florida',
  'Which states have the worst healthcare performance?',
];

const TOOL_LABELS: Record<string, string> = {
  get_quality_data: 'Quality Data',
  get_briefing: 'State Briefing',
  get_equity_analysis: 'Equity Analysis',
  compare_facilities: 'Facility Comparison',
  get_ai_briefing: 'AI Briefing',
};

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      <div className="flex gap-1">
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '0ms', animationDuration: '0.6s' }}
        />
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '150ms', animationDuration: '0.6s' }}
        />
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '300ms', animationDuration: '0.6s' }}
        />
      </div>
      <span className="text-sm text-gray-400 ml-2">HealthPulse AI is thinking...</span>
    </div>
  );
}

function formatMessage(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Bold text: **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const formattedParts = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={j} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });

    // Bullet points
    if (line.trimStart().startsWith('- ') || line.trimStart().startsWith('* ')) {
      const indent = line.length - line.trimStart().length;
      elements.push(
        <div key={i} className="flex gap-2" style={{ paddingLeft: `${indent * 4 + 8}px` }}>
          <span className="text-blue-400 mt-0.5 shrink-0">&bull;</span>
          <span>{formattedParts.slice(0).map((p, idx) => {
            if (typeof p === 'string' && (p.startsWith('- ') || p.startsWith('* '))) {
              return p.slice(2);
            }
            return p;
          })}</span>
        </div>
      );
    } else if (line.trimStart().match(/^\d+\.\s/)) {
      // Numbered lists
      const match = line.trimStart().match(/^(\d+)\.\s(.*)/);
      if (match) {
        elements.push(
          <div key={i} className="flex gap-2 pl-2">
            <span className="text-blue-400 shrink-0 font-medium">{match[1]}.</span>
            <span>{formattedParts}</span>
          </div>
        );
      }
    } else if (line.trim().startsWith('###')) {
      elements.push(
        <h4 key={i} className="font-semibold text-white mt-3 mb-1 text-sm">
          {line.replace(/^###\s*/, '')}
        </h4>
      );
    } else if (line.trim().startsWith('##')) {
      elements.push(
        <h3 key={i} className="font-bold text-white mt-3 mb-1">
          {line.replace(/^##\s*/, '')}
        </h3>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(
        <p key={i} className="leading-relaxed">
          {formattedParts}
        </p>
      );
    }
  }

  return elements;
}

function UnconfiguredState() {
  return (
    <main className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-8">
      <div className="max-w-lg text-center">
        <div className="w-16 h-16 bg-gray-800 border border-gray-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-8 h-8 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold mb-3">Chat Not Available</h1>
        <p className="text-gray-400 mb-6">
          The ANTHROPIC_API_KEY is not configured. To enable the conversational AI chat, add your
          API key to <code className="text-blue-400 bg-gray-800 px-1.5 py-0.5 rounded text-sm">.env.local</code>:
        </p>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-left mb-6">
          <code className="text-green-400 text-sm font-mono">
            ANTHROPIC_API_KEY=sk-ant-...
          </code>
        </div>
        <p className="text-gray-400 mb-6">
          In the meantime, you can use the HealthPulse MCP tools directly through Prompt Opinion:
        </p>
        <a
          href="https://promptopinion.com"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-3 rounded-lg transition"
        >
          Open Prompt Opinion
        </a>
      </div>
    </main>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [apiUnavailable, setApiUnavailable] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      const userMessage: ChatMessage = { role: 'user', content: text.trim() };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setShowSuggestions(false);
      setIsLoading(true);

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text.trim(),
            history: messages.map((m) => ({ role: m.role, content: m.content })),
          }),
        });

        if (res.status === 503) {
          setApiUnavailable(true);
          setIsLoading(false);
          return;
        }

        const data: ChatResponse = await res.json();

        if (data.error) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `Sorry, an error occurred: ${data.error}`,
              tool_used: null,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: data.response,
              tool_used: data.tool_used,
            },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Sorry, I was unable to connect to the server. Please try again.',
            tool_used: null,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, messages]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input);
      }
    },
    [input, sendMessage]
  );

  if (apiUnavailable) {
    return <UnconfiguredState />;
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col" style={{ height: 'calc(100vh - 49px)' }}>
      {/* Header */}
      <div className="border-b border-gray-800 px-4 sm:px-6 py-3 shrink-0">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-semibold">HealthPulse AI Chat</h1>
            <p className="text-xs text-gray-400">Ask about hospital quality, equity, and performance</p>
          </div>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && !isLoading && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-900 border border-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2">Welcome to HealthPulse AI</h2>
              <p className="text-gray-400 text-sm max-w-md mx-auto">
                Ask me anything about hospital quality, healthcare equity, or facility performance
                across 5,400+ US hospitals.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : 'bg-gray-800 border border-gray-700 text-gray-200 rounded-bl-md'
                }`}
              >
                {msg.role === 'assistant' && msg.tool_used && (
                  <div className="mb-2">
                    <span className="inline-block text-xs font-medium bg-gray-700 text-blue-300 px-2 py-0.5 rounded-full border border-gray-600">
                      Used: {TOOL_LABELS[msg.tool_used] || msg.tool_used}
                    </span>
                  </div>
                )}
                <div className="text-sm space-y-1">
                  {msg.role === 'assistant' ? formatMessage(msg.content) : <p>{msg.content}</p>}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-bl-md">
                <TypingIndicator />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggested queries */}
      {showSuggestions && messages.length === 0 && (
        <div className="px-4 sm:px-6 pb-2 shrink-0">
          <div className="max-w-3xl mx-auto">
            <p className="text-xs text-gray-500 mb-2">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUERIES.map((query, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(query)}
                  disabled={isLoading}
                  className="text-xs text-gray-300 border border-gray-700 hover:border-blue-500 hover:text-blue-300 rounded-full px-3 py-1.5 transition-colors disabled:opacity-50"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-gray-800 px-4 sm:px-6 py-3 shrink-0">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about hospital quality, equity, or performance..."
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-gray-900 border border-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 resize-none outline-none transition disabled:opacity-50"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl px-4 py-2.5 transition shrink-0"
              aria-label="Send message"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-1.5 text-center">
            Powered by real CMS data from 5,400+ US hospitals
          </p>
        </div>
      </div>
    </main>
  );
}
