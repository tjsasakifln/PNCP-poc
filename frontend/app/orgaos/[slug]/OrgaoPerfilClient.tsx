'use client';

import Link from 'next/link';

interface LicitacaoRecente {
  objeto_compra: string;
  modalidade_nome: string;
  valor_total_estimado: number | null;
  data_publicacao: string;
  uf: string;
}

interface ModalidadeCount {
  nome: string;
  count: number;
}

interface FornecedorTop {
  nome: string;
  cnpj: string;
  total_contratos: number;
  valor_total: number;
}

interface OrgaoStats {
  nome: string;
  cnpj: string;
  esfera: string;
  uf: string;
  municipio: string;
  total_licitacoes: number;
  licitacoes_30d: number;
  licitacoes_90d: number;
  licitacoes_365d: number;
  valor_medio_estimado: number;
  valor_total_estimado: number;
  top_modalidades: ModalidadeCount[];
  top_setores: string[];
  ultimas_licitacoes: LicitacaoRecente[];
  top_fornecedores?: FornecedorTop[];
  total_contratos_24m?: number;
  valor_total_contratos_24m?: number;
  aviso_legal: string;
}

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCnpj(cnpj: string): string {
  if (cnpj.length !== 14) return cnpj;
  return `${cnpj.slice(0, 2)}.${cnpj.slice(2, 5)}.${cnpj.slice(5, 8)}/${cnpj.slice(8, 12)}-${cnpj.slice(12)}`;
}

const ACTIVITY_CONFIG = {
  MUITO_ATIVO: {
    label: 'Muito Ativo',
    color: 'bg-green-100 text-green-800 border-green-300',
    ringColor: 'ring-green-200',
  },
  ATIVO: {
    label: 'Ativo',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    ringColor: 'ring-yellow-200',
  },
  INATIVO: {
    label: 'Sem Atividade Recente',
    color: 'bg-gray-100 text-gray-600 border-gray-300',
    ringColor: 'ring-gray-200',
  },
} as const;

