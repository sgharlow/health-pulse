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
        </nav>
        {children}
      </body>
    </html>
  );
}
