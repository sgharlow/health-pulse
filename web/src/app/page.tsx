import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Hero */}
      <section className="pt-16 pb-8 px-6 text-center">
        <h1 className="text-5xl font-bold mb-3 tracking-tight">HealthPulse AI</h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Healthcare Performance Intelligence — 5,400+ US hospitals, 233K+ data points
        </p>
      </section>

      {/* Three feature cards */}
      <section className="max-w-6xl mx-auto px-6 pb-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Visual Analytics */}
        <Link
          href="/dashboard"
          className="group relative rounded-xl bg-gray-900 border border-gray-800 hover:border-blue-500/60 p-6 flex flex-col transition-all duration-200"
        >
          <div className="absolute inset-x-0 top-0 h-1 rounded-t-xl bg-blue-500" />
          <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4">
            {/* Chart icon */}
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-2 text-white group-hover:text-blue-300 transition">Visual Analytics</h2>
          <p className="text-sm text-gray-400 mb-6 flex-1">
            Explore KPIs, star ratings, and quality flags across all hospitals
          </p>
          <span className="inline-flex items-center text-sm font-medium text-blue-400 group-hover:text-blue-300 transition">
            Open Dashboard
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1.5"><polyline points="9 18 15 12 9 6" /></svg>
          </span>
        </Link>

        {/* Ask HealthPulse AI — highlighted */}
        <Link
          href="/chat"
          className="group relative rounded-xl bg-gray-900 border-2 border-cyan-500/40 hover:border-cyan-400/70 p-6 flex flex-col transition-all duration-200 shadow-lg shadow-cyan-500/5"
        >
          <div className="absolute inset-x-0 top-0 h-1 rounded-t-xl bg-gradient-to-r from-cyan-500 to-blue-500" />
          <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center mb-4">
            {/* Chat bubble icon */}
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-2 text-white group-hover:text-cyan-300 transition">Ask HealthPulse AI</h2>
          <p className="text-sm text-gray-400 mb-6 flex-1">
            Ask questions about hospital quality, equity, and performance in natural language
          </p>
          <span className="inline-flex items-center text-sm font-medium text-cyan-400 group-hover:text-cyan-300 transition">
            Start Chatting
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1.5"><polyline points="9 18 15 12 9 6" /></svg>
          </span>
        </Link>

        {/* Prompt Opinion Marketplace */}
        <a
          href="https://app.promptopinion.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="group relative rounded-xl bg-gray-900 border border-gray-800 hover:border-green-500/60 p-6 flex flex-col transition-all duration-200"
        >
          <div className="absolute inset-x-0 top-0 h-1 rounded-t-xl bg-green-500" />
          <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center mb-4">
            {/* External / marketplace icon */}
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-400">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-2 text-white group-hover:text-green-300 transition">Prompt Opinion Marketplace</h2>
          <p className="text-sm text-gray-400 mb-6 flex-1">
            Try HealthPulse AI on the Prompt Opinion platform — our MCP server in action
          </p>
          <span className="inline-flex items-center text-sm font-medium text-green-400 group-hover:text-green-300 transition">
            Open Marketplace
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1.5">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </span>
        </a>
      </section>

      {/* Stats bar */}
      <section className="border-y border-gray-800 bg-gray-900/50 py-6 px-6">
        <div className="max-w-6xl mx-auto flex flex-wrap justify-center gap-x-8 gap-y-2 text-sm">
          <span className="text-gray-300"><span className="text-blue-400 font-semibold">11</span> MCP Tools</span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-300"><span className="text-blue-400 font-semibold">7</span> Domo Datasets</span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-300"><span className="text-blue-400 font-semibold">233K+</span> Records</span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-300"><span className="text-blue-400 font-semibold">5,426</span> Hospitals</span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-300"><span className="text-blue-400 font-semibold">100</span> Synthetic Patients</span>
          <span className="text-gray-600">|</span>
          <span className="text-green-400 font-semibold">SHARP/FHIR Ready</span>
        </div>
      </section>

      {/* Footer quick links */}
      <footer className="py-10 px-6 text-center">
        <div className="flex flex-wrap justify-center gap-4 mb-6 text-sm">
          <Link href="/dashboard" className="text-gray-400 hover:text-white transition">Dashboard</Link>
          <span className="text-gray-700">|</span>
          <Link href="/facilities" className="text-gray-400 hover:text-white transition">Facilities</Link>
          <span className="text-gray-700">|</span>
          <Link href="/compare" className="text-gray-400 hover:text-white transition">Compare</Link>
          <span className="text-gray-700">|</span>
          <Link href="/equity" className="text-gray-400 hover:text-white transition">Equity</Link>
          <span className="text-gray-700">|</span>
          <Link href="/briefing" className="text-gray-400 hover:text-white transition">Briefing</Link>
          <span className="text-gray-700">|</span>
          <Link href="/chat" className="text-gray-400 hover:text-white transition">Chat</Link>
        </div>
        <p className="text-sm text-gray-500 mb-2">
          Built for{' '}
          <span className="text-gray-400">Agents Assemble Healthcare AI Hackathon</span>
        </p>
        <a
          href="https://github.com/sgharlow/health-pulse"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-white transition"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="shrink-0">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          sgharlow/health-pulse
        </a>
      </footer>
    </main>
  );
}
