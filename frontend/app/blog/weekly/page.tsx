import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const metadata: Metadata = {
  title: 'Digest Semanal de Licitações',
  description:
    'Resumo semanal das licitações publicadas no PNCP. Acompanhe os editais publicados, setores em destaque e volume financeiro semana a semana.',
  alternates: { canonical: buildCanonical('/blog/weekly') },
  openGraph: {
    title: 'Digest Semanal de Licitações | SmartLic',
    description:
      'Resumo semanal das licitações publicadas no PNCP, com análise por setor, estado e modalidade.',
    type: 'website',
    locale: 'pt_BR',
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface WeekEntry {
  year: number;
  week: number;
  slug: string;
  periodStart: Date;
  periodEnd: Date;
}

function getISOWeekStart(year: number, week: number): Date {
  // ISO week: Monday of the week containing the first Thursday of the year
  const jan4 = new Date(year, 0, 4);
  const startOfWeek1 = new Date(jan4);
  startOfWeek1.setDate(jan4.getDate() - jan4.getDay() + 1); // Monday
  const result = new Date(startOfWeek1);
  result.setDate(startOfWeek1.getDate() + (week - 1) * 7);
  return result;
}

function buildRecentWeeks(count: number): WeekEntry[] {
  const today = new Date();
  const iso = getISOCalendar(today);
  const entries: WeekEntry[] = [];

  let year = iso.year;
  let week = iso.week;

  for (let i = 0; i < count; i++) {
    const periodStart = getISOWeekStart(year, week);
    const periodEnd = new Date(periodStart);
    periodEnd.setDate(periodStart.getDate() + 6);

    entries.push({
      year,
      week,
      slug: `${year}-w${String(week).padStart(2, '0')}`,
      periodStart,
      periodEnd,
    });

    // Go to previous week
    week -= 1;
    if (week < 1) {
      year -= 1;
      week = getMaxISOWeek(year);
    }
  }

  return entries;
}

function getISOCalendar(date: Date): { year: number; week: number } {
  // Thursday of the current week determines the year
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const week1 = new Date(d.getFullYear(), 0, 4);
  const weekNum =
    1 +
    Math.round(
      ((d.getTime() - week1.getTime()) / 86400000 -
        3 +
        ((week1.getDay() + 6) % 7)) /
        7
    );
  return { year: d.getFullYear(), week: weekNum };
}

function getMaxISOWeek(year: number): number {
  const dec28 = new Date(year, 11, 28);
  return getISOCalendar(dec28).week;
}

function formatPeriodShort(start: Date, end: Date): string {
  const fmt = (d: Date) =>
    d.toLocaleDateString('pt-BR', {
      day: 'numeric',
      month: 'short',
      timeZone: 'UTC',
    });
  return `${fmt(start)} – ${fmt(end)}`;
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function WeeklyDigestIndexPage() {
  const weeks = buildRecentWeeks(12);
  const current = weeks[0];
  const past = weeks.slice(1);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            {/* Breadcrumbs */}
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/" className="hover:text-brand-blue transition-colors">Home</Link>
              <span>/</span>
              <Link href="/blog" className="hover:text-brand-blue transition-colors">Blog</Link>
              <span>/</span>
              <span className="text-ink">Digest Semanal</span>
            </nav>

            <h1 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight mb-3">
              Digest Semanal de Licitações
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl">
              Resumo semanal das publicações no PNCP — volume financeiro, setores em
              destaque e análise por estado.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
          {/* Current week highlight */}
          <section>
            <h2 className="text-base font-semibold text-ink-secondary uppercase tracking-wider mb-4">
              Esta Semana
            </h2>
            <Link
              href={`/blog/weekly/${current.slug}`}
              className="block bg-brand-blue/5 border border-brand-blue/20 rounded-2xl p-6 hover:bg-brand-blue/10 transition-colors group"
            >
              <div className="inline-flex items-center gap-2 bg-brand-blue text-white text-xs font-semibold px-2.5 py-1 rounded-full mb-3">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
                </span>
                Ao vivo
              </div>
              <h3 className="text-xl font-bold text-ink group-hover:text-brand-blue transition-colors mb-1">
                Semana {current.week} / {current.year}
              </h3>
              <p className="text-sm text-ink-secondary">
                {formatPeriodShort(current.periodStart, current.periodEnd)}
              </p>
            </Link>
          </section>

          {/* Past weeks grid */}
          <section>
            <h2 className="text-base font-semibold text-ink-secondary uppercase tracking-wider mb-4">
              Edições Anteriores
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {past.map((entry) => (
                <Link
                  key={entry.slug}
                  href={`/blog/weekly/${entry.slug}`}
                  className="flex flex-col bg-surface-1 border border-[var(--border)] rounded-xl p-5 hover:border-brand-blue/40 hover:bg-surface-2 transition-colors group"
                >
                  <span className="text-xs text-ink-secondary font-medium mb-1">
                    {entry.year}
                  </span>
                  <span className="text-base font-semibold text-ink group-hover:text-brand-blue transition-colors mb-1">
                    Semana {entry.week}
                  </span>
                  <span className="text-sm text-ink-secondary">
                    {formatPeriodShort(entry.periodStart, entry.periodEnd)}
                  </span>
                </Link>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="bg-surface-1 border border-[var(--border)] rounded-2xl p-8 text-center">
            <h2 className="text-xl font-bold text-ink mb-2">
              Não perca nenhum edital relevante
            </h2>
            <p className="text-ink-secondary mb-6 max-w-lg mx-auto text-sm">
              Além do digest semanal, o SmartLic monitora novos editais em tempo real e
              avisa você assim que surgirem oportunidades para o seu setor.
            </p>
            <Link
              href="/consultoria-b2g"
              className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-brand-blue text-white font-semibold hover:bg-brand-blue/90 transition-colors text-sm"
            >
              Pedir um diagnóstico à CONFENGE
            </Link>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
