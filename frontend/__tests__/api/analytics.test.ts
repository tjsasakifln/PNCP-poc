/**
 * @jest-environment node
 */
import { GET } from '@/app/api/analytics/route';
import { NextRequest } from 'next/server';

// Mock fetch
global.fetch = jest.fn();

describe('GET /api/analytics', () => {
  const mockAuthToken = 'Bearer test-token-12345';

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.BACKEND_URL = 'http://test-backend:8000';
  });

  describe('Endpoint validation', () => {
    it('should reject missing endpoint parameter', async () => {
      const request = new NextRequest('http://localhost:3000/api/analytics', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Invalid endpoint');
    });

    it('should reject invalid endpoint', async () => {
      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=invalid', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Invalid endpoint');
    });

    it('should accept "summary" endpoint', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ total: 100 }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);

      expect(response.status).toBe(200);
    });

    it('should accept "searches-over-time" endpoint', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=searches-over-time', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);

      expect(response.status).toBe(200);
    });

    it('should accept "top-dimensions" endpoint', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ dimensions: [] }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=top-dimensions', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);

      expect(response.status).toBe(200);
    });
  });

  describe('Authentication', () => {
    it('should reject missing authorization header', async () => {
      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary');

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.error).toBe('Unauthorized');
    });

    it('should pass authorization header to backend', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ total: 100 }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      await GET(request);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: { Authorization: mockAuthToken },
        })
      );
    });
  });

  describe('Backend URL configuration', () => {
    it('should return 503 when BACKEND_URL not configured', async () => {
      delete process.env.BACKEND_URL;
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data.error).toBe('Servidor nao configurado');
      expect(consoleErrorSpy).toHaveBeenCalledWith(expect.stringContaining('BACKEND_URL'));

      consoleErrorSpy.mockRestore();
      process.env.BACKEND_URL = 'http://test-backend:8000';
    });

    it('should construct correct backend URL', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ total: 100 }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      await GET(request);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-backend:8000/analytics/summary',
        expect.any(Object)
      );
    });
  });

  describe('Query parameter forwarding', () => {
    it('should forward query params to backend (excluding endpoint)', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const request = new NextRequest(
        'http://localhost:3000/api/analytics?endpoint=summary&start_date=2026-01-01&end_date=2026-01-31',
        { headers: { Authorization: mockAuthToken } }
      );

      await GET(request);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-backend:8000/analytics/summary?start_date=2026-01-01&end_date=2026-01-31',
        expect.any(Object)
      );
    });

    it('should handle endpoint without additional params', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ total: 0 }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      await GET(request);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-backend:8000/analytics/summary',
        expect.any(Object)
      );
    });

    it('should handle multiple query parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const request = new NextRequest(
        'http://localhost:3000/api/analytics?endpoint=top-dimensions&dimension=uf&limit=10&order=desc',
        { headers: { Authorization: mockAuthToken } }
      );

      await GET(request);

      const calledUrl = (global.fetch as jest.Mock).mock.calls[0][0];
      expect(calledUrl).toContain('dimension=uf');
      expect(calledUrl).toContain('limit=10');
      expect(calledUrl).toContain('order=desc');
      expect(calledUrl).not.toContain('endpoint=');
    });
  });

  describe('Backend response handling', () => {
    it('should return backend data on success', async () => {
      const mockData = { total: 150, breakdown: { SC: 50, RS: 100 } };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toEqual(mockData);
    });

    it('should handle backend errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => 'Internal server error',
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Internal server error');
    });

    it('should handle non-JSON backend responses', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(502);
      expect(data.error).toBe('Resposta inesperada do servidor');
    });

    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(502);
      expect(data.error).toBe('Falha ao conectar com o servidor');
    });
  });

  describe('HTTP status code forwarding', () => {
    it('should forward 401 Unauthorized from backend', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => 'Invalid token',
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: 'Bearer invalid-token' },
      });

      const response = await GET(request);

      expect(response.status).toBe(401);
    });

    it('should forward 403 Forbidden from backend', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
        text: async () => 'Access denied',
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);

      expect(response.status).toBe(403);
    });

    it('should forward 404 Not Found from backend', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        text: async () => 'Analytics data not found',
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);

      expect(response.status).toBe(404);
    });
  });

  describe('Edge cases', () => {
    it('should handle empty analytics data', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ total: 0, data: [] }),
      });

      const request = new NextRequest('http://localhost:3000/api/analytics?endpoint=summary', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.total).toBe(0);
    });

    it('should handle special characters in query params', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const request = new NextRequest(
        'http://localhost:3000/api/analytics?endpoint=summary&search=teste%20com%20espaços',
        { headers: { Authorization: mockAuthToken } }
      );

      const response = await GET(request);

      expect(response.status).toBe(200);
    });
  });
});
