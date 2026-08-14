import { Metadata } from 'next';
import Link from 'next/link';
import LandingNavbar from '../components/landing/LandingNavbar';
import Footer from '../components/Footer';
import { QUESTIONS, CATEGORY_META, type QuestionCategory } from '@/lib/questions';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import PerguntasFilter from './PerguntasFilter';

export const metadata: Metadata = {
  title: 'Perguntas Frequentes sobre Licitações Públicas',
  description:
    'Respostas completas para 53 perguntas sobre licitações públicas: modalidades, prazos, habilitação, preços, setores e sistemas. Dados verificáveis de fontes oficiais.',
  alternates: { canonical: buildCanonical('/perguntas') },
  openGraph: {
    title: 'Perguntas Frequentes sobre Licitações Públicas | SmartLic',
    description: '53 perguntas respondidas com base na Lei 14.133/2021 e dados de fontes oficiais.',
    type: 'website',
    url: buildCanonical('/perguntas'),
    siteName: 'SmartLic',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Perguntas Frequentes sobre Licitações Públicas | SmartLic',
    description: '53 perguntas respondidas com base na Lei 14.133/2021 e dados de fontes oficiais.',
  },
};

export default function PerguntasPage() {
  /* JSON-LD: FAQPage with top 15 questions for rich snippets */
  const top15 = QUESTIONS.slice(0, 15);
  const faqLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: top15.map((q) => ({
      '@type': 'Question',
      name: q.title,
      acceptedAnswer: {
        '@type': 'Answer',
        text: q.answer.slice(0, 500),
      },
    })),
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Perguntas', item: buildCanonical('/perguntas') },
    ],
  };

  const itemListLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'Perguntas Frequentes sobre Licitações',
    numberOfItems: QUESTIONS.length,
    itemListElement: QUESTIONS.map((q, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: buildCanonical(`/perguntas/${q.slug}`),
      name: q.title,
    })),
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* Hero */}
        <section className="bg-surface-1 border-b border-[var(--border)] py-16">
          <div className="mx-auto max-w-4xl px-4 text-center">
            <nav className="text-sm text-ink-muted mb-6">
              <Link href="/" className="hover:text-ink-primary transition-colors">Início</Link>
              <span className="mx-2">›</span>
              <span className="text-ink-primary">Perguntas Frequentes</span>
            </nav>
            <h1 className="text-4xl font-bold text-ink-primary">
              Perguntas Frequentes sobre Licitações
            </h1>
            <p className="mt-4 text-lg text-ink-secondary max-w-2xl mx-auto">
              {QUESTIONS.length} perguntas respondidas com base na Lei 14.133/2021
              e dados verificáveis de fontes oficiais. Encontre respostas objetivas para suas dúvidas sobre
              contratações públicas.
            </p>
          </div>
        </section>

        {/* Content */}
        <section className="mx-auto max-w-4xl px-4 py-12">
          <PerguntasFilter questions={QUESTIONS} />

          {/* Cross-links */}
          <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link
              href="/glossario"
              className="p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 transition-colors text-center"
            >
              <p className="font-semibold text-ink-primary">Glossário</p>
              <p className="text-sm text-ink-muted mt-1">50 termos de licitações</p>
            </Link>
            <Link
              href="/calculadora"
              className="p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 transition-colors text-center"
            >
              <p className="font-semibold text-ink-primary">Calculadora</p>
              <p className="text-sm text-ink-muted mt-1">Estime oportunidades do seu setor</p>
            </Link>
            <Link
              href="/blog"
              className="p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 transition-colors text-center"
            >
              <p className="font-semibold text-ink-primary">Blog</p>
              <p className="text-sm text-ink-muted mt-1">Guias e análises aprofundadas</p>
            </Link>
          </div>

          {/* CTA */}
          <div className="mt-12 rounded-2xl bg-brand-blue p-8 text-center text-white">
            <h2 className="text-2xl font-bold">Não encontrou o que procura?</h2>
            <p className="mt-2 text-blue-100 max-w-lg mx-auto">
              Analise editais do seu setor com inteligência artificial — sem login, dado verificável.
            </p>
            <Link
              href="/consultoria-b2g?source=perguntas"
              className="mt-6 inline-block rounded-lg bg-white text-brand-blue font-semibold px-6 py-3 hover:bg-blue-50 transition-colors"
            >
              Pedir um diagnóstico à CONFENGE →
            </Link>
          </div>
        </section>

        {/* JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListLd) }} />
      </main>
      <Footer />
    </>
  );
}
