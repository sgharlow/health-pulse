import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { GET } from './route';

vi.mock('@/lib/data/domo-client', () => ({
  queryDomo: vi.fn(),
}));

import { queryDomo } from '@/lib/data/domo-client';
const mockQueryDomo = vi.mocked(queryDomo);

beforeEach(() => {
  vi.stubEnv('HP_FACILITIES_DATASET_ID', 'fac-ds');
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
  { facility_id: 'F001', facility_name: 'Hospital A', state: 'CA', hospital_overall_rating: '2', county_fips: '06001' },
  { facility_id: 'F002', facility_name: 'Hospital B', state: 'CA', hospital_overall_rating: '3', county_fips: '06001' },
  { facility_id: 'F003', facility_name: 'Hospital C', state: 'CA', hospital_overall_rating: '5', county_fips: '06002' },
  { facility_id: 'F004', facility_name: 'Hospital D', state: 'CA', hospital_overall_rating: '4', county_fips: '06002' },
  { facility_id: 'F005', facility_name: 'Hospital E', state: 'CA', hospital_overall_rating: '5', county_fips: '' },
];

const communityData = [
  { county_fips: '06001', svi_score: '0.85' },  // high SVI
  { county_fips: '06002', svi_score: '0.15' },  // low SVI
];

describe('GET /api/equity', () => {
  it('returns correct response structure', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.summary).toBeDefined();
    expect(data.highSVIFacilities).toBeDefined();
  });

  it('correctly joins facilities with SVI data by county_fips', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    // F005 has no county_fips so should be excluded
    expect(data.summary.totalWithSVI).toBe(4);
  });

  it('identifies high SVI facilities (SVI >= 0.75)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    // F001 and F002 are in county 06001 with SVI 0.85
    expect(data.summary.highSVICount).toBe(2);
  });

  it('identifies low SVI facilities (SVI < 0.25)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    // F003 and F004 are in county 06002 with SVI 0.15
    expect(data.summary.lowSVICount).toBe(2);
  });

  it('computes average star rating for high and low SVI groups', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    // High SVI: F001(2) + F002(3) = avg 2.5
    expect(data.summary.avgStarHighSVI).toBe(2.5);
    // Low SVI: F003(5) + F004(4) = avg 4.5
    expect(data.summary.avgStarLowSVI).toBe(4.5);
  });

  it('computes star disparity (lowSVI avg - highSVI avg)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    // 4.5 - 2.5 = 2.0
    expect(data.summary.starDisparity).toBe(2);
  });

  it('returns high SVI facilities list (capped at 100)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(facilities)
      .mockResolvedValueOnce(communityData);

    const response = await GET(makeRequest('http://localhost/api/equity?state=CA'));
    const data = await response.json();

    expect(data.highSVIFacilities).toHaveLength(2);
    expect(data.highSVIFacilities[0].svi_score).toBe(0.85);
  });

  it('returns 400 for invalid state code', async () => {
    const response = await GET(makeRequest('http://localhost/api/equity?state=XYZ'));
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('Invalid state code');
  });

  it('returns 500 when Domo query fails', async () => {
    mockQueryDomo.mockRejectedValueOnce(new Error('Domo timeout'));

    const response = await GET(makeRequest('http://localhost/api/equity'));
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe('Failed to fetch equity data');
  });

  it('handles zero disparity when both groups have same rating', async () => {
    const sameFac = [
      { facility_id: 'F1', facility_name: 'H1', state: 'CA', hospital_overall_rating: '3', county_fips: '06001' },
      { facility_id: 'F2', facility_name: 'H2', state: 'CA', hospital_overall_rating: '3', county_fips: '06002' },
    ];
    const sameCom = [
      { county_fips: '06001', svi_score: '0.90' },
      { county_fips: '06002', svi_score: '0.10' },
    ];

    mockQueryDomo
      .mockResolvedValueOnce(sameFac)
      .mockResolvedValueOnce(sameCom);

    const response = await GET(makeRequest('http://localhost/api/equity'));
    const data = await response.json();

    expect(data.summary.starDisparity).toBe(0);
  });
});
