'use client';

import { useEffect, useState } from 'react';

interface Facility {
  facility_id: string;
  facility_name: string;
  state: string;
  city_town: string;
  hospital_type: string;
  hospital_overall_rating: string;
}

interface QualityRow {
  facility_id: string;
  measure_id: string;
  measure_name: string;
  score: string;
  compared_to_national: string;
}

interface CompareData {
  facilities: Facility[];
  quality: Record<string, QualityRow[]>;
}

export default function ComparePage() {
  const [allFacilities, setAllFacilities] = useState<Facility[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedA, setSelectedA] = useState('');
  const [selectedB, setSelectedB] = useState('');
  const [compareData, setCompareData] = useState<CompareData | null>(null);
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/data')
      .then(r => r.json())
      .then(data => {
        setAllFacilities(data.facilities || []);
        setLoadingList(false);
      })
      .catch(() => setLoadingList(false));
  }, []);

  function handleCompare() {
    if (!selectedA || !selectedB) return;
    setLoadingCompare(true);
    setError('');
    fetch(`/api/compare?ids=${selectedA},${selectedB}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          setError(data.error);
        } else {
          setCompareData(data);
        }
        setLoadingCompare(false);
      })
      .catch(() => {
        setError('Failed to fetch comparison data');
        setLoadingCompare(false);
      });
  }

  const facA = compareData?.facilities.find(f => f.facility_id === selectedA);
  const facB = compareData?.facilities.find(f => f.facility_id === selectedB);
  const qualA = compareData?.quality[selectedA] || [];
  const qualB = compareData?.quality[selectedB] || [];

  // Align quality measures by measure_id for side-by-side display
  const allMeasureIds = Array.from(new Set([...qualA.map(q => q.measure_id), ...qualB.map(q => q.measure_id)]));
  const qualAMap = Object.fromEntries(qualA.map(q => [q.measure_id, q]));
  const qualBMap = Object.fromEntries(qualB.map(q => [q.measure_id, q]));

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Compare Facilities</h1>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="text-sm text-gray-400 block mb-1">Facility A</label>
              <select
                value={selectedA}
                onChange={e => setSelectedA(e.target.value)}
                className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 w-full"
              >
                <option value="">Select a facility...</option>
                {allFacilities.map(f => (
                  <option key={f.facility_id} value={f.facility_id}>
                    {f.facility_name} ({f.state})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">Facility B</label>
              <select
                value={selectedB}
                onChange={e => setSelectedB(e.target.value)}
                className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 w-full"
              >
                <option value="">Select a facility...</option>
                {allFacilities.map(f => (
                  <option key={f.facility_id} value={f.facility_id}>
                    {f.facility_name} ({f.state})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <button
                onClick={handleCompare}
                disabled={!selectedA || !selectedB || loadingCompare}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed px-6 py-2 rounded-lg font-semibold transition w-full"
              >
                {loadingCompare ? 'Loading...' : 'Compare'}
              </button>
            </div>
          </div>
        </div>

        {error && <p className="text-red-400 mb-4">{error}</p>}

        {compareData && facA && facB && (
          <>
            {/* Profile comparison */}
            <div className="grid grid-cols-2 gap-4 mb-8">
              <FacilityCard facility={facA} label="Facility A" />
              <FacilityCard facility={facB} label="Facility B" />
            </div>

            {/* Quality measures */}
            {allMeasureIds.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800">
                  <h2 className="font-semibold">Quality Measures</h2>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="px-4 py-3 text-left text-gray-400 w-1/2">Measure</th>
                      <th className="px-4 py-3 text-left text-gray-400">{facA.facility_name}</th>
                      <th className="px-4 py-3 text-left text-gray-400">{facB.facility_name}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allMeasureIds.map((mid, i) => {
                      const a = qualAMap[mid];
                      const b = qualBMap[mid];
                      return (
                        <tr key={mid} className={`border-b border-gray-800 ${i % 2 === 0 ? 'bg-gray-900' : 'bg-gray-950'}`}>
                          <td className="px-4 py-3 text-gray-300">{a?.measure_name || b?.measure_name || mid}</td>
                          <td className="px-4 py-3">
                            <QualityCell row={a} />
                          </td>
                          <td className="px-4 py-3">
                            <QualityCell row={b} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {compareData && (!facA || !facB) && (
          <p className="text-yellow-400">One or both facilities not found in dataset.</p>
        )}
      </div>
    </main>
  );
}

function FacilityCard({ facility, label }: { facility: Facility; label: string }) {
  const rating = parseInt(facility.hospital_overall_rating, 10);
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <p className="text-xs text-blue-400 font-semibold mb-2 uppercase tracking-wide">{label}</p>
      <h2 className="text-lg font-bold mb-3">{facility.facility_name}</h2>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">State</span>
          <span>{facility.state}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">City</span>
          <span>{facility.city_town || '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Type</span>
          <span className="text-right max-w-xs">{facility.hospital_type || '—'}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Star Rating</span>
          {isNaN(rating) ? (
            <span className="text-gray-600">N/A</span>
          ) : (
            <span className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map(s => (
                <span key={s} className={s <= rating ? 'text-yellow-400' : 'text-gray-700'}>★</span>
              ))}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function QualityCell({ row }: { row: { score: string; compared_to_national: string } | undefined }) {
  if (!row) return <span className="text-gray-600">—</span>;
  const isWorse = row.compared_to_national === 'Worse Than the National Rate';
  const isBetter = row.compared_to_national === 'Better Than the National Rate';
  return (
    <div>
      <span className="font-medium">{row.score || '—'}</span>
      {row.compared_to_national && (
        <span className={`ml-2 text-xs ${isWorse ? 'text-red-400' : isBetter ? 'text-green-400' : 'text-gray-500'}`}>
          {isWorse ? 'Worse' : isBetter ? 'Better' : 'Average'}
        </span>
      )}
    </div>
  );
}
