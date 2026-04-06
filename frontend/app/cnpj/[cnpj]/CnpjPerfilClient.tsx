'use client';

import Link from 'next/link';

interface Contrato {
  orgao: string;
  valor: number | null;
  data_inicio: string | null;
  descricao: string;
  esfera?: string | null;
  uf?: string | null;
}

interface Empresa {
  razao_social: string;
  cnpj: string;
  cnae_principal: string;
  porte: string;
  uf: string;
  situacao: string;
}

interface PerfilB2G {
  empresa: Empresa;
  contratos: Contrato[];
  score: string;
  setor_detectado: string;
  setor_nome: string;
  editais_abertos_setor: number;
  total_contratos_24m: number;
  valor_total_24m: number;
  ufs_atuacao: string[];
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

const SCORE_CONFIG = {
  ATIVO: {
    label: 'Ativo',
    color: 'bg-green-100 text-green-800 border-green-300',
    ringColor: 'ring-green-200',
  },
  INICIANTE: {
    label: 'Iniciante',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    ringColor: 'ring-yellow-200',
  },
  SEM_HISTORICO: {
    label: 'Sem Histórico',
    color: 'bg-gray-100 text-gray-600 border-gray-300',
    ringColor: 'ring-gray-200',
  },
} as const;

export default function CnpjPerfilClient({ perfil }: { perfil: PerfilB2G }) {
  const { empresa, contratos, score, setor_nome, editais_abertos_setor, total_contratos_24m, valor_total_24m, ufs_atuacao, aviso_legal } = perfil;

  const scoreConfig = SCORE_CONFIG[score as keyof typeof SCORE_CONFIG] || SCORE_CONFIG.SEM_HISTORICO;

  const ctaRef = `ref=cnpj&setor=${perfil.setor_detectado}&uf=${empresa.uf}`;

  // Copy by scenario
  let headline: string;
  let subheadline: string;
  let ctaText: string;
  let contextText: string;

  if (score === 'ATIVO') {
    headline = `${empresa.razao_social} — ${total_contratos_24m} contratos com o governo / ${formatBRL(valor_total_24m)} em 24 meses`;
    subheadline = `Score B2G: ATIVO. Setor principal: ${setor_nome}. ${editais_abertos_setor} editais deste setor abertos nos últimos 30 dias em ${empresa.uf}.`;
    ctaText = `Ver os editais abertos agora no seu setor →`;
    contextText = `Empresas ativas no seu setor com filtro estratégico participam de 3x mais editais com a mesma equipe. Veja as oportunidades que você está perdendo.`;
  } else if (score === 'INICIANTE') {
    headline = `${empresa.razao_social} — ${total_contratos_24m} contratos registrados / ${formatBRL(valor_total_24m)}`;
    subheadline = `Score B2G: INICIANTE. ${editais_abertos_setor} editais do seu setor abriram no último mês.`;
    ctaText = `Descobrir quais editais sua empresa pode ganhar →`;
    contextText = `Empresas do seu porte e setor que usam filtro estratégico desde o início alcançam o 5° contrato na metade do tempo. Veja o que está aberto agora.`;
  } else {
    headline = `${empresa.razao_social} — Nenhum contrato público registrado`;
    subheadline = `${editais_abertos_setor} editais do seu setor (detectado por CNAE) abriram nos últimos 30 dias.`;
    ctaText = `Ver editais para empresas como a sua →`;
    contextText = `Não ter histórico não é impedimento — é ponto de partida. MEI e microempresas têm vantagem legal em licitações até R$80k. Veja quantas abriram na sua UF este mês.`;
  }

  return (
    <div className="not-prose">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">{headline}</h1>
        <p className="text-lg text-gray-600">{subheadline}</p>
      </div>

      {/* Score Badge */}
      <div className="flex flex-wrap gap-3 mb-8">
        <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-bold border ${scoreConfig.color} ring-2 ${scoreConfig.ringColor}`}>
          Score B2G: {scoreConfig.label}
        </span>
        <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
          Setor: {setor_nome}
        </span>
        {empresa.uf && (
          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-gray-50 text-gray-700 border border-gray-200">
            {empresa.uf}
          </span>
        )}
      </div>

      {/* Company info */}
      <div className="bg-gray-50 rounded-xl p-6 mb-8">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Dados Cadastrais</h2>
        <dl className="grid sm:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-500">CNPJ</dt>
            <dd className="font-mono font-medium">{formatCnpj(empresa.cnpj)}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Razão Social</dt>
            <dd className="font-medium">{empresa.razao_social}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">CNAE Principal</dt>
            <dd>{empresa.cnae_principal || 'Não informado'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Porte</dt>
            <dd>{empresa.porte || 'Não informado'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">UF</dt>
            <dd>{empresa.uf || 'Não informado'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Situação Cadastral</dt>
            <dd>{empresa.situacao || 'Não informado'}</dd>
          </div>
        </dl>
      </div>

      {/* Stats cards */}
      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white border rounded-xl p-5 text-center">
          <p className="text-3xl font-black text-gray-900">{total_contratos_24m}</p>
          <p className="text-sm text-gray-500 mt-1">Contratos (24 meses)</p>
        </div>
        <div className="bg-white border rounded-xl p-5 text-center">
          <p className="text-3xl font-black text-gray-900">{formatBRL(valor_total_24m)}</p>
          <p className="text-sm text-gray-500 mt-1">Valor total</p>
        </div>
        <div className="bg-white border rounded-xl p-5 text-center">
          <p className="text-3xl font-black text-blue-600">{editais_abertos_setor}</p>
          <p className="text-sm text-gray-500 mt-1">Editais abertos (setor/UF)</p>
        </div>
      </div>

      {/* UFs de atuação */}
      {ufs_atuacao.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-3">UFs de Atuação</h2>
          <div className="flex flex-wrap gap-2">
            {ufs_atuacao.map((uf) => (
              <span key={uf} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                {uf}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Contracts table */}
      {contratos.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Últimos Contratos</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-2 font-semibold text-gray-600">Órgão</th>
                  <th className="text-left py-3 px-2 font-semibold text-gray-600">Esfera</th>
                  <th className="text-left py-3 px-2 font-semibold text-gray-600">Descrição</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-600">Valor</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-600">Data</th>
                </tr>
              </thead>
              <tbody>
                {contratos.map((c, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2 max-w-[200px] truncate">{c.orgao}</td>
                    <td className="py-3 px-2 whitespace-nowrap text-gray-500">{c.esfera || '—'}{c.uf ? ` (${c.uf})` : ''}</td>
                    <td className="py-3 px-2 max-w-[300px] truncate text-gray-600">{c.descricao}</td>
                    <td className="py-3 px-2 text-right whitespace-nowrap">
                      {c.valor ? formatBRL(c.valor) : '—'}
                    </td>
                    <td className="py-3 px-2 text-right whitespace-nowrap text-gray-500">
                      {c.data_inicio || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Context + CTA */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
        <p className="text-gray-700 mb-4">{contextText}</p>
        <Link
          href={`/signup?${ctaRef}`}
          className="inline-block w-full sm:w-auto py-3 px-8 rounded-xl font-bold text-white bg-green-600 hover:bg-green-700 transition-colors text-center shadow-lg"
          onClick={() => {
            if (typeof window !== 'undefined' && (window as any).mixpanel) {
              (window as any).mixpanel.track('cnpj_lookup', {
                setor_detectado: perfil.setor_detectado,
                uf: empresa.uf,
                total_contratos: total_contratos_24m,
                score,
                clicked_cta: true,
              });
            }
          }}
        >
          {ctaText}
        </Link>
        <p className="text-sm text-gray-500 mt-3">Trial gratuito de 14 dias, sem cartão de crédito</p>
      </div>

      {/* Legal notice */}
      <p className="text-xs text-gray-400 italic">{aviso_legal}</p>
    </div>
  );
}
