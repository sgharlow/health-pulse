'use client';

import { useEffect, useState } from 'react';

interface Facility {
  facility_id: string;
  facility_name: string;
  state: string;
  hospital_overall_rating: string;
  hospital_type: string;
}

type SortKey = keyof Facility;

export default function FacilitiesPage() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('facility_name');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch('/api/data')
      .then(r => r.json())
      .then(data => {
        setFacilities(data.facilities || []);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load facilities');
        setLoading(false);
      });
  }, []);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  const filtered = facilities
    .filter(f =>
      f.facility_name?.toLowerCase().includes(search.toLowerCase()) ||
      f.state?.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      const av = a[sortKey] ?? '';
      const bv = b[sortKey] ?? '';
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="ml-1 text-gray-600">↕</span>;
    return <span className="ml-1 text-blue-400">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  const columns: { key: SortKey; label: string }[] = [
    { key: 'facility_name', label: 'Facility Name' },
    { key: 'state', label: 'State' },
    { key: 'hospital_overall_rating', label: 'Star Rating' },
    { key: 'hospital_type', label: 'Hospital Type' },
  ];

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Facilities</h1>

        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by name or state..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-gray-800 text-white border border-gray-700 rounded px-4 py-2 w-full max-w-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        {loading && <p className="text-gray-400">Loading facilities...</p>}
        {error && <p className="text-red-400">{error}</p>}

        {!loading && !error && (
          <>
            <p className="text-sm text-gray-500 mb-3">{filtered.length} facilities shown</p>
            <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    {columns.map(col => (
                      <th
                        key={col.key}
                        onClick={() => handleSort(col.key)}
                        className="px-4 py-3 text-left text-gray-400 cursor-pointer hover:text-white select-none"
                      >
                        {col.label}
                        <SortIcon col={col.key} />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((f, i) => (
                    <>
                      <tr
                        key={f.facility_id}
                        onClick={() => setExpanded(expanded === f.facility_id ? null : f.facility_id)}
                        className={`border-b border-gray-800 cursor-pointer transition-colors ${
                          i % 2 === 0 ? 'bg-gray-900' : 'bg-gray-950'
                        } hover:bg-gray-800`}
                      >
                        <td className="px-4 py-3 font-medium">{f.facility_name || '—'}</td>
                        <td className="px-4 py-3 text-gray-400">{f.state || '—'}</td>
                        <td className="px-4 py-3">
                          <StarRating rating={f.hospital_overall_rating} />
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-xs">{f.hospital_type || '—'}</td>
                      </tr>
                      {expanded === f.facility_id && (
                        <tr key={`${f.facility_id}-detail`} className="bg-gray-800">
                          <td colSpan={4} className="px-6 py-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <DetailItem label="Facility ID" value={f.facility_id} />
                              <DetailItem label="Name" value={f.facility_name} />
                              <DetailItem label="State" value={f.state} />
                              <DetailItem label="Star Rating" value={f.hospital_overall_rating} />
                              <DetailItem label="Hospital Type" value={f.hospital_type} />
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                        No facilities match your search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </main>
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

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="text-sm font-medium">{value || '—'}</p>
    </div>
  );
}
