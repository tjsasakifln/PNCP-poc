import { Metadata } from 'next';
import Link from 'next/link';
import { BLOG_ARTICLES } from '@/lib/blog';
import LandingNavbar from '../components/landing/LandingNavbar';
import Footer from '../components/Footer';
import BlogListClient from './BlogListClient';

/**
 * STORY-261 AC4/AC5: Blog listing page with hero, category filters, and article grid.
 */

export const metadata: Metadata = {
  title: 'Blog — Inteligência em Licitações Públicas',
  description:
    'Artigos, guias e análises sobre licitações públicas para empresas B2G e consultorias. Estratégias baseadas em dados para aumentar sua taxa de vitória.',
  alternates: {
    canonical: 'https://smartlic.tech/blog',
  },
  openGraph: {
    title: 'Blog SmartLic — Inteligência em Licitações',
    description:
      'Conteúdo premium sobre estratégia, análise e inteligência em licitações públicas.',
    type: 'website',
  },
};

export default function BlogPage() {
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <main className="flex-1">
        {/* Hero Section */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 lg:py-20 text-center">
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              Inteligência em Licitações
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl mx-auto leading-relaxed">
              Artigos, guias e análises para empresas e consultorias que
              disputam contratos públicos
            </p>
          </div>
        </div>

        {/* SEO: Free tools cross-links — distributes PageRank to high-conversion pages */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 sm:pt-12">
          <h2 className="text-lg font-semibold text-ink mb-4">Ferramentas Gratuitas</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {[
              { href: '/calculadora', title: 'Calculadora de Licitacoes', desc: 'Estime valores e prazos com dados reais do PNCP' },
              { href: '/cnpj', title: 'Consulta CNPJ B2G', desc: 'Veja o historico de licitacoes de qualquer empresa' },
              { href: '/glossario', title: 'Glossario de Licitacoes', desc: '50+ termos explicados de forma pratica' },
            ].map((tool) => (
              <Link
                key={tool.href}
                href={tool.href}
                className="group p-4 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors"
              >
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-brand-blue-subtle/50 text-brand-blue">
                  Ferramenta
                </span>
                <h3 className="mt-2 text-sm font-semibold text-ink group-hover:text-brand-blue transition-colors">
                  {tool.title}
                </h3>
                <p className="mt-1 text-xs text-ink-secondary">{tool.desc}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Article Listing */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8 sm:pb-12">
          <BlogListClient articles={BLOG_ARTICLES} />
        </div>
      </main>

      <Footer />
    </div>
  );
}
