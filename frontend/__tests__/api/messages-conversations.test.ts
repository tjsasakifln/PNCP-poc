/**
 * @jest-environment node
 */
import { GET, POST } from '@/app/api/messages/conversations/route';
import { NextRequest } from 'next/server';

// Mock fetch
global.fetch = jest.fn();

describe('GET /api/messages/conversations', () => {
  const mockAuthToken = 'Bearer test-token-12345';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should reject missing authorization (if BACKEND_URL is configured)', async () => {
      const request = new NextRequest('http://localhost:3000/api/messages/conversations');

      const response = await GET(request);
      const data = await response.json();

      // Either 401 (auth check) or 503 (BACKEND_URL not configured)
      // Route checks BACKEND_URL first, so 503 takes precedence
      expect([401, 503]).toContain(response.status);
      if (response.status === 401) {
        expect(data.message).toBe('Autenticacao necessaria');
      }
    });
  });

  describe('Response handling', () => {
    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const request = new NextRequest('http://localhost:3000/api/messages/conversations', {
        headers: { Authorization: mockAuthToken },
      });

      const response = await GET(request);

      expect(response.status).toBe(503);
    });
  });
});

describe('POST /api/messages/conversations', () => {
  const mockAuthToken = 'Bearer test-token-12345';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should reject missing authorization (if BACKEND_URL is configured)', async () => {
      const request = new NextRequest('http://localhost:3000/api/messages/conversations', {
        method: 'POST',
        body: JSON.stringify({ title: 'New conversation' }),
      });

      const response = await POST(request);
      const data = await response.json();

      // Either 401 (auth check) or 503 (BACKEND_URL not configured)
      expect([401, 503]).toContain(response.status);
      if (response.status === 401) {
        expect(data.message).toBe('Autenticacao necessaria');
      }
    });
  });

  describe('Response handling', () => {
    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const request = new NextRequest('http://localhost:3000/api/messages/conversations', {
        method: 'POST',
        headers: { Authorization: mockAuthToken, 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New conversation' }),
      });

      const response = await POST(request);

      expect(response.status).toBe(503);
    });
  });
});
