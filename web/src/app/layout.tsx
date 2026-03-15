import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'HealthPulse AI',
  description: 'Healthcare Performance Intelligence Dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-white antialiased">
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
          <span className="text-blue-400 font-bold text-lg mr-4">HealthPulse AI</span>
          <Link href="/" className="text-gray-300 hover:text-white text-sm transition">Home</Link>
          <Link href="/dashboard" className="text-gray-300 hover:text-white text-sm transition">Dashboard</Link>
          <Link href="/facilities" className="text-gray-300 hover:text-white text-sm transition">Facilities</Link>
          <Link href="/compare" className="text-gray-300 hover:text-white text-sm transition">Compare</Link>
          <Link href="/equity" className="text-gray-300 hover:text-white text-sm transition">Equity</Link>
          <Link href="/briefing" className="text-gray-300 hover:text-white text-sm transition">Briefing</Link>
          <Link href="/chat" className="text-gray-300 hover:text-white text-sm transition">Chat</Link>
          <div className="ml-auto">
            <a
              href="https://app.promptopinion.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 border border-green-500 text-green-400 hover:bg-green-500/10 hover:text-green-300 px-3 py-1.5 rounded-md text-sm font-medium transition"
            >
              Prompt Opinion
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="shrink-0"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </a>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
