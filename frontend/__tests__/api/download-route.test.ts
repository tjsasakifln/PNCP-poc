/**
 * @jest-environment node
 */
import { GET } from '@/app/api/download/route';
import { NextRequest } from 'next/server';

describe('GET /api/download - STORY-202 Signed URL Feature', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_APP_NAME = 'SmartLic.tech';
  });

  describe('Authentication', () => {
    it('should require Bearer token', async () => {
      const request = new NextRequest('http://localhost:3000/api/download?id=test-123');

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.message).toContain('Autenticacao necessaria');
    });

    it('should reject non-Bearer auth', async () => {
      const request = new NextRequest('http://localhost:3000/api/download?id=test-123', {
        headers: { Authorization: 'Basic dXNlcjpwYXNz' },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.message).toContain('Autenticacao necessaria');
    });
  });

  describe('X-Request-ID header (STORY-202 SYS-M01)', () => {
    it('should log X-Request-ID if present', async () => {
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();

      const request = new NextRequest('http://localhost:3000/api/download?url=https://storage.example.com/file.xlsx', {
        headers: {
          Authorization: 'Bearer token',
          'X-Request-ID': 'req-12345',
        },
      });

      await GET(request);

      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('req-12345'));
      consoleLogSpy.mockRestore();
    });

    it('should work without X-Request-ID', async () => {
      const request = new NextRequest('http://localhost:3000/api/download?url=https://storage.example.com/file.xlsx', {
        headers: { Authorization: 'Bearer token' },
      });

      const response = await GET(request);

      expect(response.status).toBe(307); // Redirect
    });
  });

  describe('Signed URL redirect (STORY-202 CROSS-C02 Priority 1)', () => {
    it('should redirect to signed URL when url param provided', async () => {
      const signedUrl = 'https://storage.example.com/file.xlsx?signature=abc123';

      const request = new NextRequest(
        `http://localhost:3000/api/download?url=${encodeURIComponent(signedUrl)}`,
        { headers: { Authorization: 'Bearer token' } }
      );

      const response = await GET(request);

      expect(response.status).toBe(307); // Redirect
      expect(response.headers.get('Location')).toBe(signedUrl);
    });

    it('should log signed URL redirect', async () => {
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
      const signedUrl = 'https://storage.example.com/file.xlsx';

      const request = new NextRequest(
        `http://localhost:3000/api/download?url=${encodeURIComponent(signedUrl)}`,
        { headers: { Authorization: 'Bearer token' } }
      );

      await GET(request);

      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Redirecting to signed URL'));
      consoleLogSpy.mockRestore();
    });
  });

  describe('Legacy filesystem download (Priority 2)', () => {
    it('should return 400 when neither id nor url provided', async () => {
      const request = new NextRequest('http://localhost:3000/api/download', {
        headers: { Authorization: 'Bearer token' },
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toContain('obrigatório');
    });
  });
});
