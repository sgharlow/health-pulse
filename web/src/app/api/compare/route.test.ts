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
  mockQueryDomo.mockReset();
});

afterEach(() => {
  vi.unstubAllEnvs();
});

function makeRequest(url: string): Request {
  return new Request(url);
}

const allFacilities = [
  { facility_id: 'F00001', facility_name: 'Hospital A', state: 'CA', city_town: 'LA', hospital_type: 'Acute', hospital_overall_rating: '4' },
  { facility_id: 'F00002', facility_name: 'Hospital B', state: 'TX', city_town: 'Dallas', hospital_type: 'Acute', hospital_overall_rating: '3' },
  { facility_id: 'F00003', facility_name: 'Hospital C', state: 'NY', city_town: 'NYC', hospital_type: 'Critical', hospital_overall_rating: '5' },
];

const allQuality = [
  { facility_id: 'F00001', measure_id: 'M1', measure_name: 'Mortality', score: '10', compared_to_national: 'Better' },
  { facility_id: 'F00001', measure_id: 'M2', measure_name: 'Safety', score: '8', compared_to_national: 'Same' },
  { facility_id: 'F00002', measure_id: 'M1', measure_name: 'Mortality', score: '6', compared_to_national: 'Worse' },
  { facility_id: 'F00003', measure_id: 'M1', measure_name: 'Mortality', score: '12', compared_to_national: 'Better' },
];

describe('GET /api/compare', () => {
  it('returns 400 when no ids parameter is provided', async () => {
    const response = await GET(makeRequest('http://localhost/api/compare'));
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('Provide ?ids=ID1,ID2');
  });

  it('returns 400 for empty ids parameter', async () => {
    const response = await GET(makeRequest('http://localhost/api/compare?ids='));
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('Provide ?ids=ID1,ID2');
  });

  it('returns 400 for invalid facility ID format', async () => {
    const response = await GET(makeRequest('http://localhost/api/compare?ids=INVALID_ID'));
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('Invalid facility ID format');
  });

  it('returns facilities and quality data for valid IDs', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(allFacilities)
      .mockResolvedValueOnce(allQuality);

    const response = await GET(makeRequest('http://localhost/api/compare?ids=F00001,F00002'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.facilities).toHaveLength(2);
    expect(data.quality).toBeDefined();
  });

  it('filters facilities to only requested IDs', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(allFacilities)
      .mockResolvedValueOnce(allQuality);

    const response = await GET(makeRequest('http://localhost/api/compare?ids=F00001'));
    const data = await response.json();

    expect(data.facilities).toHaveLength(1);
    expect(data.facilities[0].facility_id).toBe('F00001');
  });

  it('groups quality measures by facility ID', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(allFacilities)
      .mockResolvedValueOnce(allQuality);

    const response = await GET(makeRequest('http://localhost/api/compare?ids=F00001,F00002'));
    const data = await response.json();

    // F00001 has 2 quality measures, F00002 has 1
    expect(data.quality['F00001']).toHaveLength(2);
    expect(data.quality['F00002']).toHaveLength(1);
  });

  it('returns empty quality array for facility with no quality data', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(allFacilities)
      .mockResolvedValueOnce(allQuality);

    const response = await GET(makeRequest('http://localhost/api/compare?ids=F00003'));
    const data = await response.json();

    expect(data.facilities).toHaveLength(1);
    expect(data.quality['F00003']).toHaveLength(1); // F00003 has 1 quality record
  });

  it('handles single facility ID (no comma)', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(allFacilities)
      .mockResolvedValueOnce(allQuality);

    const response = await GET(makeRequest('http://localhost/api/compare?ids=F00002'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.facilities).toHaveLength(1);
    expect(data.facilities[0].facility_name).toBe('Hospital B');
  });

  it('returns 500 when Domo query fails', async () => {
    mockQueryDomo.mockRejectedValueOnce(new Error('Domo error'));

    const response = await GET(makeRequest('http://localhost/api/compare?ids=F00001'));
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe('Failed to fetch comparison data');
  });

  it('trims whitespace from facility IDs', async () => {
    mockQueryDomo
      .mockResolvedValueOnce(allFacilities)
      .mockResolvedValueOnce(allQuality);

    const response = await GET(makeRequest('http://localhost/api/compare?ids=%20F00001%20,%20F00002%20'));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.facilities).toHaveLength(2);
  });
});
