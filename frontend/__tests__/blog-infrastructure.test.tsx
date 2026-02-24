/**
 * STORY-261 AC15: Blog infrastructure tests (20+ tests)
 *
 * Tests cover:
 * - BlogArticleLayout rendering (JSON-LD, breadcrumbs, share buttons)
 * - Blog listing page (cards, category filtering)
 * - lib/blog.ts utilities (getArticleBySlug, getRelatedArticles, calculateReadingTime)
 * - RSS route (XML generation)
 * - generateStaticParams
 */

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';

// ---------- Mock setup ----------

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  );
});

// Mock next/dynamic
jest.mock('next/dynamic', () => {
  return (loader: () => Promise<{ default: React.ComponentType }>, _options?: unknown) => {
    const Component = React.lazy(loader);
    return function DynamicComponent(props: Record<string, unknown>) {
      return (
        <React.Suspense fallback={<div>Loading...</div>}>
          <Component {...props} />
        </React.Suspense>
      );
    };
  };
});

// Mock lucide-react
jest.mock('lucide-react', () => ({
  ChevronRight: ({ className }: { className?: string }) => (
    <svg data-testid="chevron-right" className={className} />
  ),
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

// Mock LandingNavbar
jest.mock('../app/components/landing/LandingNavbar', () => {
  return function MockLandingNavbar() {
    return <nav data-testid="landing-navbar">Navbar</nav>;
  };
});

// Mock Footer
jest.mock('../app/components/Footer', () => {
  return function MockFooter() {
    return <footer data-testid="footer">Footer</footer>;
  };
});

// Mock AuthProvider
jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => ({ user: null, loading: false, session: null }),
}));

// ---------- Imports under test ----------

import {
  calculateReadingTime,
  getArticleBySlug,
  getArticlesByCategory,
  getRelatedArticles,
  getAllSlugs,
  BLOG_ARTICLES,
  type BlogArticleMeta,
} from '../lib/blog';

import BlogArticleLayout from '../app/components/BlogArticleLayout';
import BlogListClient from '../app/blog/BlogListClient';

// ---------- lib/blog.ts utility tests ----------

