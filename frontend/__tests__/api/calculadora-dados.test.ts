/**
 * @jest-environment node
 *
 * STORY-432 AC8: Testes do endpoint proxy /api/calculadora/dados
 * Verifica roteamento correto ao backend, parâmetros obrigatórios e headers CORS.
 */

import { GET, OPTIONS } from '@/app/api/calculadora/dados/route';
import { NextRequest } from 'next/server';

global.fetch = jest.fn();

const MOCK_DADOS = {
  total_editais_mes: 342,
  avg_value: 185000,
  p25_value: 45000,
  p75_value: 320000,
  setor_name: 'Saúde',
  uf: 'SP',
};

describe('GET /api/calculadora/dados — STORY-432 AC8', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.BACKEND_URL = 'http://test-backend:8000';
  });

  afterEach(() => {
    delete process.env.BACKEND_URL;
  });

  it('retorna 200 com dados quando setor e uf são válidos', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_DADOS,
    });

    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?setor=saude&uf=SP'
    );
    const response = await GET(req);

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.total_editais_mes).toBe(342);
    expect(data.setor_name).toBe('Saúde');
  });

  it('chamou o backend com os parâmetros corretos', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_DADOS,
    });

    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?setor=informatica&uf=RJ'
    );
    await GET(req);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('setor=informatica'),
      expect.any(Object)
    );
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('uf=RJ'),
      expect.any(Object)
    );
  });

  it('retorna 400 quando setor está ausente', async () => {
    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?uf=SP'
    );
    const response = await GET(req);
    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.message).toBeDefined();
  });

  it('retorna 400 quando uf está ausente', async () => {
    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?setor=saude'
    );
    const response = await GET(req);
    expect(response.status).toBe(400);
  });

  it('repassa status do backend em caso de erro (ex: 422)', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 422,
      text: async () => 'Setor inválido',
    });

    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?setor=invalido&uf=SP'
    );
    const response = await GET(req);
    expect(response.status).toBe(422);
  });

  it('retorna 502 quando backend está inacessível', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('ECONNREFUSED'));

    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?setor=saude&uf=SP'
    );
    const response = await GET(req);
    expect(response.status).toBe(502);
  });

  it('inclui header CORS Access-Control-Allow-Origin: * na resposta', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_DADOS,
    });

    const req = new NextRequest(
      'http://localhost:3000/api/calculadora/dados?setor=saude&uf=SP'
    );
    const response = await GET(req);

    expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
  });
});

describe('OPTIONS /api/calculadora/dados — preflight CORS', () => {
  it('retorna 204 com headers CORS corretos', async () => {
    const response = await OPTIONS();
    expect(response.status).toBe(204);
    expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    expect(response.headers.get('Access-Control-Allow-Methods')).toContain('GET');
  });
});
