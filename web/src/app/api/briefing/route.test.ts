import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { GET } from './route';

vi.mock('@/lib/data/domo-client', () => ({
  queryDomo: vi.fn(),
}));

import { queryDomo } from '@/lib/data/domo-client';
const mockQueryDomo = vi.mocked(queryDomo);

beforeEach(() => {
  vi.stubEnv('HP_FACILITIES_DATASET_ID', 'fac-ds');
  vi.stubEnv('HP_QUALITY_DATASET_ID', 'qual-ds');
  vi.stubEnv('HP_READMISSIONS_DATASET_ID', 'readm-ds');
  vi.stubEnv('HP_COMMUNITY_DATASET_ID', 'com-ds');
  mockQueryDomo.mockReset();
});

afterEach(() => {
  vi.unstubAllEnvs();
});

function makeRequest(url: string): Request {
  return new Request(url);
}

const facilities = [
  { facility_id: 'F001', facility_name: 'Hospital A', state: 'CA', hospital_overall_rating: '4' },
  { facility_id: 'F002', facility_name: 'Hospital B', state: 'CA', hospital_overall_rating: '2' },
  { facility_id: 'F003', facility_name: 'Hospital C', state: 'CA', hospital_overall_rating: '5' },
];

const quality = [
  { facility_id: 'F001', measure_id: 'M1', score: '10', compared_to_national: 'Better Than the National Rate' },
  { facility_id: 'F001', measure_id: 'M2', score: '5', compared_to_national: 'Worse Than the National Rate' },
  { facility_id: 'F002', measure_id: 'M1', score: '3', compared_to_national: 'Worse Than the National Rate' },
  { facility_id: 'F002', measure_id: 'M3', score: '2', compared_to_national: 'Worse Than the National Rate' },
  { facility_id: 'F999', measure_id: 'M1', score: '9', compared_to_national: 'Better Than the National Rate' },
];

const readmissions = [
  { facility_id: 'F001', facility_name: 'Hospital A', measure_name: 'Heart Failure', excess_readmission_ratio: '1.10' },
  { facility_id: 'F002', facility_name: 'Hospital B', measure_name: 'Pneumonia', excess_readmission_ratio: '0.95' },
  { facility_id: 'F003', facility_name: 'Hospital C', measure_name: 'Hip/Knee', excess_readmission_ratio: '1.20' },
];

const community = [
  { county_fips: '06001', svi_score: '0.85', poverty_rate: '18', uninsured_rate: '12', minority_pct: '55' },
  { county_fips: '06002', svi_score: '0.20', poverty_rate: '8', uninsured_rate: '5', minority_pct: '30' },
  { county_fips: '06003', svi_score: '0.90', poverty_rate: '22', uninsured_rate: '15', minority_pct: '60' },
];

function setupMocks() {
  mockQueryDomo
    .mockResolvedValueOnce(facilities)
    .mockResolvedValueOnce(quality)
    .mockResolvedValueOnce(readmissions)
    .mockResolvedValueOnce(community);
}

describe('GET /api/briefing', () => {
  it('returns the correct response structure', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.state).toBe('CA');
    expect(data.summary).toBeDefined();
    expect(data.starDistribution).toBeDefined();
    expect(data.worstFacilities).toBeDefined();
    expect(data.topCareGaps).toBeDefined();
    expect(data.equityConcerns).toBeDefined();
  });

  it('computes summary statistics correctly', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    expect(data.summary.totalFacilities).toBe(3);
    // avg of 4, 2, 5 = 3.67 -> rounded to 3.67
    expect(data.summary.avgStarRating).toBe(3.67);
    // F001 and F002 quality records only (F999 is not in facilities)
    // F001: 1 worse, F002: 2 worse = 3 total
    expect(data.summary.qualityFlags).toBe(3);
  });

  it('counts care gaps as readmissions with excess ratio > 1.05', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    // F001 (1.10) and F003 (1.20) have ratio > 1.05
    expect(data.summary.careGapCount).toBe(2);
  });

  it('counts high SVI counties (SVI >= 0.75)', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    // county_fips 06001 (0.85) and 06003 (0.90) have SVI >= 0.75
    expect(data.summary.highSVICounties).toBe(2);
  });

  it('builds star rating distribution correctly', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    expect(data.starDistribution).toEqual({
      '1': 0,
      '2': 1,
      '3': 0,
      '4': 1,
      '5': 1,
    });
  });

  it('ranks worst facilities by number of worse-than-national flags', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    // F002 has 2 "worse" flags, F001 has 1
    expect(data.worstFacilities[0].facility_id).toBe('F002');
    expect(data.worstFacilities[0].count).toBe(2);
    expect(data.worstFacilities[1].facility_id).toBe('F001');
    expect(data.worstFacilities[1].count).toBe(1);
  });

  it('sorts top care gaps by excess_readmission_ratio descending', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    expect(data.topCareGaps[0].excess_readmission_ratio).toBe('1.20');
    expect(data.topCareGaps[1].excess_readmission_ratio).toBe('1.10');
  });

  it('defaults state to CA when no state param provided', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing'));
    const data = await response.json();

    expect(data.state).toBe('CA');
  });

  it('returns 400 for invalid state code', async () => {
    const response = await GET(makeRequest('http://localhost/api/briefing?state=INVALID'));
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('Invalid state code');
  });

  it('returns 500 when Domo query fails', async () => {
    mockQueryDomo.mockRejectedValueOnce(new Error('Domo unreachable'));

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe('Failed to generate briefing');
  });

  it('filters out quality records not belonging to state facilities', async () => {
    setupMocks();

    const response = await GET(makeRequest('http://localhost/api/briefing?state=CA'));
    const data = await response.json();

    // F999 quality record should not be counted
    // Total worse: F001 has 1, F002 has 2 = 3 (no F999)
    expect(data.summary.qualityFlags).toBe(3);
  });
});