describe('lib/blog.ts utilities', () => {
  describe('calculateReadingTime', () => {
    it('returns "1 min de leitura" for very short content', () => {
      expect(calculateReadingTime(50)).toBe('1 min de leitura');
    });

    it('returns "1 min de leitura" for exactly 200 words', () => {
      expect(calculateReadingTime(200)).toBe('1 min de leitura');
    });

    it('returns correct reading time for 2500 words', () => {
      expect(calculateReadingTime(2500)).toBe('13 min de leitura');
    });

    it('returns correct reading time for 600 words', () => {
      expect(calculateReadingTime(600)).toBe('3 min de leitura');
    });

    it('rounds up to nearest minute', () => {
      expect(calculateReadingTime(201)).toBe('2 min de leitura');
    });

    it('returns "1 min de leitura" for 0 words', () => {
      expect(calculateReadingTime(0)).toBe('1 min de leitura');
    });
  });

  describe('getArticleBySlug', () => {
    it('returns article when slug matches', () => {
      const article = getArticleBySlug('como-aumentar-taxa-vitoria-licitacoes');
      expect(article).toBeDefined();
      expect(article?.title).toBe('Como Aumentar sua Taxa de Vitória em Licitações');
    });

    it('returns undefined for non-existent slug', () => {
      expect(getArticleBySlug('non-existent-slug')).toBeUndefined();
    });

    it('returns article with correct structure', () => {
      const article = getArticleBySlug('como-aumentar-taxa-vitoria-licitacoes');
      expect(article).toHaveProperty('slug');
      expect(article).toHaveProperty('title');
      expect(article).toHaveProperty('description');
      expect(article).toHaveProperty('category');
      expect(article).toHaveProperty('tags');
      expect(article).toHaveProperty('publishDate');
      expect(article).toHaveProperty('readingTime');
      expect(article).toHaveProperty('wordCount');
      expect(article).toHaveProperty('keywords');
      expect(article).toHaveProperty('relatedSlugs');
    });
  });

  describe('getArticlesByCategory', () => {
    it('returns articles matching category', () => {
      const articles = getArticlesByCategory('Empresas B2G');
      expect(articles.length).toBeGreaterThan(0);
      articles.forEach((a) => {
        expect(a.category).toBe('Empresas B2G');
      });
    });

    it('returns empty array for non-existent category', () => {
      expect(getArticlesByCategory('Non-Existent')).toEqual([]);
    });

    it('filters Consultorias category correctly', () => {
      const articles = getArticlesByCategory('Consultorias de Licitação');
      expect(articles.length).toBeGreaterThan(0);
      articles.forEach((a) => {
        expect(a.category).toBe('Consultorias de Licitação');
      });
    });
  });

  describe('getRelatedArticles', () => {
    it('returns related articles for valid slug', () => {
      const related = getRelatedArticles('como-aumentar-taxa-vitoria-licitacoes');
      expect(related.length).toBeGreaterThan(0);
      related.forEach((a) => {
        expect(a.slug).not.toBe('como-aumentar-taxa-vitoria-licitacoes');
      });
    });

    it('returns empty array for non-existent slug', () => {
      expect(getRelatedArticles('non-existent')).toEqual([]);
    });

    it('returns BlogArticleMeta objects', () => {
      const related = getRelatedArticles('como-aumentar-taxa-vitoria-licitacoes');
      related.forEach((a) => {
        expect(a).toHaveProperty('slug');
        expect(a).toHaveProperty('title');
      });
    });
  });

  describe('getAllSlugs', () => {
    it('returns all article slugs', () => {
      const slugs = getAllSlugs();
      expect(slugs.length).toBe(BLOG_ARTICLES.length);
      expect(slugs).toContain('como-aumentar-taxa-vitoria-licitacoes');
    });

    it('returns strings only', () => {
      const slugs = getAllSlugs();
      slugs.forEach((s) => {
        expect(typeof s).toBe('string');
      });
    });
  });

  describe('BLOG_ARTICLES integrity', () => {
    it('all articles have valid publishDate format', () => {
      BLOG_ARTICLES.forEach((a) => {
        expect(a.publishDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      });
    });

    it('all articles have non-empty tags', () => {
      BLOG_ARTICLES.forEach((a) => {
        expect(a.tags.length).toBeGreaterThan(0);
      });
    });

    it('all articles have valid category', () => {
      const validCategories = ['Empresas B2G', 'Consultorias de Licitação'];
      BLOG_ARTICLES.forEach((a) => {
        expect(validCategories).toContain(a.category);
      });
    });

    it('all relatedSlugs reference existing articles', () => {
      const allSlugs = new Set(getAllSlugs());
      BLOG_ARTICLES.forEach((a) => {
        a.relatedSlugs.forEach((rs) => {
          expect(allSlugs.has(rs)).toBe(true);
        });
      });
    });

    it('readingTime matches wordCount calculation', () => {
      BLOG_ARTICLES.forEach((a) => {
        expect(a.readingTime).toBe(calculateReadingTime(a.wordCount));
      });
    });
  });
});

// ---------- BlogArticleLayout tests ----------

describe('BlogArticleLayout', () => {
  const mockArticle: BlogArticleMeta = {
    slug: 'test-article',
    title: 'Test Article Title',
    description: 'Test description for the article.',
    category: 'Empresas B2G',
    tags: ['test', 'article'],
    publishDate: '2026-02-24',
    readingTime: '5 min de leitura',
    wordCount: 1000,
    keywords: ['test keyword'],
    relatedSlugs: [],
  };

  const mockRelated: BlogArticleMeta[] = [
    {
      slug: 'related-article',
      title: 'Related Article Title',
      description: 'Related article description.',
      category: 'Empresas B2G',
      tags: ['related'],
      publishDate: '2026-02-20',
      readingTime: '3 min de leitura',
      wordCount: 600,
      keywords: ['related'],
      relatedSlugs: [],
    },
  ];

  it('renders article title with serif font', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('Test Article Title');
    // Verify serif font is applied via inline style attribute
    expect(heading.getAttribute('style')).toContain('Georgia');
  });

  it('renders BlogPosting JSON-LD schema', () => {
    const { container } = render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) => JSON.parse(s.textContent || '{}'));
    const blogPosting = schemas.find((s) => s['@type'] === 'BlogPosting');

    expect(blogPosting).toBeDefined();
    expect(blogPosting.headline).toBe('Test Article Title');
    expect(blogPosting.author.name).toBe('SmartLic');
    expect(blogPosting.wordCount).toBe(1000);
    expect(blogPosting.articleSection).toBe('Empresas B2G');
    expect(blogPosting.inLanguage).toBe('pt-BR');
    expect(blogPosting.datePublished).toBe('2026-02-24');
  });

  it('renders BreadcrumbList JSON-LD schema', () => {
    const { container } = render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const scripts = container.querySelectorAll('script[type="application/ld+json"]');
    const schemas = Array.from(scripts).map((s) => JSON.parse(s.textContent || '{}'));
    const breadcrumbList = schemas.find((s) => s['@type'] === 'BreadcrumbList');

    expect(breadcrumbList).toBeDefined();
    expect(breadcrumbList.itemListElement).toHaveLength(4);
    expect(breadcrumbList.itemListElement[0].name).toBe('Início');
    expect(breadcrumbList.itemListElement[1].name).toBe('Blog');
    expect(breadcrumbList.itemListElement[2].name).toBe('Empresas B2G');
    expect(breadcrumbList.itemListElement[3].name).toBe('Test Article Title');
  });

  it('renders visual breadcrumb navigation', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const breadcrumb = screen.getByTestId('breadcrumb');
    expect(breadcrumb).toBeInTheDocument();
    expect(breadcrumb).toHaveTextContent('Início');
    expect(breadcrumb).toHaveTextContent('Blog');
    expect(breadcrumb).toHaveTextContent('Empresas B2G');
    expect(breadcrumb).toHaveTextContent('Test Article Title');
  });

  it('renders category badge', () => {
    const { container } = render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    // Category badge is in the article header with specific styling
    const badge = container.querySelector('header span.rounded-full');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Empresas B2G');
  });

  it('renders formatted publish date', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    expect(screen.getByText(/24 de fevereiro de 2026/i)).toBeInTheDocument();
  });

  it('renders reading time', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    expect(screen.getByText('5 min de leitura')).toBeInTheDocument();
  });

  it('renders author as Equipe SmartLic', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    expect(screen.getByText('Equipe SmartLic')).toBeInTheDocument();
  });

  it('renders article tags', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const tagsContainer = screen.getByTestId('article-tags');
    expect(tagsContainer).toBeInTheDocument();
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('article')).toBeInTheDocument();
  });

  it('renders share buttons', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const shareButtons = screen.getByTestId('share-buttons');
    expect(shareButtons).toBeInTheDocument();
    expect(screen.getByTestId('share-linkedin')).toBeInTheDocument();
    expect(screen.getByTestId('share-whatsapp')).toBeInTheDocument();
    expect(screen.getByTestId('share-copy-link')).toBeInTheDocument();
  });

  it('copy link button changes text on click', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
    });

    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const copyBtn = screen.getByTestId('share-copy-link');
    expect(copyBtn).toHaveTextContent('Copiar link');

    await act(async () => {
      fireEvent.click(copyBtn);
    });

    expect(copyBtn).toHaveTextContent('Copiado!');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'https://smartlic.tech/blog/test-article',
    );
  });

  it('renders related articles in sidebar when provided', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={mockRelated}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    const relatedSection = screen.getByTestId('related-articles');
    expect(relatedSection).toBeInTheDocument();
    expect(screen.getByText('Related Article Title')).toBeInTheDocument();
  });

  it('renders reading progress bar', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    expect(screen.getByTestId('reading-progress-bar')).toBeInTheDocument();
  });

  it('renders children content', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p data-testid="article-content">Article body content</p>
      </BlogArticleLayout>,
    );

    expect(screen.getByTestId('article-content')).toHaveTextContent(
      'Article body content',
    );
  });

  it('renders CTA card in sidebar', () => {
    render(
      <BlogArticleLayout article={mockArticle} relatedArticles={[]}>
        <p>Content</p>
      </BlogArticleLayout>,
    );

    expect(screen.getByText('Avalie licitações automaticamente')).toBeInTheDocument();
    expect(screen.getByText('Comece Grátis')).toBeInTheDocument();
  });
});

