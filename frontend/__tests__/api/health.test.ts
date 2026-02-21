/**
 * @jest-environment node
 */
import { GET } from '@/app/api/health/route';

// Mock fetch
global.fetch = jest.fn();

describe('GET /api/health', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    delete process.env.BACKEND_URL;
  });

  describe('Backend connectivity checks', () => {
    it('should return healthy status when backend is reachable and ready', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'healthy', ready: true, uptime_seconds: 42.5 }),
      });

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('healthy');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-backend:8000/health',
        expect.objectContaining({
          headers: { Accept: 'application/json' },
        })
      );
    });

    it('should return unhealthy backend when backend returns non-200', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('unhealthy');
    });

    it('should return unreachable when backend has network error', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('unreachable');
    });

    it('should return unreachable when fetch times out', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      const abortError = new Error('The operation was aborted');
      abortError.name = 'AbortError';
      (global.fetch as jest.Mock).mockRejectedValue(abortError);

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('unreachable');
    });

    it('should return not configured when BACKEND_URL is missing', async () => {
      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('not configured');
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('Timeout behavior', () => {
    it('should use AbortController for timeout', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      let capturedSignal: AbortSignal | undefined;

      (global.fetch as jest.Mock).mockImplementation((_url, options) => {
        capturedSignal = options.signal;
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'healthy', ready: true }),
        });
      });

      await GET();

      expect(capturedSignal).toBeDefined();
      expect(capturedSignal).toBeInstanceOf(AbortSignal);
    });
  });

  describe('Error handling', () => {
    it('should handle non-Error exceptions gracefully', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      (global.fetch as jest.Mock).mockRejectedValue('string error');

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('unreachable');
    });
  });

  // CRIT-010 T5-T6: Startup readiness detection
  describe('CRIT-010: Startup readiness', () => {
    it('T5: should return backend "starting" when ready is false', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'healthy', ready: false, uptime_seconds: 0 }),
      });

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('starting');
    });

    it('T6: should return backend "healthy" when ready is true', async () => {
      process.env.BACKEND_URL = 'http://test-backend:8000';

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'healthy', ready: true, uptime_seconds: 15.3 }),
      });

      const response = await GET();
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.backend).toBe('healthy');
    });
  });
});
