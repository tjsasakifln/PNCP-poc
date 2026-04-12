import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { GLOSSARY_TERMS } from '@/lib/glossary-terms';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import { SECTORS } from '@/lib/sectors';

export const revalidate = 86400;

export function generateStaticParams() {
  return GLOSSARY_TERMS.map((t) => ({ termo: t.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ termo: string }>;
}): Promise<Metadata> {
  const { termo } = await params;
  const term = GLOSSARY_TERMS.find((t) => t.slug === termo);
  if (!term) return {};

  const title = `${term.term}: O que é e como funciona em licitações`;
  const description =
    term.definition.length > 155
      ? term.definition.slice(0, 152) + '...'
      : term.definition;

  return {
    title,
    description,
    alternates: { canonical: buildCanonical(`/glossario/${termo}`) },
    openGraph: {
      title,
      description,
      url: buildCanonical(`/glossario/${termo}`),
      type: 'article',
      siteName: 'SmartLic',
    },
    twitter: { card: 'summary_large_image', title, description },
  };
}

/* ---------------------------------------------------------------------------
 * Related sectors per glossary concept (deterministic, up to 3)
 * --------------------------------------------------------------------------- */
const TERM_SECTOR_MAP: Record<string, string[]> = {
  'pregao-eletronico': ['informatica', 'software', 'facilities'],
  'concorrencia': ['engenharia', 'engenharia-rodoviaria', 'manutencao-predial'],
  'habilitacao': ['informatica', 'saude', 'facilities'],
  'edital': ['software', 'saude', 'mobiliario'],
  'ata-de-registro-de-precos': ['alimentos', 'materiais-eletricos', 'papelaria'],
  'sistema-de-registro-de-precos': ['alimentos', 'materiais-eletricos', 'papelaria'],
  'pncp': ['software', 'informatica', 'saude'],
  'contrato-administrativo': ['facilities', 'vigilancia', 'transporte'],
  'aditivo-contratual': ['engenharia', 'manutencao-predial', 'engenharia-rodoviaria'],
  'fiscalizacao': ['facilities', 'saude', 'manutencao-predial'],
  'garantia-contratual': ['engenharia', 'engenharia-rodoviaria', 'transporte'],
  'me-epp': ['papelaria', 'vestuario', 'alimentos'],
  'medicao': ['engenharia', 'facilities', 'manutencao-predial'],
  'bdi': ['engenharia', 'engenharia-rodoviaria', 'materiais-eletricos'],
  'atestado-de-capacidade-tecnica': ['engenharia', 'saude', 'software'],
  'proposta-tecnica': ['software', 'saude', 'engenharia'],
  'proposta-comercial': ['informatica', 'mobiliario', 'vestuario'],
  'pregão-eletrônico': ['informatica', 'software', 'facilities'],
};

function getRelatedSectors(slug: string) {
  const sectorSlugs = TERM_SECTOR_MAP[slug] ?? [];
  return sectorSlugs
    .map((s) => SECTORS.find((sec) => sec.slug === s))
    .filter(Boolean) as typeof SECTORS;
}

/* ---------------------------------------------------------------------------
 * Page component
 * --------------------------------------------------------------------------- */
export default async function GlossaryTermPage({
  params,
}: {
  params: Promise<{ termo: string }>;
}) {
  const { termo } = await params;
  const term = GLOSSARY_TERMS.find((t) => t.slug === termo);

  if (!term) {
    notFound();
  }

  const relatedTermObjects = (term.relatedTerms ?? [])
    .map((slug) => GLOSSARY_TERMS.find((t) => t.slug === slug))
    .filter(Boolean) as typeof GLOSSARY_TERMS;

  const relatedSectors = getRelatedSectors(termo);

  /* JSON-LD: BreadcrumbList */
  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: SITE_URL,
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Glossário',
        item: buildCanonical('/glossario'),
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: term.term,
        item: buildCanonical(`/glossario/${termo}`),
      },
    ],
  };

  /* JSON-LD: DefinedTerm */
  const definedTermLd = {
    '@context': 'https://schema.org',
    '@type': 'DefinedTerm',
    name: term.term,
    description: term.definition,
    inDefinedTermSet: {
      '@type': 'DefinedTermSet',
      name: 'Glossário de Licitações SmartLic',
      url: buildCanonical('/glossario'),
    },
    url: buildCanonical(`/glossario/${termo}`),
  };

  /* JSON-LD: FAQPage */
  const faqLd = term.faqEntries && term.faqEntries.length > 0
    ? {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: term.faqEntries.map((faq) => ({
          '@type': 'Question',
          name: faq.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: faq.answer,
          },
        })),
      }
    : null;

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(definedTermLd) }}
      />
      {faqLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }}
        />
      )}

      <main className="flex-1">
        {/* ── Hero / Header ── */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
            {/* Breadcrumbs */}
            <nav aria-label="Breadcrumb" className="mb-5">
              <ol className="flex flex-wrap items-center gap-1.5 text-sm text-ink-secondary">
                <li>
                  <Link href="/" className="hover:text-brand-blue transition-colors">
                    Home
                  </Link>
                </li>
                <li aria-hidden="true" className="text-ink-tertiary">
                  /
                </li>
                <li>
                  <Link href="/glossario" className="hover:text-brand-blue transition-colors">
                    Glossário
                  </Link>
                </li>
                <li aria-hidden="true" className="text-ink-tertiary">
                  /
                </li>
                <li className="font-medium text-ink" aria-current="page">
                  {term.term}
                </li>
              </ol>
            </nav>

            <h1 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight mb-3">
              {term.term}
            </h1>

            {term.legalBasis && (
              <p className="text-sm text-ink-secondary">
                <span className="font-medium">Base legal:</span>{' '}
                <span className="italic">{term.legalBasis}</span>
              </p>
            )}
          </div>
        </div>

        {/* ── Main content ── */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
            {/* Left — primary content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Definition */}
              <section aria-labelledby="definicao-heading">
                <h2
                  id="definicao-heading"
                  className="text-lg font-bold text-brand-blue mb-3"
                >
                  Definição
                </h2>
                <p className="text-ink-secondary leading-relaxed">
                  {term.definition}
                </p>
              </section>

              {/* Example box */}
              <section aria-labelledby="exemplo-heading">
                <h2
                  id="exemplo-heading"
                  className="text-lg font-bold text-brand-blue mb-3"
                >
                  Exemplo prático
                </h2>
                <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4">
                  <span className="font-semibold text-ink text-sm">Exemplo: </span>
                  <span className="text-ink-secondary text-sm leading-relaxed">
                    {term.example}
                  </span>
                </div>
              </section>

              {/* FAQ */}
              {term.faqEntries && term.faqEntries.length > 0 && (
                <section aria-labelledby="faq-heading">
                  <h2
                    id="faq-heading"
                    className="text-lg font-bold text-brand-blue mb-4"
                  >
                    Perguntas frequentes
                  </h2>
                  <div className="space-y-4">
                    {term.faqEntries.map((faq, idx) => (
                      <div
                        key={idx}
                        className="border border-[var(--border)] rounded-lg overflow-hidden"
                      >
                        <div className="bg-surface-1 px-4 py-3 border-b border-[var(--border)]">
                          <p className="font-semibold text-ink text-sm">
                            {faq.question}
                          </p>
                        </div>
                        <div className="px-4 py-3">
                          <p className="text-ink-secondary text-sm leading-relaxed">
                            {faq.answer}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* CTA */}
              <section className="rounded-2xl bg-brand-blue p-6 sm:p-8 text-center">
                <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">
                  Encontre editais abertos agora
                </h2>
                <p className="text-white/85 max-w-sm mx-auto mb-5 text-sm leading-relaxed">
                  O SmartLic monitora PNCP diariamente e classifica licitações por setor automaticamente.
                </p>
                <Link
                  href="/signup?source=glossario-termo"
                  className="inline-flex items-center gap-2 bg-white text-brand-blue px-6 py-3 rounded-lg font-semibold text-sm hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
                >
                  Testar gratis por 14 dias &rarr;
                </Link>
              </section>
            </div>

            {/* Right sidebar */}
            <aside className="space-y-6">
              {/* Related terms */}
              {relatedTermObjects.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold text-ink uppercase tracking-wider mb-3">
                    Termos relacionados
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {relatedTermObjects.map((related) => (
                      <Link
                        key={related.slug}
                        href={`/glossario/${related.slug}`}
                        className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-surface-1 border border-[var(--border)] text-ink-secondary hover:text-brand-blue hover:border-brand-blue/40 transition-colors"
                      >
                        {related.term}
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Related sectors */}
              {relatedSectors.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold text-ink uppercase tracking-wider mb-3">
                    Editais por setor
                  </h3>
                  <div className="flex flex-col gap-2">
                    {relatedSectors.map((sector) => (
                      <Link
                        key={sector.slug}
                        href={`/licitacoes/${sector.slug}`}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-1 border border-[var(--border)] text-ink-secondary hover:text-brand-blue hover:border-brand-blue/40 transition-colors text-sm"
                      >
                        <span className="flex-1">{sector.name}</span>
                        <span className="text-ink-tertiary text-xs">&rarr;</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Guide link */}
              <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4">
                <p className="text-xs text-ink-tertiary uppercase tracking-wider font-semibold mb-2">
                  Guia relacionado
                </p>
                <Link
                  href={term.guideHref}
                  className="text-brand-blue hover:underline text-sm font-medium"
                >
                  {term.guideLabel} &rarr;
                </Link>
              </div>

              {/* Back to glossary */}
              <Link
                href="/glossario"
                className="flex items-center gap-2 text-sm text-ink-secondary hover:text-brand-blue transition-colors"
              >
                <span aria-hidden="true">&larr;</span>
                Voltar ao Glossário completo
              </Link>
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