export default function OrgaoPerfilClient({ stats }: { stats: OrgaoStats }) {
  const {
    nome,
    cnpj,
    esfera,
    uf,
    municipio,
    total_licitacoes,
    licitacoes_30d,
    licitacoes_90d,
    licitacoes_365d,
    valor_medio_estimado,
    top_modalidades,
    top_setores,
    ultimas_licitacoes,
    top_fornecedores,
    total_contratos_24m,
    valor_total_contratos_24m,
    aviso_legal,
  } = stats;

  // Determine activity level
  const activityKey =
    licitacoes_30d >= 10 ? 'MUITO_ATIVO' : licitacoes_30d >= 1 ? 'ATIVO' : 'INATIVO';
  const activityConfig = ACTIVITY_CONFIG[activityKey];

  // Copy by scenario
  let headline: string;
  let subheadline: string;
  let ctaText: string;
  let contextText: string;

  if (licitacoes_30d >= 10) {
    headline = `${nome} — ${total_licitacoes} licitações publicadas`;
    subheadline = `Órgão muito ativo: ${licitacoes_30d} editais publicados nos últimos 30 dias. Valor médio estimado: ${formatBRL(valor_medio_estimado)}.`;
    ctaText = `Acompanhar novos editais deste órgão →`;
    contextText = `Este órgão publica editais com frequência elevada. Empresas que monitoram órgãos ativos respondem às oportunidades antes dos concorrentes e aumentam a taxa de vitória.`;
  } else if (licitacoes_30d >= 1) {
    headline = `${nome} — ${total_licitacoes} licitações publicadas`;
    subheadline = `Órgão ativo: ${licitacoes_30d} edital(is) publicado(s) nos últimos 30 dias. Valor médio estimado: ${formatBRL(valor_medio_estimado)}.`;
    ctaText = `Ver editais abertos deste órgão →`;
    contextText = `Este órgão publicou editais recentemente. Fique por dentro das próximas oportunidades e prepare sua empresa para participar com antecedência.`;
  } else {
    headline = `${nome} — Nenhuma licitação publicada nos últimos 30 dias`;
    subheadline = `Nenhuma licitação publicada nos últimos 30 dias. Total histórico: ${total_licitacoes} licitações.`;
    ctaText = `Buscar editais em órgãos similares →`;
    contextText = `Este órgão não publicou editais recentemente. Use o SmartLic para monitorar quando voltarem a publicar ou encontre órgãos similares na sua região que estão ativos agora.`;
  }

  return (
    <div className="not-prose">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">{headline}</h1>
        <p className="text-lg text-gray-600">{subheadline}</p>
      </div>

      {/* Badges row */}
      <div className="flex flex-wrap gap-3 mb-8">
        <span
          className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-bold border ${activityConfig.color} ring-2 ${activityConfig.ringColor}`}
        >
          {activityConfig.label}
        </span>
        {esfera && (
          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
            {esfera}
          </span>
        )}
        {uf && (
          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 border border-gray-200">
            {uf}
          </span>
        )}
      </div>

      {/* Stats cards */}
      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white border rounded-xl p-5 text-center">
          <p className="text-3xl font-black text-gray-900">{total_licitacoes}</p>
          <p className="text-sm text-gray-500 mt-1">Total de licitações</p>
        </div>
        <div className="bg-white border rounded-xl p-5 text-center">
          <p className="text-3xl font-black text-blue-600">{licitacoes_30d}</p>
          <p className="text-sm text-gray-500 mt-1">Últimos 30 dias</p>
        </div>
        <div className="bg-white border rounded-xl p-5 text-center">
          <p className="text-3xl font-black text-gray-900">{formatBRL(valor_medio_estimado)}</p>
          <p className="text-sm text-gray-500 mt-1">Valor médio estimado</p>
        </div>
      </div>

      {/* Org info card */}
      <div className="bg-gray-50 rounded-xl p-6 mb-8">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Dados do Órgão</h2>
        <dl className="grid sm:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-500">CNPJ</dt>
            <dd className="font-mono font-medium">{formatCnpj(cnpj)}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Nome</dt>
            <dd className="font-medium">{nome}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Esfera</dt>
            <dd>{esfera || 'Não informado'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">UF</dt>
            <dd>{uf || 'Não informado'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Município</dt>
            <dd>{municipio || 'Não informado'}</dd>
          </div>
        </dl>
      </div>

      {/* Activity breakdown */}
      <div className="bg-white border rounded-xl p-5 mb-8">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Atividade por Período</h2>
        <div className="flex flex-wrap gap-6">
          <div className="text-center">
            <p className="text-2xl font-black text-gray-900">{licitacoes_30d}</p>
            <p className="text-sm text-gray-500">30 dias</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-black text-gray-900">{licitacoes_90d}</p>
            <p className="text-sm text-gray-500">90 dias</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-black text-gray-900">{licitacoes_365d}</p>
            <p className="text-sm text-gray-500">365 dias</p>
          </div>
        </div>
      </div>

      {/* Top modalidades */}
      {top_modalidades.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-3">Modalidades Mais Utilizadas</h2>
          <ul className="space-y-2">
            {top_modalidades.map((m) => (
              <li key={m.nome} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3">
                <span className="text-gray-700">{m.nome}</span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
                  {m.count}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Top setores */}
      {top_setores.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-3">Setores Frequentes</h2>
          <div className="flex flex-wrap gap-2">
            {top_setores.map((setor) => (
              <span
                key={setor}
                className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium border border-blue-100"
              >
                {setor}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Últimas licitações table */}
      {ultimas_licitacoes.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Últimas Licitações</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-2 font-semibold text-gray-600">Objeto</th>
                  <th className="text-left py-3 px-2 font-semibold text-gray-600">Modalidade</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-600">Valor Estimado</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-600">Data</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-600">UF</th>
                </tr>
              </thead>
              <tbody>
                {ultimas_licitacoes.map((l, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2 max-w-[300px] truncate text-gray-700">{l.objeto_compra}</td>
                    <td className="py-3 px-2 whitespace-nowrap text-gray-500">{l.modalidade_nome}</td>
                    <td className="py-3 px-2 text-right whitespace-nowrap">
                      {l.valor_total_estimado != null ? formatBRL(l.valor_total_estimado) : '—'}
                    </td>
                    <td className="py-3 px-2 text-right whitespace-nowrap text-gray-500">
                      {l.data_publicacao || '—'}
                    </td>
                    <td className="py-3 px-2 text-right whitespace-nowrap text-gray-500">
                      {l.uf || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Contratos Firmados — spending data from pncp_supplier_contracts */}
      {total_contratos_24m != null && total_contratos_24m > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Contratos Firmados (24 meses)</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="bg-white border rounded-xl p-5 text-center">
              <p className="text-3xl font-black text-gray-900">{total_contratos_24m}</p>
              <p className="text-sm text-gray-500 mt-1">Contratos assinados</p>
            </div>
            <div className="bg-white border rounded-xl p-5 text-center">
              <p className="text-3xl font-black text-gray-900">
                {valor_total_contratos_24m ? formatBRL(valor_total_contratos_24m) : 'N/D'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Valor total contratado</p>
            </div>
          </div>
        </div>
      )}

      {/* SEO-Sprint2 P7.3: Link para contratos históricos deste órgão */}
      {total_contratos_24m != null && total_contratos_24m > 0 && (
        <div className="mb-6">
          <Link
            href={`/contratos/orgao/${cnpj}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 transition-colors text-sm font-medium"
          >
            Ver {total_contratos_24m.toLocaleString('pt-BR')} contratos históricos deste órgão →
          </Link>
        </div>
      )}

      {/* Principais Fornecedores */}
      {top_fornecedores && top_fornecedores.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Principais Fornecedores</h2>
          <p className="text-sm text-gray-500 mb-3">
            Empresas com maior volume de contratos assinados com {nome} (últimos 24 meses).
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-2 font-semibold text-gray-600">Empresa</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-600">Contratos</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-600">Valor Total</th>
                </tr>
              </thead>
              <tbody>
                {top_fornecedores.map((f, i) => (
                  <tr key={f.cnpj} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2">
                      <Link
                        href={`/fornecedores/${f.cnpj}`}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {f.nome || formatCnpj(f.cnpj)}
                      </Link>
                      <span className="block text-xs text-gray-400 font-mono">{formatCnpj(f.cnpj)}</span>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
                        {f.total_contratos}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-right font-medium text-gray-900">
                      {formatBRL(f.valor_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-400 mt-2 italic">
            Fonte: PNCP — contratos assinados e publicados no portal.
          </p>
        </div>
      )}

      {/* CTA block */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
        <p className="text-gray-700 mb-4">{contextText}</p>
        <Link
          href={`/signup?ref=orgao&uf=${uf}`}
          className="inline-block w-full sm:w-auto py-3 px-8 rounded-xl font-bold text-white bg-green-600 hover:bg-green-700 transition-colors text-center shadow-lg"
          onClick={() => {
            if (typeof window !== 'undefined' && (window as any).mixpanel) {
              (window as any).mixpanel.track('orgao_lookup', {
                cnpj: stats.cnpj,
                uf: stats.uf,
                total_licitacoes: stats.total_licitacoes,
                clicked_cta: true,
              });
            }
          }}
        >
          {ctaText}
        </Link>
        <p className="text-sm text-gray-500 mt-3">Trial gratuito de 14 dias, sem cartão de crédito</p>
      </div>

      {/* Aviso legal */}
      <p className="text-xs text-gray-400 italic">{aviso_legal}</p>
    </div>
  );
}
