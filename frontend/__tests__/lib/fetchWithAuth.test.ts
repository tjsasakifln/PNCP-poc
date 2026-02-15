/**
 * STORY-253: fetchWithAuth utility tests
 *
 * Tests the 401 → refresh → retry pattern.
 */

// Mock supabase before imports
const mockGetSession = jest.fn();
const mockRefreshSession = jest.fn();

jest.mock('../../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: () => mockGetSession(),
      refreshSession: () => mockRefreshSession(),
    },
  },
}));

// Mock window.location
const originalLocation = window.location;
beforeAll(() => {
  Object.defineProperty(window, 'location', {
    value: { ...originalLocation, pathname: '/buscar', href: '' },
    writable: true,
  });
});

afterAll(() => {
  Object.defineProperty(window, 'location', {
    value: originalLocation,
    writable: true,
  });
});

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

import { fetchWithAuth } from '../../lib/fetchWithAuth';

describe('fetchWithAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'original-token' } },
    });
    window.location.href = '';
  });

  it('should add Authorization header from current session', async () => {
    mockFetch.mockResolvedValueOnce({ status: 200, ok: true });

    await fetchWithAuth('/api/test');

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/test',
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders.get('Authorization')).toBe('Bearer original-token');
  });

  it('should return response directly on non-401 status', async () => {
    mockFetch.mockResolvedValueOnce({ status: 200, ok: true, body: 'success' });

    const response = await fetchWithAuth('/api/test');

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockRefreshSession).not.toHaveBeenCalled();
  });

  it('should refresh token and retry on 401', async () => {
    // First call returns 401
    mockFetch.mockResolvedValueOnce({ status: 401, ok: false });
    // Refresh succeeds
    mockRefreshSession.mockResolvedValueOnce({
      data: { session: { access_token: 'refreshed-token' } },
      error: null,
    });
    // Retry succeeds
    mockFetch.mockResolvedValueOnce({ status: 200, ok: true });

    const response = await fetchWithAuth('/api/test');

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockRefreshSession).toHaveBeenCalledTimes(1);

    // Second call should use the refreshed token
    const retryHeaders = mockFetch.mock.calls[1][1].headers;
    expect(retryHeaders.get('Authorization')).toBe('Bearer refreshed-token');
  });

  it('should redirect to login when refresh fails', async () => {
    mockFetch.mockResolvedValueOnce({ status: 401, ok: false });
    mockRefreshSession.mockResolvedValueOnce({
      data: { session: null },
      error: new Error('Refresh failed'),
    });

    await fetchWithAuth('/api/test');

    expect(window.location.href).toContain('/login?reason=session_expired');
    expect(window.location.href).toContain('redirect=%2Fbuscar');
  });

  it('should redirect to login when retry also returns 401', async () => {
    // First call returns 401
    mockFetch.mockResolvedValueOnce({ status: 401, ok: false });
    // Refresh succeeds
    mockRefreshSession.mockResolvedValueOnce({
      data: { session: { access_token: 'refreshed-token' } },
      error: null,
    });
    // Retry also returns 401
    mockFetch.mockResolvedValueOnce({ status: 401, ok: false });

    await fetchWithAuth('/api/test');

    expect(window.location.href).toContain('/login?reason=session_expired');
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should pass custom headers along with auth header', async () => {
    mockFetch.mockResolvedValueOnce({ status: 200, ok: true });

    await fetchWithAuth('/api/test', {
      headers: { 'Content-Type': 'application/json' },
    });

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders.get('Authorization')).toBe('Bearer original-token');
    expect(callHeaders.get('Content-Type')).toBe('application/json');
  });

  it('should work without a session (no auth header)', async () => {
    mockGetSession.mockResolvedValueOnce({ data: { session: null } });
    mockFetch.mockResolvedValueOnce({ status: 200, ok: true });

    await fetchWithAuth('/api/public');

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders.get('Authorization')).toBeNull();
  });
});
