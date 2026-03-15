import { NextResponse } from 'next/server';
import { queryDomo } from '@/lib/data/domo-client';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const state = searchParams.get('state') || 'CA';

  try {
    const facId = process.env.HP_FACILITIES_DATASET_ID!;
    const qualId = process.env.HP_QUALITY_DATASET_ID!;
    const readmId = process.env.HP_READMISSIONS_DATASET_ID!;
    const comId = process.env.HP_COMMUNITY_DATASET_ID!;

    // Parallel queries — Domo SQL uses FROM table (no subqueries)
    const [facilities, allQuality, readmissions, community] = await Promise.all([
      queryDomo(
        facId,
        `SELECT facility_id, facility_name, state, hospital_overall_rating FROM table WHERE state = '${state}' LIMIT 6000`
      ),
      queryDomo(
        qualId,
        `SELECT facility_id, measure_id, score, compared_to_national FROM table LIMIT 50000`
      ),
      queryDomo(
        readmId,
        `SELECT facility_id, facility_name, measure_name, excess_readmission_ratio FROM table WHERE state = '${state}' LIMIT 10000`
      ),
      queryDomo(
        comId,
        `SELECT county_fips, svi_score, poverty_rate, uninsured_rate, minority_pct FROM table WHERE state = '${state}' LIMIT 5000`
      ),
    ]);

    // Filter quality to state facilities (avoids Domo subquery limitation)
    const facIds = new Set(facilities.map((f) => f.facility_id));
    const stateQuality = allQuality.filter((q) => facIds.has(q.facility_id));

    // Compute summary stats
    const ratings = facilities
      .map((f) => parseFloat(f.hospital_overall_rating))
      .filter((r) => !isNaN(r) && r > 0);
    const avgRating = ratings.length
      ? ratings.reduce((a, b) => a + b, 0) / ratings.length
      : 0;

    const worseCount = stateQuality.filter(
      (q) => q.compared_to_national === 'Worse Than the National Rate'
    ).length;

    const careGaps = readmissions.filter(
      (r) => parseFloat(r.excess_readmission_ratio || '0') > 1.05
    );

    const highSVI = community.filter(
      (c) => parseFloat(c.svi_score || '0') >= 0.75
    );

    // Star rating distribution
    const starDist: Record<string, number> = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 };
    for (const f of facilities) {
      const r = f.hospital_overall_rating;
      if (r in starDist) starDist[r]++;
    }

    // Worst facilities by quality flag count
    const facilityWorseCount: Record<string, { name: string; count: number }> = {};
    for (const q of stateQuality) {
      if (q.compared_to_national === 'Worse Than the National Rate') {
        if (!facilityWorseCount[q.facility_id]) {
          const match = facilities.find((f) => f.facility_id === q.facility_id);
          facilityWorseCount[q.facility_id] = {
            name: match?.facility_name || q.facility_id,
            count: 0,
          };
        }
        facilityWorseCount[q.facility_id].count++;
      }
    }
    const worstFacilities = Object.entries(facilityWorseCount)
      .sort(([, a], [, b]) => b.count - a.count)
      .slice(0, 5)
      .map(([id, data]) => ({ facility_id: id, ...data }));

    // Top care gaps sorted by excess ratio
    const topCareGaps = careGaps
      .sort(
        (a, b) =>
          parseFloat(b.excess_readmission_ratio || '0') -
          parseFloat(a.excess_readmission_ratio || '0')
      )
      .slice(0, 10);

    return NextResponse.json({
      state,
      summary: {
        totalFacilities: facilities.length,
        avgStarRating: Math.round(avgRating * 100) / 100,
        qualityFlags: worseCount,
        careGapCount: careGaps.length,
        highSVICounties: highSVI.length,
      },
      starDistribution: starDist,
      worstFacilities,
      topCareGaps,
      equityConcerns: highSVI.slice(0, 5),
    });
  } catch (error) {
    console.error('Briefing fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to generate briefing' },
      { status: 500 }
    );
  }
}
