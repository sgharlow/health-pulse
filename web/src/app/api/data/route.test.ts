import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { GET } from './route';

// Mock the domo-client module
vi.mock('@/lib/data/domo-client', () => ({
  queryDomo: vi.fn(),
}));

import { queryDomo } from '@/lib/data/domo-client';
const mockQueryDomo = vi.mocked(queryDomo);

beforeEach(() => {
  vi.stubEnv('HP_FACILITIES_DATASET_ID', 'fac-dataset');
  vi.stubEnv('HP_QUALITY_DATASET_ID', 'qual-dataset');
  mockQueryDomo.mockReset();
});

afterEach(() => {
  vi.unstubAllEnvs();
});

function makeRequest(url: string): Request {
  return new Request(url);
}

const sampleFacilities = [
  { facility_id: 'F001', facility_name: 'Hospital A', state: 'CA', hospital_overall_rating: '4' },
  { facility_id: 'F002', facility_name: 'Hospital B', state: 'CA', hospital_overall_rating: '3' },
  { facility_id: 'F003', facility_name: 'Hospital C', state: 'TX', hospital_overall_rating: '5' },
];

const sampleQuality = [
  { facility_id: 'F001', measure_id: 'M1', score: '10', compared_to_national: 'Better Than the National Rate' },
  { facility_id: 'F001', measure_id: 'M2', score: '5', compared_to_national: 'Worse Than the National Rate' },
  { facility_id: 'F002', measure_id: 'M1', score: '8', compared_to_national: 'Worse Than the National Rate' },
  { facility_id: 'F003', measure_id: 'M1', score: '12', compared_to_national: 'Better Than the National Rate' },
];

describe('GET /api/data', () => {
  it('returns correct KPIs for all states (no filter)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(sampleFacilities)
      .mockResolvedValueOnce(sampleQuality);

    const response = await GET(makeRequest('http://localhost/api/data'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.kpis).toBeDefined();
    expect(data.kpis.totalFacilities).toBe(3);
    expect(data.kpis.avgStarRating).toBe(4); // (4+3+5)/3 = 4
    expect(data.kpis.anomalyCount).toBe(2); // 2 "Worse Than the National Rate"
    expect(data.kpis.totalMeasures).toBe(4);
  });

  it('returns facilities array (capped at 100)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(sampleFacilities)
      .mockResolvedValueOnce(sampleQuality);

    const response = await GET(makeRequest('http://localhost/api/data'));
    const data = await response.json();

    expect(data.facilities).toHaveLength(3);
    expect(data.facilities[0].facility_name).toBe('Hospital A');
  });

  it('returns quality array (capped at 200)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(sampleFacilities)
      .mockResolvedValueOnce(sampleQuality);

    const response = await GET(makeRequest('http://localhost/api/data'));
    const data = await response.json();

    expect(data.quality).toHaveLength(4);
  });

  it('filters quality records by state when state param is provided', async () => {
    // When state is provided, only quality for matching facility IDs is returned
    const caFacilities = sampleFacilities.filter(f => f.state === 'CA');
    mockQueryDomo
      .mockResolvedValueOnce(caFacilities)
      .mockResolvedValueOnce(sampleQuality);

    const response = await GET(makeRequest('http://localhost/api/data?state=CA'));
    const data = await response.json();

    expect(data.kpis.totalFacilities).toBe(2);
    // Only quality records for F001 and F002 should be included
    expect(data.quality.length).toBe(3); // F001 has 2, F002 has 1
  });

  it('returns 400 for invalid state code', async () => {
    const response = await GET(makeRequest('http://localhost/api/data?state=INVALID'));
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('Invalid state code');
  });

  it('handles empty facilities gracefully', async () => {
    mockQueryDomo
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);

    const response = await GET(makeRequest('http://localhost/api/data'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.kpis.totalFacilities).toBe(0);
    expect(data.kpis.avgStarRating).toBe(0);
    expect(data.kpis.anomalyCount).toBe(0);
    expect(data.kpis.totalMeasures).toBe(0);
  });

  it('handles non-numeric ratings in avgStarRating calculation', async () => {
    mockQueryDomo
      .mockResolvedValueOnce([
        { facility_id: 'F1', facility_name: 'H1', state: 'CA', hospital_overall_rating: 'Not Available' },
        { facility_id: 'F2', facility_name: 'H2', state: 'CA', hospital_overall_rating: '4' },
      ])
      .mockResolvedValueOnce([]);

    const response = await GET(makeRequest('http://localhost/api/data'));
    const data = await response.json();

    // Only the numeric rating should be included in average
    expect(data.kpis.avgStarRating).toBe(4);
  });

  it('returns 500 when Domo query fails', async () => {
    mockQueryDomo.mockRejectedValueOnce(new Error('Domo query failed: 503'));

    const response = await GET(makeRequest('http://localhost/api/data'));
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe('Failed to fetch data');
  });

  it('state parameter is case-insensitive (lowercased input becomes uppercase)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(sampleFacilities)
      .mockResolvedValueOnce(sampleQuality);

    const response = await GET(makeRequest('http://localhost/api/data?state=ca'));
    expect(response.status).toBe(200);

    // Verify the SQL was called with uppercase state
    const firstCallSql = mockQueryDomo.mock.calls[0][1];
    expect(firstCallSql).toContain("WHERE state = 'CA'");
  });
});
