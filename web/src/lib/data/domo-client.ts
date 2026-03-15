const API_BASE = 'https://api.domo.com';

let cachedToken: { token: string; expiresAt: number } | null = null;

export async function getDomoToken(): Promise<string> {
  const now = Date.now();
  if (cachedToken && now < cachedToken.expiresAt - 60_000) {
    return cachedToken.token;
  }

  const clientId = process.env.DOMO_CLIENT_ID!;
  const clientSecret = process.env.DOMO_CLIENT_SECRET!;
  const basic = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  const resp = await fetch(
    `${API_BASE}/oauth/token?grant_type=client_credentials&scope=data`,
    {
      method: 'GET',
      headers: { Authorization: `Basic ${basic}` },
    }
  );

  if (!resp.ok) throw new Error(`Domo auth failed: ${resp.status}`);
  const data = await resp.json();
  cachedToken = {
    token: data.access_token,
    expiresAt: now + data.expires_in * 1000,
  };
  return cachedToken.token;
}

export async function queryDomo(datasetId: string, sql: string): Promise<Record<string, string>[]> {
  const token = await getDomoToken();
  const resp = await fetch(
    `${API_BASE}/v1/datasets/query/execute/${datasetId}`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ sql }),
    }
  );

  if (!resp.ok) throw new Error(`Domo query failed: ${resp.status}`);
  const result = await resp.json();
  const columns: string[] = result.columns || [];
  const rows: string[][] = result.rows || [];
  return rows.map(row => Object.fromEntries(columns.map((col, i) => [col, row[i]])));
}
