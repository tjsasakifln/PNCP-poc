/**
 * @jest-environment node
 */
import { GET } from '@/app/api/og/indice-municipal/route';

// Mock next/og
jest.mock('next/og', () => ({
  ImageResponse: jest.fn().mockImplementation((element, options) => ({
    __type: 'ImageResponse',
    options,
  })),
}));

const { ImageResponse } = require('next/og');

function makeRequest(params: Record<string, string>) {
  const url = new URL('http://localhost/api/og/indice-municipal');
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  return new Request(url.toString());
}

describe('GET /api/og/indice-municipal', () => {
  beforeEach(() => ImageResponse.mockClear());

  it('retorna ImageResponse 1200x630', async () => {
    const req = makeRequest({ cidade: 'São Paulo', uf: 'SP', score: '75', periodo: '2026-Q1' });
    await GET(req as any);
    expect(ImageResponse).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ width: 1200, height: 630 })
    );
  });

  it('trata score ausente sem erro', async () => {
    const req = makeRequest({ cidade: 'Campinas', uf: 'SP' });
    await GET(req as any);
    expect(ImageResponse).toHaveBeenCalledTimes(1);
  });

  it('trata score 0 (cor vermelha)', async () => {
    const req = makeRequest({ cidade: 'Test', uf: 'RJ', score: '0' });
    await GET(req as any);
    expect(ImageResponse).toHaveBeenCalledTimes(1);
  });

  it('trata score 100 (cor verde)', async () => {
    const req = makeRequest({ cidade: 'Test', uf: 'MG', score: '100' });
    await GET(req as any);
    expect(ImageResponse).toHaveBeenCalledTimes(1);
  });

  it('inclui ranking_nacional quando fornecido', async () => {
    const req = makeRequest({ cidade: 'Curitiba', uf: 'PR', score: '80', ranking_nacional: '5' });
    await GET(req as any);
    expect(ImageResponse).toHaveBeenCalledTimes(1);
  });
});
