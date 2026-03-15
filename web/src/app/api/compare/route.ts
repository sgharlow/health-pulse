import { NextResponse } from 'next/server';
import { queryDomo } from '@/lib/data/domo-client';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const idsParam = searchParams.get('ids') || '';
  const ids = idsParam.split(',').map(id => id.trim()).filter(Boolean);

  if (ids.length < 1) {
    return NextResponse.json({ error: 'Provide ?ids=ID1,ID2' }, { status: 400 });
  }

  try {
    const facId = process.env.HP_FACILITIES_DATASET_ID!;
    const qualId = process.env.HP_QUALITY_DATASET_ID!;

    // Fetch all facilities and quality data, then filter in JS (Domo no-subquery constraint)
    const [allFacilities, allQuality] = await Promise.all([
      queryDomo(facId, `SELECT facility_id, facility_name, state, city_town, hospital_type, hospital_overall_rating FROM table LIMIT 500`),
      queryDomo(qualId, `SELECT facility_id, measure_id, measure_name, score, compared_to_national FROM table LIMIT 2000`),
    ]);

    const facilities = allFacilities.filter(f => ids.includes(f.facility_id));
    const qualityMap: Record<string, typeof allQuality> = {};
    for (const id of ids) {
      qualityMap[id] = allQuality.filter(q => q.facility_id === id);
    }

    return NextResponse.json({ facilities, quality: qualityMap });
  } catch (error) {
    console.error('Compare fetch error:', error);
    return NextResponse.json({ error: 'Failed to fetch comparison data' }, { status: 500 });
  }
}
