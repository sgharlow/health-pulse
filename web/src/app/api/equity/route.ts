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
    const communityId = process.env.HP_COMMUNITY_DATASET_ID!;

    const stateFilter = safeState ? `WHERE state = '${safeState}'` : '';
    const [allFacilities, allCommunity] = await Promise.all([
      queryDomo(facId, `SELECT facility_id, facility_name, state, hospital_overall_rating, county_fips FROM table ${stateFilter} LIMIT 6000`),
      queryDomo(communityId, `SELECT county_fips, svi_score FROM table LIMIT 5000`),
    ]);

    // Build county_fips -> svi_score map
    const sviMap: Record<string, number> = {};
    for (const row of allCommunity) {
      const fips = row.county_fips;
      const svi = parseFloat(row.svi_score);
      if (fips && !isNaN(svi)) {
        sviMap[fips] = svi;
      }
    }

    // Join facilities with SVI by county_fips
    const joined = allFacilities
      .filter(f => f.county_fips)
      .map(f => ({
        facility_id: f.facility_id,
        facility_name: f.facility_name,
        state: f.state,
        hospital_overall_rating: f.hospital_overall_rating,
        county_fips: f.county_fips,
        svi_score: sviMap[f.county_fips] ?? null,
      }))
      .filter(f => f.svi_score !== null);

    // High SVI = top quartile (>= 0.75)
    const highSVI = joined.filter(f => (f.svi_score as number) >= 0.75);
    const lowSVI = joined.filter(f => (f.svi_score as number) < 0.25);

    function avgRating(list: typeof joined) {
      const ratings = list
        .map(f => parseFloat(f.hospital_overall_rating))
        .filter(r => !isNaN(r));
      return ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : 0;
    }

    const avgHighSVI = avgRating(highSVI);
    const avgLowSVI = avgRating(lowSVI);
    const disparity = avgLowSVI - avgHighSVI;

    return NextResponse.json({
      summary: {
        totalWithSVI: joined.length,
        highSVICount: highSVI.length,
        lowSVICount: lowSVI.length,
        avgStarHighSVI: Math.round(avgHighSVI * 100) / 100,
        avgStarLowSVI: Math.round(avgLowSVI * 100) / 100,
        starDisparity: Math.round(disparity * 100) / 100,
      },
      highSVIFacilities: highSVI.slice(0, 100),
    });
  } catch (error) {
    console.error('Equity fetch error:', error);
    return NextResponse.json({ error: 'Failed to fetch equity data' }, { status: 500 });
  }
}
