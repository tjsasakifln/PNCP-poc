'use client';

import { useState, useCallback, useEffect } from 'react';
import Link from 'next/link';

const SETORES = [
  { id: 'vestuario', name: 'Vestuário e Uniformes' },
  { id: 'alimentos', name: 'Alimentos e Merenda' },
  { id: 'informatica', name: 'Hardware e Equipamentos de TI' },
  { id: 'mobiliario', name: 'Mobiliário' },
  { id: 'papelaria', name: 'Papelaria e Material de Escritório' },
  { id: 'engenharia', name: 'Engenharia, Projetos e Obras' },
  { id: 'software_desenvolvimento', name: 'Desenvolvimento de Software e Consultoria de TI' },
  { id: 'software_licencas', name: 'Licenciamento de Software Comercial' },
  { id: 'servicos_prediais', name: 'Serviços Prediais e Facilities' },
  { id: 'produtos_limpeza', name: 'Produtos de Limpeza e Higienização' },
  { id: 'medicamentos', name: 'Medicamentos e Produtos Farmacêuticos' },
  { id: 'equipamentos_medicos', name: 'Equipamentos Médico-Hospitalares' },
  { id: 'insumos_hospitalares', name: 'Insumos e Materiais Hospitalares' },
  { id: 'vigilancia', name: 'Vigilância e Segurança Patrimonial' },
  { id: 'transporte_servicos', name: 'Transporte de Pessoas e Cargas' },
  { id: 'frota_veicular', name: 'Frota e Veículos' },
  { id: 'manutencao_predial', name: 'Manutenção e Conservação Predial' },
  { id: 'engenharia_rodoviaria', name: 'Engenharia Rodoviária e Infraestrutura Viária' },
  { id: 'materiais_eletricos', name: 'Materiais Elétricos e Instalações' },
  { id: 'materiais_hidraulicos', name: 'Materiais Hidráulicos e Saneamento' },
];

// Map calculadora sector IDs (granular) to blog sector slugs (15 canonical)
const SETOR_TO_BLOG_SLUG: Record<string, string> = {
  vestuario: 'vestuario', alimentos: 'alimentos', informatica: 'informatica',
  mobiliario: 'mobiliario', papelaria: 'papelaria', engenharia: 'engenharia',
  software_desenvolvimento: 'software', software_licencas: 'software',
  servicos_prediais: 'facilities', produtos_limpeza: 'facilities',
  medicamentos: 'saude', equipamentos_medicos: 'saude', insumos_hospitalares: 'saude',
  vigilancia: 'vigilancia', transporte_servicos: 'transporte', frota_veicular: 'transporte',
  manutencao_predial: 'manutencao-predial', engenharia_rodoviaria: 'engenharia-rodoviaria',
  materiais_eletricos: 'materiais-eletricos', materiais_hidraulicos: 'materiais-hidraulicos',
};

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
  'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
  'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

// Preposição correta por UF (contração de "em" com artigo definido)
const PREP_UF: Record<string, string> = {
  AC: 'no', AM: 'no', AP: 'no', BA: 'na', CE: 'no', DF: 'no',
  ES: 'no', MA: 'no', MT: 'no', MS: 'no', PA: 'no', PB: 'na',
  PI: 'no', PR: 'no', RJ: 'no', RN: 'no', RS: 'no',
  // Sem artigo: AL, GO, MG, PE, RO, RR, SC, SE, SP, TO → "em"
};
function prepUF(uf: string): string {
  return PREP_UF[uf] ?? 'em';
}

interface DadosCalculadora {
  total_editais_mes: number;
  avg_value: number;
  p25_value: number;
  p75_value: number;
  setor_name: string;
  uf: string;
}

