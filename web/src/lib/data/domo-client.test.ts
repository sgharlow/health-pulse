import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// We need to test the module fresh each time to reset the cached token
let getDomoToken: typeof import('./domo-client').getDomoToken;
let queryDomo: typeof import('./domo-client').queryDomo;

const mockFetch = vi.fn();

beforeEach(async () => {
  vi.stubGlobal('fetch', mockFetch);
  vi.stubEnv('DOMO_CLIENT_ID', 'test-client-id');
  vi.stubEnv('DOMO_CLIENT_SECRET', 'test-client-secret');
  mockFetch.mockReset();

  // Re-import to reset cached token
  vi.resetModules();
  const mod = await import('./domo-client');
  getDomoToken = mod.getDomoToken;
  queryDomo = mod.queryDomo;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('getDomoToken', () => {
  it('fetches a new OAuth token from Domo API', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'tok-123', expires_in: 3600 }),
    });

    const token = await getDomoToken();

    expect(token).toBe('tok-123');
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/oauth/token');
    expect(url).toContain('grant_type=client_credentials');
    expect(opts.method).toBe('GET');
    expect(opts.headers.Authorization).toMatch(/^Basic /);
  });

  it('sends correct Basic auth header encoding client_id:client_secret', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'tok-abc', expires_in: 3600 }),
    });

    await getDomoToken();

    const expectedBasic = Buffer.from('test-client-id:test-client-secret').toString('base64');
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers.Authorization).toBe(`Basic ${expectedBasic}`);
  });

  it('caches the token for subsequent calls', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'tok-cached', expires_in: 3600 }),
    });

    const token1 = await getDomoToken();
    const token2 = await getDomoToken();

    expect(token1).toBe('tok-cached');
    expect(token2).toBe('tok-cached');
    // Should only call fetch once due to caching
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('throws an error when the auth request fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    await expect(getDomoToken()).rejects.toThrow('Domo auth failed: 401');
  });

  it('throws on network failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    await expect(getDomoToken()).rejects.toThrow('Network error');
  });
});

describe('queryDomo', () => {
  beforeEach(() => {
    // First call will be the token fetch, second will be the query
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'tok-query', expires_in: 3600 }),
    });
  });

  it('executes a SQL query against the Domo dataset API', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        columns: ['id', 'name'],
        rows: [['1', 'Hospital A'], ['2', 'Hospital B']],
      }),
    });

    const result = await queryDomo('dataset-123', 'SELECT id, name FROM table');

    expect(result).toEqual([
      { id: '1', name: 'Hospital A' },
      { id: '2', name: 'Hospital B' },
    ]);
  });

  it('sends the correct request to Domo query endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ columns: ['a'], rows: [['1']] }),
    });

    await queryDomo('ds-abc', 'SELECT a FROM table');

    const [url, opts] = mockFetch.mock.calls[1]; // second call is the query
    expect(url).toContain('/v1/datasets/query/execute/ds-abc');
    expect(opts.method).toBe('POST');
    expect(opts.headers.Authorization).toBe('Bearer tok-query');
    expect(opts.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(opts.body)).toEqual({ sql: 'SELECT a FROM table' });
  });

  it('returns empty array when no rows are returned', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ columns: ['id'], rows: [] }),
    });

    const result = await queryDomo('ds-empty', 'SELECT id FROM table');
    expect(result).toEqual([]);
  });

  it('handles missing columns and rows gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}), // no columns or rows keys
    });

    const result = await queryDomo('ds-x', 'SELECT x FROM table');
    expect(result).toEqual([]);
  });

  it('throws an error when the query request fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    await expect(queryDomo('ds-bad', 'SELECT x FROM table')).rejects.toThrow(
      'Domo query failed: 500'
    );
  });

  it('maps columns to row values correctly for multi-column results', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        columns: ['facility_id', 'state', 'rating'],
        rows: [
          ['F001', 'CA', '4'],
          ['F002', 'TX', '3'],
          ['F003', 'NY', '5'],
        ],
      }),
    });

    const result = await queryDomo('ds-multi', 'SELECT facility_id, state, rating FROM table');

    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ facility_id: 'F001', state: 'CA', rating: '4' });
    expect(result[2]).toEqual({ facility_id: 'F003', state: 'NY', rating: '5' });
  });
});
