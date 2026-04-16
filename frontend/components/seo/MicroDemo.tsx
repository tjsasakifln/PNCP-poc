'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, useInView, AnimatePresence } from 'framer-motion';

export type MicroDemoVariant = 'busca' | 'resultado' | 'viabilidade';

interface MicroDemoProps {
  variant: MicroDemoVariant;
  className?: string;
}

// ─── Busca Variant ────────────────────────────────────────────────────────────

const KEYWORDS = ['Informática', 'São Paulo', 'Pregão'];
const SOURCES = [
  { name: 'PNCP', color: 'bg-blue-500' },
  { name: 'PCP', color: 'bg-emerald-500' },
  { name: 'ComprasGov', color: 'bg-violet-500' },
];

function BuscaDemo({ play }: { play: boolean }) {
  const [typedKeywords, setTypedKeywords] = useState<string[]>([]);
  const [litSources, setLitSources] = useState<number[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!play) {
      setTypedKeywords([]);
      setLitSources([]);
      setProgress(0);
      return;
    }

    const timers: ReturnType<typeof setTimeout>[] = [];

    // Type keywords one by one
    KEYWORDS.forEach((kw, i) => {
      timers.push(setTimeout(() => {
        setTypedKeywords(prev => [...prev, kw]);
      }, 600 + i * 700));
    });

    // Light up sources
    SOURCES.forEach((_, i) => {
      timers.push(setTimeout(() => {
        setLitSources(prev => [...prev, i]);
      }, 2500 + i * 600));
    });

    // Progress bar
    timers.push(setTimeout(() => {
      let p = 0;
      const interval = setInterval(() => {
        p += 2;
        setProgress(p);
        if (p >= 100) clearInterval(interval);
      }, 30);
      timers.push(interval as unknown as ReturnType<typeof setTimeout>);
    }, 2400));

    return () => timers.forEach(t => clearTimeout(t));
  }, [play]);

  return (
    <div className="flex flex-col gap-5 p-5 h-full justify-center">
      {/* Search bar */}
      <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 shadow-sm">
        <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <div className="flex flex-wrap gap-2 flex-1 min-h-[24px]">
          <AnimatePresence>
            {typedKeywords.map((kw) => (
              <motion.span
                key={kw}
                initial={{ opacity: 0, scale: 0.8, x: -8 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-medium px-2.5 py-0.5 rounded-full"
              >
                {kw}
              </motion.span>
            ))}
          </AnimatePresence>
          {typedKeywords.length === 0 && (
            <span className="text-gray-400 text-sm">Buscar licitações...</span>
          )}
        </div>
      </div>

      {/* Sources */}
      <div className="flex gap-3">
        {SOURCES.map((src, i) => (
          <motion.div
            key={src.name}
            className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 flex-1"
            animate={litSources.includes(i) ? { borderColor: '#22c55e', backgroundColor: '#f0fdf4' } : {}}
            transition={{ duration: 0.3 }}
          >
            <motion.div
              className="w-2 h-2 rounded-full bg-gray-300"
              animate={litSources.includes(i) ? { backgroundColor: '#22c55e', scale: [1, 1.4, 1] } : {}}
              transition={{ duration: 0.4 }}
            />
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{src.name}</span>
          </motion.div>
        ))}
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1.5">
          <span>Buscando editais...</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width animated from 0 to 100% by setInterval-driven progress state */}
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full"
            style={{ width: `${progress}%` }}
            transition={{ ease: 'easeOut' }}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Resultado Variant ────────────────────────────────────────────────────────

const RESULTADO_CARDS = [
  {
    title: 'Aquisição de Equipamentos de TI — Notebooks e Periféricos',
    org: 'Prefeitura de São Paulo — SP',
    value: 'R$ 1.240.000',
    score: 92,
    scoreColor: 'bg-emerald-500',
    scoreLabel: 'text-emerald-700',
    scoreBg: 'bg-emerald-50 dark:bg-emerald-900/30',
  },
  {
    title: 'Pregão Eletrônico — Serviços de Manutenção de Infraestrutura de TI',
    org: 'Governo do Estado de São Paulo — SP',
    value: 'R$ 870.000',
    score: 78,
    scoreColor: 'bg-amber-500',
    scoreLabel: 'text-amber-700',
    scoreBg: 'bg-amber-50 dark:bg-amber-900/30',
  },
  {
    title: 'Contratação de Solução de Segurança da Informação — Firewall',
    org: 'TRE-SP — São Paulo',
    value: 'R$ 320.000',
    score: 45,
    scoreColor: 'bg-red-400',
    scoreLabel: 'text-red-700',
    scoreBg: 'bg-red-50 dark:bg-red-900/30',
  },
];

function AnimatedScore({ target, color }: { target: number; color: string }) {
  const [value, setValue] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    let v = 0;
    const interval = setInterval(() => {
      v += 3;
      if (v >= target) {
        setValue(target);
        clearInterval(interval);
      } else {
        setValue(v);
      }
    }, 20);
    return () => clearInterval(interval);
  }, [target]);

  return (
    <span className={`text-xs font-bold ${color}`}>{value}</span>
  );
}

