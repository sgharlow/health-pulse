import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-bold mb-4">HealthPulse AI</h1>
        <p className="text-xl text-gray-400 mb-8">
          Healthcare Performance Intelligence — powered by real CMS data for 5,400+ US hospitals
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition"
          >
            Open Dashboard
          </Link>
        </div>
        <p className="text-sm text-gray-500 mt-12">
          Agents Assemble Healthcare AI Hackathon Entry
        </p>
      </div>
    </main>
  );
}
