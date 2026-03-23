import { CheckCircle2, XCircle, MapPin, Calendar, DollarSign, Building2, TrendingUp, AlertTriangle } from 'lucide-react';
import AnimateOnScroll from '@/components/ui/AnimateOnScroll';

interface ProofOfValueProps {
  className?: string;
}

// GTM-COPY-003 AC5+AC10: Static data — realistic examples covering different sectors and UFs
const recommendedBid = {
  title: 'Pregão Eletrônico — Manutenção predial com fornecimento de materiais',
  valor: 'R$ 380.000,00',
  uf: 'SP',
  modalidade: 'Pregão Eletrônico',
  orgao: 'Tribunal Regional do Trabalho — 2ª Região',
  prazo: '18 dias restantes',
  compatibilidade: 92,
  viabilidade: 'Alta',
  justificativas: [
    { icon: 'setor', text: 'Setor compatível: manutenção predial' },
    { icon: 'valor', text: 'Valor dentro da faixa ideal do seu perfil (R$ 100k–500k)' },
    { icon: 'prazo', text: 'Prazo viável: 18 dias para preparar proposta' },
    { icon: 'regiao', text: 'Região de atuação: São Paulo' },
  ],
};

const rejectedBid = {
  title: 'Pregão Eletrônico — Manutenção preventiva e corretiva de sistemas prediais em unidades de saúde',
  valor: 'R$ 420.000,00',
  uf: 'SP',
  modalidade: 'Pregão Eletrônico',
  motivos: [
    { icon: 'setor', text: 'Exige atestado técnico em engenharia hospitalar — fora da sua especialidade' },
    { icon: 'valor', text: 'Requer capacidade técnica comprovada acima de R$ 1,2M' },
    { icon: 'prazo', text: 'Prazo para envio de proposta: 2 dias — insuficiente para preparação' },
  ],
};

function JustificativaIcon({ tipo }: { tipo: string }) {
  const iconClass = 'w-4 h-4 flex-shrink-0';
  switch (tipo) {
    case 'setor': return <Building2 className={`${iconClass} text-emerald-600`} />;
    case 'valor': return <DollarSign className={`${iconClass} text-emerald-600`} />;
    case 'prazo': return <Calendar className={`${iconClass} text-emerald-600`} />;
    case 'regiao': return <MapPin className={`${iconClass} text-emerald-600`} />;
    default: return <CheckCircle2 className={`${iconClass} text-emerald-600`} />;
  }
}

function RejectionIcon({ tipo }: { tipo: string }) {
  const iconClass = 'w-4 h-4 flex-shrink-0';
  switch (tipo) {
    case 'setor': return <Building2 className={`${iconClass} text-red-400`} />;
    case 'valor': return <DollarSign className={`${iconClass} text-red-400`} />;
    case 'prazo': return <Calendar className={`${iconClass} text-red-400`} />;
    case 'regiao': return <MapPin className={`${iconClass} text-red-400`} />;
    default: return <AlertTriangle className={`${iconClass} text-red-400`} />;
  }
}

/**
 * GTM-COPY-003: Proof of Value — Real recommendation example
 * DEBT-2: Converted to RSC with AnimateOnScroll client islands.
 */