function ResultadoDemo({ play }: { play: boolean }) {
  const [key, setKey] = useState(0);

  useEffect(() => {
    if (play) setKey(k => k + 1);
  }, [play]);

  return (
    <div className="flex flex-col gap-2.5 p-4 h-full justify-center">
      <AnimatePresence mode="wait">
        {play && (
          <motion.div key={key} className="flex flex-col gap-2.5">
            {RESULTADO_CARDS.map((card, i) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15, type: 'spring', stiffness: 260, damping: 22 }}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 flex items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{card.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{card.org}</p>
                  <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mt-0.5">{card.value}</p>
                </div>
                <div className={`shrink-0 flex flex-col items-center justify-center w-10 h-10 rounded-full ${card.scoreBg}`}>
                  <AnimatedScore target={card.score} color={card.scoreLabel} />
                  <div className={`w-5 h-1 rounded-full ${card.scoreColor} mt-0.5`} />
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Viabilidade Variant ──────────────────────────────────────────────────────

const VIABILITY_FACTORS = [
  { label: 'Modalidade', pct: 85, color: 'bg-blue-500', trackColor: 'bg-blue-100 dark:bg-blue-900/30', textColor: 'text-blue-700 dark:text-blue-300' },
  { label: 'Prazo', pct: 70, color: 'bg-emerald-500', trackColor: 'bg-emerald-100 dark:bg-emerald-900/30', textColor: 'text-emerald-700 dark:text-emerald-300' },
  { label: 'Valor', pct: 60, color: 'bg-amber-500', trackColor: 'bg-amber-100 dark:bg-amber-900/30', textColor: 'text-amber-700 dark:text-amber-300' },
  { label: 'Geografia', pct: 90, color: 'bg-violet-500', trackColor: 'bg-violet-100 dark:bg-violet-900/30', textColor: 'text-violet-700 dark:text-violet-300' },
];

const OVERALL_SCORE = 76;

function OverallScore({ play }: { play: boolean }) {
  const [val, setVal] = useState(0);

  useEffect(() => {
    if (!play) { setVal(0); return; }
    let v = 0;
    const timer = setTimeout(() => {
      const interval = setInterval(() => {
        v += 2;
        if (v >= OVERALL_SCORE) { setVal(OVERALL_SCORE); clearInterval(interval); }
        else setVal(v);
      }, 25);
      return () => clearInterval(interval);
    }, 200);
    return () => clearTimeout(timer);
  }, [play]);

  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="relative w-14 h-14 shrink-0">
        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="22" fill="none" stroke="currentColor" strokeWidth="5" className="text-gray-100 dark:text-gray-700" />
          <motion.circle
            cx="28" cy="28" r="22"
            fill="none"
            stroke="#3b82f6"
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 22}`}
            animate={play ? { strokeDashoffset: 2 * Math.PI * 22 * (1 - OVERALL_SCORE / 100) } : { strokeDashoffset: 2 * Math.PI * 22 }}
            transition={{ duration: 1.2, ease: 'easeOut', delay: 0.2 }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-gray-800 dark:text-gray-100">{val}</span>
        </div>
      </div>
      <div>
        <p className="text-xs text-gray-500">Score de Viabilidade</p>
        <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">Boa Oportunidade</p>
      </div>
    </div>
  );
}

function ViabilidadeDemo({ play }: { play: boolean }) {
  return (
    <div className="flex flex-col p-5 h-full justify-center">
      <OverallScore play={play} />
      <div className="flex flex-col gap-3">
        {VIABILITY_FACTORS.map((factor, i) => (
          <div key={factor.label} className="flex items-center gap-3">
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400 w-20 shrink-0">{factor.label}</span>
            <div className={`flex-1 h-2.5 rounded-full ${factor.trackColor} overflow-hidden`}>
              <motion.div
                className={`h-full rounded-full ${factor.color}`}
                initial={{ width: 0 }}
                animate={play ? { width: `${factor.pct}%` } : { width: 0 }}
                transition={{ duration: 0.7, delay: i * 0.2, ease: 'easeOut' }}
              />
            </div>
            <motion.span
              className={`text-xs font-semibold ${factor.textColor} w-8 text-right shrink-0`}
              initial={{ opacity: 0 }}
              animate={play ? { opacity: 1 } : { opacity: 0 }}
              transition={{ delay: i * 0.2 + 0.5 }}
            >
              {factor.pct}%
            </motion.span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

const VARIANT_LABELS: Record<MicroDemoVariant, string> = {
  busca: 'Busca Multi-Fonte',
  resultado: 'Resultados',
  viabilidade: 'Viabilidade',
};

export function MicroDemo({ variant, className = '' }: MicroDemoProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: false, margin: '-80px' });
  const [playKey, setPlayKey] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (inView) {
      setIsPlaying(true);
      setPlayKey(k => k + 1);
    } else {
      setIsPlaying(false);
    }
  }, [inView]);

  const handleReplay = () => {
    setIsPlaying(false);
    setTimeout(() => {
      setIsPlaying(true);
      setPlayKey(k => k + 1);
    }, 50);
  };

  return (
    <div
      ref={ref}
      className={`relative rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-hidden cursor-pointer select-none aspect-video ${className}`}
      onClick={handleReplay}
      title="Clique para repetir a animação"
    >
      {/* Label */}
      <div className="absolute top-3 left-3 z-10">
        <span className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-600 dark:text-gray-400 px-2.5 py-1 rounded-full">
          {VARIANT_LABELS[variant]}
        </span>
      </div>

      {/* Replay hint */}
      <div className="absolute bottom-3 right-3 z-10">
        <span className="flex items-center gap-1 bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm text-xs text-gray-400 px-2 py-0.5 rounded-full">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          repetir
        </span>
      </div>

      {/* Content */}
      <div className="h-full">
        {variant === 'busca' && <BuscaDemo key={`busca-${playKey}`} play={isPlaying} />}
        {variant === 'resultado' && <ResultadoDemo key={`resultado-${playKey}`} play={isPlaying} />}
        {variant === 'viabilidade' && <ViabilidadeDemo key={`viabilidade-${playKey}`} play={isPlaying} />}
      </div>
    </div>
  );
}
