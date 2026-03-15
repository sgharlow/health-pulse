import { NextResponse } from 'next/server';
import { queryDomo } from '@/lib/data/domo-client';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const state = searchParams.get('state') || '';

  // Validate state parameter
  if (state && !/^[A-Z]{2}$/.test(state.toUpperCase())) {
    return NextResponse.json({ error: 'Invalid state code' }, { status: 400 });
  }
  const safeState = state ? state.toUpperCase() : '';

  try {
    const facId = process.env.HP_FACILITIES_DATASET_ID!;
    const qualId = process.env.HP_QUALITY_DATASET_ID!;

    // Domo SQL does not support subqueries — fetch all data and filter in JS
    const stateFilter = safeState ? `WHERE state = '${safeState}'` : '';
    const [allFacilities, allQuality] = await Promise.all([
      queryDomo(facId, `SELECT facility_id, facility_name, state, hospital_overall_rating FROM table ${stateFilter} LIMIT 6000`),
      queryDomo(qualId, `SELECT facility_id, measure_id, score, compared_to_national FROM table LIMIT 50000`),
    ]);

    // Filter quality records in JS to match facilities (avoids Domo subquery limitation)
    const facilityIds = new Set(allFacilities.map(f => f.facility_id));
    const quality = safeState
      ? allQuality.filter(q => facilityIds.has(q.facility_id))
      : allQuality;

    const facilities = allFacilities;

    // Compute KPIs
    const ratings = facilities
      .map(f => parseFloat(f.hospital_overall_rating))
      .filter(r => !isNaN(r));
    const avgRating = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : 0;
    const worseCount = quality.filter(q => q.compared_to_national === 'Worse Than the National Rate').length;

    return NextResponse.json({
      kpis: {
        totalFacilities: facilities.length,
        avgStarRating: Math.round(avgRating * 100) / 100,
        anomalyCount: worseCount,
        totalMeasures: quality.length,
      },
      facilities: facilities,
      quality: quality,
    });
  } catch (error) {
    console.error('Data fetch error:', error);
    return NextResponse.json({ error: 'Failed to fetch data' }, { status: 500 });
  }
}
