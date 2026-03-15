'use client';

import { useEffect, useState } from 'react';

interface KPIs {
  totalFacilities: number;
  avgStarRating: number;
  anomalyCount: number;
  totalMeasures: number;
}

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState('');

  useEffect(() => {
    setLoading(true);
    fetch(`/api/data?state=${state}`)
      .then(r => r.json())
      .then(data => {
        setKpis(data.kpis);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [state]);

  const states = ['', 'CA', 'TX', 'NY', 'FL', 'OH', 'PA', 'IL', 'GA', 'NC', 'MI'];

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">HealthPulse Dashboard</h1>
          <select
            value={state}
            onChange={e => setState(e.target.value)}
            className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2"
          >
            <option value="">All States</option>
            {states.filter(Boolean).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="text-gray-400">Loading...</p>
        ) : kpis ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard title="Total Facilities" value={kpis.totalFacilities.toLocaleString()} />
            <KPICard title="Avg Star Rating" value={kpis.avgStarRating.toFixed(2)} subtitle="out of 5.0" />
            <KPICard title="Quality Flags" value={kpis.anomalyCount.toLocaleString()} subtitle="worse than national" color="red" />
            <KPICard title="Measures Tracked" value={kpis.totalMeasures.toLocaleString()} />
          </div>
        ) : (
          <p className="text-red-400">Failed to load data</p>
        )}
      </div>
    </main>
  );
}

function KPICard({ title, value, subtitle, color }: { title: string; value: string; subtitle?: string; color?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p className={`text-3xl font-bold ${color === 'red' ? 'text-red-400' : 'text-white'}`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}