export default function ProofOfValue({ className = '' }: ProofOfValueProps) {
  return (
    <section
      id="proof-of-value"
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      {/* Section Header */}
      <AnimateOnScroll threshold={0.15}>
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight mb-4">
            Veja como o filtro funciona na prática
          </h2>
          {/* AC7: Mechanism explanation */}
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto">
            O SmartLic cruza o perfil da sua empresa com cada edital publicado.
            Avalia setor, valor, prazo e região. Entrega apenas o que tem aderência — com a explicação do porquê.
          </p>
        </div>
      </AnimateOnScroll>

      {/* Cards Grid: Recommended + Rejected */}
      <div className="grid md:grid-cols-5 gap-6 items-start">
        {/* AC2+AC3: Recommended Bid Card — 60% width */}
        <AnimateOnScroll
          delay={100}
          className="md:col-span-3 bg-surface-0 border-2 border-emerald-200 dark:border-emerald-700/50 rounded-2xl p-6 sm:p-8 shadow-md hover:-translate-y-1 hover:shadow-lg"
        >
          {/* Header with compatibility badge */}
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">
                Recomendada
              </span>
            </div>
            {/* AC2: Compatibility badge */}
            <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-900/30 px-3 py-1.5 rounded-full">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-bold text-emerald-700 dark:text-emerald-400 tabular-nums">
                {recommendedBid.compatibilidade}% compatível
              </span>
            </div>
          </div>

          {/* Bid details */}
          <h3 className="text-lg font-semibold text-ink mb-3 leading-snug">
            {recommendedBid.title}
          </h3>

          <div className="flex flex-wrap gap-3 mb-5 text-sm text-ink-secondary">
            <span className="inline-flex items-center gap-1.5 bg-surface-1 px-2.5 py-1 rounded-md">
              <DollarSign className="w-3.5 h-3.5" />
              {recommendedBid.valor}
            </span>
            <span className="inline-flex items-center gap-1.5 bg-surface-1 px-2.5 py-1 rounded-md">
              <MapPin className="w-3.5 h-3.5" />
              {recommendedBid.uf}
            </span>
            <span className="inline-flex items-center gap-1.5 bg-surface-1 px-2.5 py-1 rounded-md">
              <Calendar className="w-3.5 h-3.5" />
              {recommendedBid.prazo}
            </span>
            <span className="inline-flex items-center gap-1.5 bg-surface-1 px-2.5 py-1 rounded-md">
              <Building2 className="w-3.5 h-3.5" />
              {recommendedBid.modalidade}
            </span>
          </div>

          {/* AC3: Justification criteria */}
          <div className="border-t border-emerald-100 dark:border-emerald-800/30 pt-4">
            <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide mb-3">
              Por que foi recomendada:
            </p>
            <ul className="space-y-2">
              {recommendedBid.justificativas.map((j, i) => (
                <li key={i} className="flex items-center gap-2.5 text-sm text-ink-secondary">
                  <JustificativaIcon tipo={j.icon} />
                  <span>{j.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Viability seal */}
          <div className="mt-4 inline-flex items-center gap-2 bg-emerald-50 dark:bg-emerald-900/20 px-3 py-1.5 rounded-md">
            <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">
              Viabilidade: {recommendedBid.viabilidade}
            </span>
          </div>
        </AnimateOnScroll>

        {/* AC4: Rejected Bid Card — 40% width, subdued */}
        <AnimateOnScroll
          delay={200}
          visibleClass="opacity-75 translate-y-0"
          className="md:col-span-2 bg-surface-0 border border-red-200/50 dark:border-red-800/30 rounded-2xl p-6 shadow-sm"
        >
          {/* Header */}
          <div className="flex items-center gap-2 mb-4">
            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <span className="text-sm font-semibold text-red-500 dark:text-red-400 uppercase tracking-wide">
              Descartada automaticamente
            </span>
          </div>

          {/* Bid details */}
          <h3 className="text-base font-medium text-ink-secondary mb-3 leading-snug">
            {rejectedBid.title}
          </h3>

          <div className="flex flex-wrap gap-2 mb-4 text-xs text-ink-muted">
            <span className="inline-flex items-center gap-1 bg-surface-1 px-2 py-1 rounded-md">
              <DollarSign className="w-3 h-3" />
              {rejectedBid.valor}
            </span>
            <span className="inline-flex items-center gap-1 bg-surface-1 px-2 py-1 rounded-md">
              <MapPin className="w-3 h-3" />
              {rejectedBid.uf}
            </span>
          </div>

          {/* Rejection reasons */}
          <div className="border-t border-red-100 dark:border-red-900/20 pt-3">
            <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide mb-2">
              Motivos do descarte:
            </p>
            <ul className="space-y-2">
              {rejectedBid.motivos.map((m, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-ink-muted">
                  <RejectionIcon tipo={m.icon} />
                  <span>{m.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Visual indicator */}
          <p className="mt-4 text-xs text-red-400 italic">
            Parecia perfeita, mas te custaria horas para descobrir sozinho.
          </p>
        </AnimateOnScroll>
      </div>

      {/* AC6: Transparency annotation */}
      <AnimateOnScroll
        delay={300}
        hiddenClass="opacity-0"
        visibleClass="opacity-100"
      >
        <p className="text-xs text-ink-muted text-center mt-8 italic">
          Exemplo ilustrativo baseado em análises reais do sistema. Dados anonimizados.
        </p>
      </AnimateOnScroll>
    </section>
  );
}
