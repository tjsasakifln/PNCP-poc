/**
 * STORY-432 AC4: Tests for Calculator API CORS headers.
 * Uses Node environment because Next.js API route uses the Web API Response global.
 *
 * @jest-environment node
 */

describe('Calculadora CORS — STORY-432 AC4', () => {
  it('OPTIONS handler retorna 204 com CORS headers', async () => {
    const { OPTIONS } = await import('@/app/api/calculadora/dados/route');
    const resp = await OPTIONS();
    expect(resp.status).toBe(204);
    const headers = Object.fromEntries(resp.headers.entries());
    expect(headers['access-control-allow-origin']).toBe('*');
    expect(headers['access-control-allow-methods']).toContain('GET');
  });
});