interface ResultadoCalculo {
  valorPerdido: number;
  coberturaAtual: number;
  totalEditais: number;
  avgValue: number;
  dados: DadosCalculadora;
}

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function CalculadoraClient() {
  const [step, setStep] = useState(1);
  const [setor, setSetor] = useState('');
  const [uf, setUf] = useState('');
  const [editaisMes, setEditaisMes] = useState(20);
  const [taxaVitoria, setTaxaVitoria] = useState(15);
  const [valorMedio, setValorMedio] = useState('100000');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultado, setResultado] = useState<ResultadoCalculo | null>(null);
  const [copied, setCopied] = useState(false);

  // STORY-432 AC5: Pre-populate from URL params for shareable links
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const s = params.get('setor');
    const u = params.get('uf');
    const a = params.get('analisa');
    if (s && SETORES.find((x) => x.id === s)) setSetor(s);
    if (u && UFS.includes(u.toUpperCase())) setUf(u.toUpperCase());
    if (a) {
      const n = parseInt(a, 10);
      if (!isNaN(n)) setEditaisMes(Math.min(200, Math.max(1, n)));
    }
  }, []);

  function getShareUrl(): string {
    if (typeof window === 'undefined') return '';
    const base = `${window.location.origin}/calculadora`;
    const p = new URLSearchParams({ setor, uf, analisa: String(editaisMes) });
    return `${base}?${p.toString()}`;
  }

  async function handleShare() {
    const url = getShareUrl();
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      window.open(url, '_blank');
    }
  }

  const canAdvanceStep1 = setor && uf;
  const canAdvanceStep2 = editaisMes > 0 && taxaVitoria > 0;
  const canCalculate = canAdvanceStep1 && canAdvanceStep2 && parseFloat(valorMedio) > 0;

  const calcular = useCallback(async () => {
    if (!canCalculate) return;

    setLoading(true);
    setError('');

    try {
      const resp = await fetch(`/api/calculadora/dados?setor=${setor}&uf=${uf}`);
      if (!resp.ok) {
        throw new Error('Erro ao buscar dados');
      }

      const dados: DadosCalculadora = await resp.json();
      const totalEditais = dados.total_editais_mes;
      const editaisNaoAnalisados = Math.max(0, totalEditais - editaisMes);
      const avgVal = dados.avg_value > 0 ? dados.avg_value : parseFloat(valorMedio);
      const taxaDecimal = taxaVitoria / 100;
      const valorPerdido = editaisNaoAnalisados * avgVal * taxaDecimal;
      const coberturaAtual = totalEditais > 0 ? Math.min(100, (editaisMes / totalEditais) * 100) : 100;

      setResultado({
        valorPerdido,
        coberturaAtual,
        totalEditais,
        avgValue: avgVal,
        dados,
      });
      setStep(4);

      // Mixpanel event
      if (typeof window !== 'undefined' && (window as any).mixpanel) {
        (window as any).mixpanel.track('calculadora_completed', {
          setor,
          uf,
          resultado_valor: valorPerdido,
          total_editais: totalEditais,
          cobertura_pct: coberturaAtual,
        });
      }
    } catch {
      setError('Não foi possível obter os dados. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }, [canCalculate, setor, uf, editaisMes, taxaVitoria, valorMedio]);

  const recalcular = () => {
    setResultado(null);
    setStep(1);
  };

  return (
    <div className="not-prose mt-8">
      {/* Step indicator */}
      {step < 4 && (
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  s === step
                    ? 'bg-blue-600 text-white'
                    : s < step
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {s < step ? '✓' : s}
              </div>
              {s < 3 && <div className={`w-12 h-0.5 ${s < step ? 'bg-green-500' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>
      )}

      {/* Step 1: Setor + UF */}
      {step === 1 && (
        <div className="space-y-6 max-w-lg mx-auto">
          <div>
            <label htmlFor="setor" className="block text-sm font-semibold text-gray-700 mb-2">
              Setor de atuação
            </label>
            <select
              id="setor"
              value={setor}
              onChange={(e) => setSetor(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Selecione seu setor</option>
              {SETORES.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="uf" className="block text-sm font-semibold text-gray-700 mb-2">
              UF principal de atuação
            </label>
            <select
              id="uf"
              value={uf}
              onChange={(e) => setUf(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Selecione o estado</option>
              {UFS.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setStep(2)}
            disabled={!canAdvanceStep1}
            className="w-full py-3 px-6 rounded-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Continuar
          </button>
        </div>
      )}

      {/* Step 2: Capacidade */}
      {step === 2 && (
        <div className="space-y-6 max-w-lg mx-auto">
          <div>
            <label htmlFor="editais" className="block text-sm font-semibold text-gray-700 mb-2">
              Editais que sua equipe analisa por mês: <span className="text-blue-600">{editaisMes}</span>
            </label>
            <input
              id="editais"
              type="range"
              min={1}
              max={200}
              value={editaisMes}
              onChange={(e) => setEditaisMes(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1</span>
              <span>200</span>
            </div>
          </div>

          <div>
            <label htmlFor="taxa" className="block text-sm font-semibold text-gray-700 mb-2">
              Taxa de vitória atual: <span className="text-blue-600">{taxaVitoria}%</span>
            </label>
            <input
              id="taxa"
              type="range"
              min={5}
              max={50}
              value={taxaVitoria}
              onChange={(e) => setTaxaVitoria(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>5%</span>
              <span>50%</span>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 py-3 px-6 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              Voltar
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={!canAdvanceStep2}
              className="flex-1 py-3 px-6 rounded-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Continuar
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Valor + Calcular */}
      {step === 3 && (
        <div className="space-y-6 max-w-lg mx-auto">
          <div>
            <label htmlFor="valor" className="block text-sm font-semibold text-gray-700 mb-2">
              Valor médio dos seus contratos (R$)
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">R$</span>
              <input
                id="valor"
                type="number"
                min={1000}
                step={1000}
                value={valorMedio}
                onChange={(e) => setValorMedio(e.target.value)}
                className="w-full rounded-lg border border-gray-300 pl-12 pr-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="100000"
              />
            </div>
          </div>

          {error && (
            <p className="text-red-600 text-sm font-medium">{error}</p>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => setStep(2)}
              className="flex-1 py-3 px-6 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              Voltar
            </button>
            <button
              onClick={calcular}
              disabled={!canCalculate || loading}
              className="flex-1 py-3 px-6 rounded-lg font-semibold text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Calculando...' : 'Calcular'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Resultado */}
      {step === 4 && resultado && (
        <div className="space-y-8 max-w-2xl mx-auto">
          {/* Shock card */}
          <div className="bg-gradient-to-br from-red-600 to-orange-500 rounded-2xl p-8 text-white text-center shadow-xl">
            <p className="text-lg opacity-90 mb-2">
              Valor de licitações de {resultado.dados.setor_name} {prepUF(resultado.dados.uf)} {resultado.dados.uf} que sua equipe
            </p>
            <p className="text-xl font-bold opacity-90 mb-4">NÃO está analisando por mês</p>
            <p className="text-5xl sm:text-6xl font-black tracking-tight">
              {formatBRL(resultado.valorPerdido)}
            </p>
          </div>

          {/* Breakdown */}
          <div className="bg-gray-50 rounded-xl p-6 space-y-3">
            <p className="text-gray-700">
              Seu setor tem <strong>{resultado.totalEditais} editais/mês</strong> {prepUF(resultado.dados.uf)} {resultado.dados.uf} — dados reais do PNCP
            </p>
            <p className="text-gray-700">
              Sua equipe cobre <strong>{resultado.coberturaAtual.toFixed(0)}%</strong> do total disponível
            </p>
            <p className="text-gray-700">
              Valor médio por edital: <strong>{formatBRL(resultado.avgValue)}</strong>
            </p>
          </div>

          {/* Comparison */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4">Sem filtro estratégico</h3>
              <ul className="space-y-2 text-gray-600">
                <li>{resultado.coberturaAtual.toFixed(0)}% de cobertura</li>
                <li>~3h/dia em triagem manual</li>
                <li>{editaisMes} editais analisados/mês</li>
              </ul>
            </div>
            <div className="bg-white border-2 border-blue-500 rounded-xl p-6 ring-2 ring-blue-100">
              <h3 className="text-lg font-bold text-blue-700 mb-4">Com SmartLic</h3>
              <ul className="space-y-2 text-gray-600">
                <li>100% dos relevantes filtrados por IA</li>
                <li>~20min/dia de revisão</li>
                <li>3x mais oportunidades analisadas</li>
              </ul>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center space-y-4">
            <Link
              href={`/signup?ref=calculadora&setor=${setor}&uf=${uf}`}
              className="inline-block w-full sm:w-auto py-4 px-8 rounded-xl font-bold text-lg text-white bg-green-600 hover:bg-green-700 transition-colors shadow-lg"
            >
              Analisar as {resultado.totalEditais} oportunidades abertas no seu setor →
            </Link>
            <p className="text-sm text-gray-500">Trial gratuito de 14 dias, sem cartão de crédito</p>
            <button
              onClick={recalcular}
              className="text-sm text-blue-600 hover:underline"
            >
              Recalcular com outros parâmetros
            </button>
            {/* STORY-432 AC5: Shareable URL */}
            <button
              onClick={handleShare}
              className="text-sm text-gray-500 hover:text-gray-700 hover:underline block mx-auto"
            >
              {copied ? '✓ Link copiado!' : '🔗 Compartilhar este resultado'}
            </button>
            {SETOR_TO_BLOG_SLUG[setor] && (
              <Link
                href={`/blog/licitacoes/${SETOR_TO_BLOG_SLUG[setor]}/${uf.toLowerCase()}`}
                className="block text-sm text-blue-600 hover:underline"
              >
                Ver todas as licitacoes de {resultado.dados.setor_name} {prepUF(uf)} {uf} →
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
