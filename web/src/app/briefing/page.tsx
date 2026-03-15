'use client';

import { useEffect, useState } from 'react';

interface BriefingSummary {
  totalFacilities: number;
  avgStarRating: number;
  qualityFlags: number;
  careGapCount: number;
  highSVICounties: number;
}

interface WorstFacility {
  facility_id: string;
  name: string;
  count: number;
}

interface CareGap {
  facility_id: string;
  facility_name: string;
  measure_name: string;
  excess_readmission_ratio: string;
}

interface EquityConcern {
  county_fips: string;
  svi_score: string;
  poverty_rate: string;
  uninsured_rate: string;
  minority_pct: string;
}

interface BriefingData {
  state: string;
  summary: BriefingSummary;
  starDistribution: Record<string, string | number>;
  worstFacilities: WorstFacility[];
  topCareGaps: CareGap[];
  equityConcerns: EquityConcern[];
}

const STATES = ['CA', 'TX', 'NY', 'FL', 'OH', 'PA', 'IL', 'GA', 'NC', 'MI'];

function SeverityBadge({ level }: { level: 'critical' | 'warning' | 'good' }) {
  const styles = {
    critical: 'bg-red-900/50 text-red-300 border border-red-700',
    warning: 'bg-yellow-900/50 text-yellow-300 border border-yellow-700',
    good: 'bg-green-900/50 text-green-300 border border-green-700',
  };
  const labels = { critical: 'CRITICAL', warning: 'WARNING', good: 'GOOD' };
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded ${styles[level]}`}>
      {labels[level]}
    </span>
  );
}

function SectionCard({
  title,
  borderColor,
  children,
}: {
  title: string;
  borderColor: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg p-6 border-l-4 ${borderColor}`}>
      <h2 className="text-lg font-semibold text-white mb-4">{title}</h2>
      {children}
    </div>
  );
}

function MetricRow({
  label,
  value,
  level,
}: {
  label: string;
  value: string | number;
  level?: 'critical' | 'warning' | 'good';
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-white">{value}</span>
        {level && <SeverityBadge level={level} />}
      </div>
    </div>
  );
}

