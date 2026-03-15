import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from './page';

// Mock recharts to avoid issues with SSR/canvas in test environment
vi.mock('recharts', () => {
  const MockComponent = ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="mock-chart">{children}</div>
  );
  return {
    BarChart: MockComponent,
    Bar: MockComponent,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    ResponsiveContainer: MockComponent,
    Cell: () => null,
  };
});

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
  mockFetch.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const dashboardData = {
  kpis: {
    totalFacilities: 1500,
    avgStarRating: 3.42,
    anomalyCount: 287,
    totalMeasures: 12500,
  },
  facilities: [
    { facility_id: 'F001', facility_name: 'Hospital A', state: 'CA', hospital_overall_rating: '4' },
    { facility_id: 'F002', facility_name: 'Hospital B', state: 'TX', hospital_overall_rating: '3' },
  ],
};

describe('Dashboard page', () => {
  it('shows loading state initially', () => {
    mockFetch.mockReturnValue(new Promise(() => {})); // never resolves

    render(<Dashboard />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders the page title', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => dashboardData,
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('HealthPulse Dashboard')).toBeInTheDocument();
    });
  });

  it('renders KPI cards with correct values after data loads', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => dashboardData,
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Facilities')).toBeInTheDocument();
      expect(screen.getByText('1,500')).toBeInTheDocument();
    });

    expect(screen.getByText('Avg Star Rating')).toBeInTheDocument();
    expect(screen.getByText('3.42')).toBeInTheDocument();
    expect(screen.getByText('Quality Flags')).toBeInTheDocument();
    expect(screen.getByText('287')).toBeInTheDocument();
    expect(screen.getByText('Measures Tracked')).toBeInTheDocument();
    expect(screen.getByText('12,500')).toBeInTheDocument();
  });

  it('renders the state selector dropdown', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => dashboardData,
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('All States')).toBeInTheDocument();
    });

    // Check a few state options
    expect(screen.getByText('CA')).toBeInTheDocument();
    expect(screen.getByText('TX')).toBeInTheDocument();
    expect(screen.getByText('NY')).toBeInTheDocument();
  });

  it('shows error message when fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    });
  });
});