// ---------- BlogListClient tests ----------

describe('BlogListClient', () => {
  const mockArticles: BlogArticleMeta[] = [
    {
      slug: 'article-b2g',
      title: 'B2G Article',
      description: 'Description for B2G article.',
      category: 'Empresas B2G',
      tags: ['b2g'],
      publishDate: '2026-02-24',
      readingTime: '5 min de leitura',
      wordCount: 1000,
      keywords: [],
      relatedSlugs: [],
    },
    {
      slug: 'article-consultoria',
      title: 'Consultoria Article',
      description: 'Description for consultoria article.',
      category: 'Consultorias de Licitação',
      tags: ['consultoria'],
      publishDate: '2026-02-23',
      readingTime: '3 min de leitura',
      wordCount: 600,
      keywords: [],
      relatedSlugs: [],
    },
  ];

  it('renders all article cards', () => {
    render(<BlogListClient articles={mockArticles} />);

    expect(screen.getByText('B2G Article')).toBeInTheDocument();
    expect(screen.getByText('Consultoria Article')).toBeInTheDocument();
  });

  it('renders category filter tabs', () => {
    render(<BlogListClient articles={mockArticles} />);

    expect(screen.getByRole('tab', { name: 'Todos' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Empresas B2G' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Consultorias' })).toBeInTheDocument();
  });

  it('filters articles by Empresas B2G category', () => {
    render(<BlogListClient articles={mockArticles} />);

    fireEvent.click(screen.getByRole('tab', { name: 'Empresas B2G' }));

    expect(screen.getByText('B2G Article')).toBeInTheDocument();
    expect(screen.queryByText('Consultoria Article')).not.toBeInTheDocument();
  });

  it('filters articles by Consultorias category', () => {
    render(<BlogListClient articles={mockArticles} />);

    fireEvent.click(screen.getByRole('tab', { name: 'Consultorias' }));

    expect(screen.queryByText('B2G Article')).not.toBeInTheDocument();
    expect(screen.getByText('Consultoria Article')).toBeInTheDocument();
  });

  it('shows all articles when "Todos" is selected', () => {
    render(<BlogListClient articles={mockArticles} />);

    // First filter to a category
    fireEvent.click(screen.getByRole('tab', { name: 'Empresas B2G' }));
    // Then switch back to all
    fireEvent.click(screen.getByRole('tab', { name: 'Todos' }));

    expect(screen.getByText('B2G Article')).toBeInTheDocument();
    expect(screen.getByText('Consultoria Article')).toBeInTheDocument();
  });

  it('shows empty state when no articles match filter', () => {
    render(<BlogListClient articles={[]} />);

    expect(
      screen.getByText('Nenhum artigo encontrado nesta categoria.'),
    ).toBeInTheDocument();
  });

  it('sorts articles by date (most recent first)', () => {
    render(<BlogListClient articles={mockArticles} />);

    const cards = screen.getAllByTestId('blog-article-card');
    expect(cards[0]).toHaveTextContent('B2G Article');
    expect(cards[1]).toHaveTextContent('Consultoria Article');
  });

  it('renders reading time on article cards', () => {
    render(<BlogListClient articles={mockArticles} />);

    expect(screen.getByText('5 min de leitura')).toBeInTheDocument();
    expect(screen.getByText('3 min de leitura')).toBeInTheDocument();
  });
});

