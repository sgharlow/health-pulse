'use client';

import { useEffect, useState } from 'react';

interface EquitySummary {
  totalWithSVI: number;
  highSVICount: number;
  lowSVICount: number;
  avgStarHighSVI: number;
  avgStarLowSVI: number;
  starDisparity: number;
}

interface FacilityRow {
  facility_id: string;
  facility_name: string;
  state: string;
  hospital_overall_rating: string;
  county_fips: string;
  svi_score: number;
}

export default function EquityPage() {
  const [summary, setSummary] = useState<EquitySummary | null>(null);
  const [facilities, setFacilities] = useState<FacilityRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/equity')
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          setError(data.error);
        } else {
          setSummary(data.summary);
          setFacilities(data.highSVIFacilities || []);
        }
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load equity data');
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Equity Analysis</h1>
        <p className="text-gray-400 mb-8">
          Social Vulnerability Index (SVI) analysis — facilities serving high-vulnerability communities
        </p>

        {loading && <p className="text-gray-400">Loading equity data...</p>}
        {error && <p className="text-red-400">{error}</p>}

        {!loading && !error && summary && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <SummaryCard
                title="Facilities with SVI Data"
                value={summary.totalWithSVI.toLocaleString()}
              />
              <SummaryCard
                title="High-SVI Communities (SVI ≥ 0.75)"
                value={summary.highSVICount.toLocaleString()}
                subtitle="hospitals in vulnerable areas"
              />
              <SummaryCard
                title="Star Rating Disparity"
                value={summary.starDisparity > 0 ? `+${summary.starDisparity.toFixed(2)}` : summary.starDisparity.toFixed(2)}
                subtitle="low vs high SVI avg stars"
                color={summary.starDisparity < -0.1 ? 'red' : summary.starDisparity > 0.1 ? 'green' : undefined}
              />
            </div>

            {/* Disparity breakdown */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-8">
              <h2 className="font-semibold text-lg mb-4">Avg Star Rating by SVI Tier</h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Low Vulnerability (SVI &lt; 0.25)</p>
                  <p className="text-3xl font-bold text-green-400">{summary.avgStarLowSVI.toFixed(2)}</p>
                  <p className="text-xs text-gray-500 mt-1">{summary.lowSVICount} facilities</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-1">High Vulnerability (SVI ≥ 0.75)</p>
                  <p className="text-3xl font-bold text-red-400">{summary.avgStarHighSVI.toFixed(2)}</p>
                  <p className="text-xs text-gray-500 mt-1">{summary.highSVICount} facilities</p>
                </div>
              </div>
              {summary.starDisparity !== 0 && (
                <div className="mt-4 p-3 bg-gray-800 rounded text-sm text-gray-300">
                  {summary.starDisparity > 0
                    ? `Facilities in low-vulnerability areas rate ${summary.starDisparity.toFixed(2)} stars higher on average than those in high-vulnerability areas.`
                    : `Facilities in high-vulnerability areas rate ${Math.abs(summary.starDisparity).toFixed(2)} stars higher on average than those in low-vulnerability areas.`}
                </div>
              )}
            </div>

            {/* High-SVI facilities table */}
            {facilities.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800">
                  <h2 className="font-semibold">High-SVI Facilities (SVI &ge; 0.75)</h2>
                  <p className="text-xs text-gray-500 mt-0.5">Hospitals in communities with high social vulnerability</p>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="px-4 py-3 text-left text-gray-400">Facility Name</th>
                      <th className="px-4 py-3 text-left text-gray-400">State</th>
                      <th className="px-4 py-3 text-left text-gray-400">Star Rating</th>
                      <th className="px-4 py-3 text-left text-gray-400">SVI Score</th>
                      <th className="px-4 py-3 text-left text-gray-400">County FIPS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {facilities.map((f, i) => (
                      <tr
                        key={f.facility_id}
                        className={`border-b border-gray-800 ${i % 2 === 0 ? 'bg-gray-900' : 'bg-gray-950'}`}
                      >
                        <td className="px-4 py-3 font-medium">{f.facility_name || '—'}</td>
                        <td className="px-4 py-3 text-gray-400">{f.state || '—'}</td>
                        <td className="px-4 py-3">
                          <StarRating rating={f.hospital_overall_rating} />
                        </td>
                        <td className="px-4 py-3">
                          <SVIBadge score={f.svi_score} />
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">{f.county_fips}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}

function SummaryCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string;
  subtitle?: string;
  color?: 'red' | 'green';
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p
        className={`text-3xl font-bold ${
          color === 'red' ? 'text-red-400' : color === 'green' ? 'text-green-400' : 'text-white'
        }`}
      >
        {value}
      </p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

function StarRating({ rating }: { rating: string }) {
  const num = parseInt(rating, 10);
  if (isNaN(num)) return <span className="text-gray-600">N/A</span>;
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map(s => (
        <span key={s} className={s <= num ? 'text-yellow-400' : 'text-gray-700'}>★</span>
      ))}
    </span>
  );
}

function SVIBadge({ score }: { score: number }) {
  const color =
    score >= 0.75 ? 'bg-red-900 text-red-300' :
    score >= 0.5 ? 'bg-yellow-900 text-yellow-300' :
    'bg-green-900 text-green-300';
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {score.toFixed(3)}
    </span>
  );
}
