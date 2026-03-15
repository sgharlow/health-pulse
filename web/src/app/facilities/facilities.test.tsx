import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import FacilitiesPage from './page';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
  mockFetch.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const facilitiesData = {
  facilities: [
    { facility_id: 'F001', facility_name: 'General Hospital', state: 'CA', hospital_overall_rating: '4', hospital_type: 'Acute Care' },
    { facility_id: 'F002', facility_name: 'City Medical Center', state: 'TX', hospital_overall_rating: '3', hospital_type: 'Critical Access' },
    { facility_id: 'F003', facility_name: 'County Health', state: 'NY', hospital_overall_rating: '5', hospital_type: 'Acute Care' },
  ],
};

describe('Facilities page', () => {
  it('shows loading state initially', () => {
    mockFetch.mockReturnValue(new Promise(() => {}));

    render(<FacilitiesPage />);
    expect(screen.getByText('Loading facilities...')).toBeInTheDocument();
  });

  it('renders the page title', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => facilitiesData,
    });

    render(<FacilitiesPage />);

    await waitFor(() => {
      expect(screen.getByText('Facilities')).toBeInTheDocument();
    });
  });

  it('renders facility names in the table', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => facilitiesData,
    });

    render(<FacilitiesPage />);

    await waitFor(() => {
      expect(screen.getByText('General Hospital')).toBeInTheDocument();
    });
    expect(screen.getByText('City Medical Center')).toBeInTheDocument();
    expect(screen.getByText('County Health')).toBeInTheDocument();
  });

  it('renders table column headers', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => facilitiesData,
    });

    render(<FacilitiesPage />);

    await waitFor(() => {
      expect(screen.getByText('Facility Name')).toBeInTheDocument();
    });
    expect(screen.getByText('State')).toBeInTheDocument();
    expect(screen.getByText('Star Rating')).toBeInTheDocument();
    expect(screen.getByText('Hospital Type')).toBeInTheDocument();
  });

  it('shows facility count', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => facilitiesData,
    });

    render(<FacilitiesPage />);

    await waitFor(() => {
      expect(screen.getByText('3 facilities shown')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => facilitiesData,
    });

    render(<FacilitiesPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search by name or state...')).toBeInTheDocument();
    });
  });

  it('shows error message when fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(<FacilitiesPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load facilities')).toBeInTheDocument();
    });
  });
});