export default function BriefingPage() {
  const [state, setState] = useState('CA');
  const [data, setData] = useState<BriefingData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/briefing?state=${state}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [state]);

  const ratingLevel = (avg: number): 'critical' | 'warning' | 'good' =>
    avg >= 4 ? 'good' : avg >= 3 ? 'warning' : 'critical';

  const flagLevel = (count: number, total: number): 'critical' | 'warning' | 'good' => {
    const pct = total > 0 ? count / total : 0;
    return pct > 0.15 ? 'critical' : pct > 0.08 ? 'warning' : 'good';
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Executive Briefing</h1>
            <p className="text-gray-400 text-sm mt-1">
              AI-powered state-level healthcare intelligence from CMS data
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-400">State</label>
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 text-sm"
            >
              {STATES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* State Badge */}
        <div className="mb-6 flex items-center gap-3">
          <span className="bg-blue-900/50 border border-blue-700 text-blue-300 text-xs font-bold px-3 py-1 rounded-full">
            {state} BRIEFING
          </span>
          <span className="text-gray-500 text-xs">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400 text-sm">Generating executive briefing…</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 text-red-300">
            <p className="font-semibold mb-1">Failed to load briefing</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {data && !loading && (
          <div className="space-y-6">
            {/* Performance Overview */}
            <SectionCard title="Performance Overview" borderColor="border-l-blue-500">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <StatTile
                  label="Total Facilities"
                  value={data.summary.totalFacilities.toLocaleString()}
                />
                <StatTile
                  label="Avg Star Rating"
                  value={`${data.summary.avgStarRating.toFixed(2)} / 5`}
                  color={
                    data.summary.avgStarRating >= 4
                      ? 'text-green-400'
                      : data.summary.avgStarRating >= 3
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  }
                />
                <StatTile
                  label="Quality Flags"
                  value={data.summary.qualityFlags.toLocaleString()}
                  color="text-red-400"
                />
                <StatTile
                  label="Care Gaps"
                  value={data.summary.careGapCount.toLocaleString()}
                  color="text-yellow-400"
                />
                <StatTile
                  label="High-Risk Counties"
                  value={data.summary.highSVICounties.toLocaleString()}
                  color="text-orange-400"
                />
              </div>
              <div className="mt-4 pt-4 border-t border-gray-800">
                <MetricRow
                  label="Overall Rating Health"
                  value={data.summary.avgStarRating.toFixed(2)}
                  level={ratingLevel(data.summary.avgStarRating)}
                />
                <MetricRow
                  label="Quality Flag Rate"
                  value={`${data.summary.qualityFlags.toLocaleString()} measures below national benchmark`}
                  level={flagLevel(data.summary.qualityFlags, data.summary.totalFacilities * 10)}
                />
              </div>
            </SectionCard>

            {/* Star Distribution */}
            <SectionCard title="Star Rating Distribution" borderColor="border-l-purple-500">
              <div className="flex items-end gap-3 h-32">
                {[1, 2, 3, 4, 5].map((star) => {
                  const rawVal = data.starDistribution[String(star)];
                  const count = parseInt(String(rawVal ?? 0), 10);
                  const max = Math.max(
                    ...Object.values(data.starDistribution).map((v) => parseInt(String(v), 10))
                  );
                  const heightPct = max > 0 ? (count / max) * 100 : 0;
                  const barColor =
                    star >= 4 ? 'bg-green-500' : star >= 3 ? 'bg-yellow-500' : 'bg-red-500';
                  return (
                    <div key={star} className="flex-1 flex flex-col items-center gap-1">
                      <span className="text-xs text-gray-400">{count}</span>
                      <div className="w-full flex items-end justify-center">
                        <div
                          className={`w-full rounded-t ${barColor} transition-all duration-500`}
                          style={{ height: `${Math.max(heightPct, 2)}px`, maxHeight: '96px', minHeight: count > 0 ? '4px' : '0' }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{star}★</span>
                    </div>
                  );
                })}
              </div>
            </SectionCard>

            {/* Quality Concerns */}
            <SectionCard title="Quality Concerns — Worst Performing Facilities" borderColor="border-l-red-500">
              {data.worstFacilities.length === 0 ? (
                <p className="text-gray-400 text-sm">No significant quality concerns identified.</p>
              ) : (
                <div className="space-y-0">
                  {data.worstFacilities.map((f, i) => (
                    <div
                      key={f.facility_id}
                      className="flex items-center justify-between py-3 border-b border-gray-800 last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-500 w-4">{i + 1}</span>
                        <span className="text-sm text-white font-medium">{f.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-red-400 font-semibold">
                          {f.count} flags
                        </span>
                        <SeverityBadge level={f.count >= 5 ? 'critical' : 'warning'} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            {/* Readmission Analysis */}
            <SectionCard title="Readmission Analysis — Excess Ratio &gt; 1.05" borderColor="border-l-yellow-500">
              {data.topCareGaps.length === 0 ? (
                <p className="text-gray-400 text-sm">No excess readmission concerns detected.</p>
              ) : (
                <div className="space-y-0">
                  {data.topCareGaps.map((gap, i) => {
                    const ratio = parseFloat(gap.excess_readmission_ratio || '0');
                    const level: 'critical' | 'warning' = ratio >= 1.15 ? 'critical' : 'warning';
                    return (
                      <div
                        key={`${gap.facility_id}-${i}`}
                        className="py-3 border-b border-gray-800 last:border-0"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-sm text-white font-medium">{gap.facility_name}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{gap.measure_name}</p>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-sm font-mono text-yellow-400">
                              {ratio.toFixed(3)}×
                            </span>
                            <SeverityBadge level={level} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </SectionCard>

            {/* Health Equity */}
            <SectionCard title="Health Equity — High Social Vulnerability Counties" borderColor="border-l-orange-500">
              {data.equityConcerns.length === 0 ? (
                <p className="text-gray-400 text-sm">No high-SVI counties identified for this state.</p>
              ) : (
                <div className="space-y-0">
                  {data.equityConcerns.map((c, i) => {
                    const svi = parseFloat(c.svi_score || '0');
                    const poverty = parseFloat(c.poverty_rate || '0');
                    const uninsured = parseFloat(c.uninsured_rate || '0');
                    return (
                      <div
                        key={`${c.county_fips}-${i}`}
                        className="py-3 border-b border-gray-800 last:border-0"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-white font-medium">
                              FIPS: {c.county_fips}
                            </p>
                            <div className="flex gap-4 mt-1">
                              <span className="text-xs text-gray-500">
                                Poverty:{' '}
                                <span className="text-orange-400">
                                  {isNaN(poverty) ? 'N/A' : `${(poverty * 100).toFixed(1)}%`}
                                </span>
                              </span>
                              <span className="text-xs text-gray-500">
                                Uninsured:{' '}
                                <span className="text-orange-400">
                                  {isNaN(uninsured) ? 'N/A' : `${(uninsured * 100).toFixed(1)}%`}
                                </span>
                              </span>
                              <span className="text-xs text-gray-500">
                                Minority:{' '}
                                <span className="text-orange-400">
                                  {c.minority_pct
                                    ? `${(parseFloat(c.minority_pct) * 100).toFixed(1)}%`
                                    : 'N/A'}
                                </span>
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono text-orange-400">
                              SVI: {svi.toFixed(3)}
                            </span>
                            <SeverityBadge level={svi >= 0.9 ? 'critical' : 'warning'} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </SectionCard>
          </div>
        )}
      </div>
    </main>
  );
}

function StatTile({
  label,
  value,
  color = 'text-white',
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 text-center">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
