import { Metadata } from 'next';
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

        {/* Article Listing */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          <BlogListClient articles={BLOG_ARTICLES} />
        </div>
      </main>

      <Footer />
    </div>
  );
}