// ---------- RSS Feed test ----------

// Polyfill Response for jsdom
if (typeof globalThis.Response === 'undefined') {
  globalThis.Response = class MockResponse {
    body: string;
    _headers: Map<string, string>;
    status: number;
    ok: boolean;
    constructor(body: string, init?: { headers?: Record<string, string>; status?: number }) {
      this.body = body;
      this._headers = new Map(Object.entries(init?.headers || {}));
      this.status = init?.status || 200;
      this.ok = this.status >= 200 && this.status < 300;
    }
    async text() { return this.body; }
    async json() { return JSON.parse(this.body); }
    get headers() {
      const h = this._headers;
      return { get: (k: string) => h.get(k) || null };
    }
  } as unknown as typeof Response;
}

describe('RSS Feed route', () => {
  it('generates valid RSS XML', async () => {
    // Import the route handler
    const { GET } = await import('../app/blog/rss.xml/route');
    const response = await GET();
    const xml = await response.text();

    expect(response.headers.get('Content-Type')).toBe(
      'application/rss+xml; charset=utf-8',
    );
    expect(xml).toContain('<?xml version="1.0" encoding="UTF-8"?>');
    expect(xml).toContain('<rss version="2.0"');
    expect(xml).toContain('<title>SmartLic Blog</title>');
    expect(xml).toContain('<language>pt-BR</language>');
    expect(xml).toContain('<item>');
    expect(xml).toContain('como-aumentar-taxa-vitoria-licitacoes');
  });

  it('includes all blog articles in RSS feed', async () => {
    const { GET } = await import('../app/blog/rss.xml/route');
    const response = await GET();
    const xml = await response.text();

    BLOG_ARTICLES.forEach((article) => {
      expect(xml).toContain(article.slug);
    });
  });
});

// ---------- generateStaticParams test ----------

describe('generateStaticParams', () => {
  it('returns all article slugs for static generation', () => {
    const slugs = getAllSlugs();
    const staticParams = slugs.map((slug) => ({ slug }));

    expect(staticParams.length).toBe(BLOG_ARTICLES.length);
    staticParams.forEach((param) => {
      expect(param).toHaveProperty('slug');
      expect(typeof param.slug).toBe('string');
      expect(param.slug.length).toBeGreaterThan(0);
    });
  });
});
