/**
 * STORY-261 AC6: Blog article metadata index and utilities
 *
 * Central registry for all blog articles. Provides access patterns
 * used by listing page, dynamic route, RSS feed, and sitemap.
 */

export type BlogCategory = 'Empresas B2G' | 'Consultorias de Licitação';

export interface BlogArticleMeta {
  slug: string;
  title: string;
  description: string;
  category: BlogCategory;
  tags: string[];
  publishDate: string;
  readingTime: string;
  wordCount: number;
  keywords: string[];
  relatedSlugs: string[];
}

/**
 * Calculate reading time based on word count (~200 words/minute).
 */
export function calculateReadingTime(wordCount: number): string {
  const minutes = Math.max(1, Math.ceil(wordCount / 200));
  return `${minutes} min de leitura`;
}

/**
 * Central article metadata registry.
 * STORY-262 and STORY-263 will populate with 30 articles.
 */
export const BLOG_ARTICLES: BlogArticleMeta[] = [
  {
    slug: 'como-aumentar-taxa-vitoria-licitacoes',
    title: 'Como Aumentar sua Taxa de Vitória em Licitações',
    description:
      'Estratégias baseadas em dados para melhorar sua taxa de sucesso em licitações públicas. Aprenda a selecionar editais com maior probabilidade de retorno.',
    category: 'Empresas B2G',
    tags: ['estratégia', 'taxa de vitória', 'seleção de editais'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2500),
    wordCount: 2500,
    keywords: [
      'como aumentar taxa de vitória em licitações',
      'como ganhar licitação pública',
      'estratégia licitação',
    ],
    relatedSlugs: [
      'erro-operacional-perder-contratos',
      'consultoria-licitacao-ferramenta-digital',
    ],
  },
  {
    slug: 'erro-operacional-perder-contratos',
    title: 'Erros Operacionais que Fazem Empresas Perderem Contratos Públicos',
    description:
      'Os 7 erros mais comuns que levam empresas B2G a perderem licitações que poderiam vencer. Análise com base em dados de milhares de processos.',
    category: 'Empresas B2G',
    tags: ['erros comuns', 'contratos públicos', 'gestão operacional'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'erros em licitações',
      'como não perder licitação',
      'erros operacionais licitação pública',
    ],
    relatedSlugs: [
      'como-aumentar-taxa-vitoria-licitacoes',
      'consultoria-licitacao-ferramenta-digital',
    ],
  },
  {
    slug: 'consultoria-licitacao-ferramenta-digital',
    title: 'Ferramentas Digitais para Consultorias de Licitação',
    description:
      'Como consultorias especializadas em licitações podem escalar suas operações com inteligência artificial e automação.',
    category: 'Consultorias de Licitação',
    tags: [
      'consultoria',
      'ferramentas digitais',
      'automação',
      'inteligência artificial',
    ],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2200),
    wordCount: 2200,
    keywords: [
      'consultoria de licitação',
      'ferramenta para licitação',
      'automação licitações públicas',
    ],
    relatedSlugs: [
      'como-aumentar-taxa-vitoria-licitacoes',
      'erro-operacional-perder-contratos',
    ],
  },
];

export function getArticleBySlug(slug: string): BlogArticleMeta | undefined {
  return BLOG_ARTICLES.find((article) => article.slug === slug);
}

export function getArticlesByCategory(category: string): BlogArticleMeta[] {
  return BLOG_ARTICLES.filter((article) => article.category === category);
}

export function getRelatedArticles(slug: string): BlogArticleMeta[] {
  const article = getArticleBySlug(slug);
  if (!article) return [];
  return article.relatedSlugs
    .map((relSlug) => getArticleBySlug(relSlug))
    .filter((a): a is BlogArticleMeta => a !== undefined);
}

export function getAllSlugs(): string[] {
  return BLOG_ARTICLES.map((article) => article.slug);
}
