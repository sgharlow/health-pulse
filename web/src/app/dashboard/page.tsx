'use client';

import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface KPIs {
  totalFacilities: number;
  avgStarRating: number;
  anomalyCount: number;
  totalMeasures: number;
}

interface FacilityRow {
  facility_id: string;
  facility_name: string;
  state: string;
  hospital_overall_rating: string;
}

interface DashboardData {
  kpis: KPIs;
  facilities: FacilityRow[];
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState('');

  useEffect(() => {
    setLoading(true);
    fetch(`/api/data?state=${state}`)
      .then((r) => r.json())
      .then((d) => {
        setData(d);
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
            onChange={(e) => setState(e.target.value)}
            className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2"
          >
            <option value="">All States</option>
            {states.filter(Boolean).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="text-gray-400">Loading...</p>
        ) : data?.kpis ? (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <KPICard
                title="Total Facilities"
                value={data.kpis.totalFacilities.toLocaleString()}
              />
              <KPICard
                title="Avg Star Rating"
                value={data.kpis.avgStarRating.toFixed(2)}
                subtitle="out of 5.0"
              />
              <KPICard
                title="Quality Flags"
                value={data.kpis.anomalyCount.toLocaleString()}
                subtitle="worse than national"
                color="red"
              />
              <KPICard
                title="Measures Tracked"
                value={data.kpis.totalMeasures.toLocaleString()}
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <StarDistribution facilities={data.facilities} />
              <RatingBreakdown facilities={data.facilities} />
            </div>
          </>
        ) : (
          <p className="text-red-400">Failed to load data</p>
        )}
      </div>
    </main>
  );
}

function KPICard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p className={`text-3xl font-bold ${color === 'red' ? 'text-red-400' : 'text-white'}`}>
        {value}
      </p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

function StarDistribution({ facilities }: { facilities: FacilityRow[] }) {
  const dist = [1, 2, 3, 4, 5].map((star) => ({
    rating: `${star} Star`,
    count: facilities.filter((f) => f.hospital_overall_rating === String(star)).length,
    fill: star >= 4 ? '#22c55e' : star >= 3 ? '#eab308' : '#ef4444',
  }));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Star Rating Distribution</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={dist}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="rating" stroke="#9ca3af" tick={{ fontSize: 12 }} />
          <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              color: '#fff',
              borderRadius: '6px',
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {dist.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function RatingBreakdown({ facilities }: { facilities: FacilityRow[] }) {
  // Group by state and count low-rated (1-2 star) facilities
  const stateMap: Record<string, { low: number; total: number }> = {};
  for (const f of facilities) {
    const s = f.state;
    if (!s) continue;
    if (!stateMap[s]) stateMap[s] = { low: 0, total: 0 };
    stateMap[s].total++;
    const r = parseFloat(f.hospital_overall_rating);
    if (!isNaN(r) && r <= 2) stateMap[s].low++;
  }

  const chartData = Object.entries(stateMap)
    .map(([state, counts]) => ({ state, lowRated: counts.low, total: counts.total }))
    .sort((a, b) => b.lowRated - a.lowRated)
    .slice(0, 5);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-1">Top States by Low-Rated Facilities</h3>
      <p className="text-xs text-gray-500 mb-4">Facilities with 1–2 star ratings</p>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 12 }} />
          <YAxis dataKey="state" type="category" stroke="#9ca3af" tick={{ fontSize: 12 }} width={30} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              color: '#fff',
              borderRadius: '6px',
            }}
          />
          <Bar dataKey="lowRated" fill="#ef4444" radius={[0, 4, 4, 0]} name="Low-Rated" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
