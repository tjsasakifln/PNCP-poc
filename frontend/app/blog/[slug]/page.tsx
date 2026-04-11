import { Metadata } from 'next';
import { notFound, redirect } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  getAllSlugs,
  getArticleBySlug,
  getRelatedArticles,
} from '@/lib/blog';
import BlogArticleLayout from '../../components/BlogArticleLayout';

/**
 * Normalizes a slug by stripping diacritics and decoding percent-encoded chars.
 * Enables 301 redirects from accented URLs (e.g. /blog/análise-...) to the
 * canonical ASCII slug (e.g. /blog/analise-...).
 */
function normalizeSlug(slug: string): string {
  try {
    return decodeURIComponent(slug)
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  } catch {
    return slug;
  }
}

/**
 * STORY-261 AC7/AC12: Dynamic article route with SSG, metadata, and JSON-LD.
 */

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  let article = getArticleBySlug(slug);

  if (!article) {
    const normalized = normalizeSlug(slug);
    if (normalized !== slug) {
      article = getArticleBySlug(normalized);
    }
  }

  if (!article) {
    return { title: 'Artigo não encontrado' };
  }

  const canonicalUrl = `https://smartlic.tech/blog/${slug}`;

  return {
    title: article.title,
    description: article.description,
    keywords: article.keywords,
    alternates: {
      canonical: canonicalUrl,
    },
    openGraph: {
      title: article.title,
      description: article.description,
      type: 'article',
      publishedTime: article.publishDate,
      modifiedTime: article.lastModified || article.publishDate,
      section: article.category,
      tags: article.tags,
      url: canonicalUrl,
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(article.title)}&category=${encodeURIComponent(article.category)}`,
          width: 1200,
          height: 630,
          alt: article.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: article.title,
      description: article.description,
      images: [
        `/api/og?title=${encodeURIComponent(article.title)}&category=${encodeURIComponent(article.category)}`,
      ],
    },
  };
}

export default async function BlogArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  let article = getArticleBySlug(slug);

  if (!article) {
    const normalized = normalizeSlug(slug);
    if (normalized !== slug) {
      const normalizedArticle = getArticleBySlug(normalized);
      if (normalizedArticle) {
        redirect(`/blog/${normalized}`);
      }
    }
    notFound();
  }

  const relatedArticles = getRelatedArticles(slug);

  // Dynamic import of article content component
  const ArticleContent = dynamic(
    () => import(`@/app/blog/content/${slug}`),
    {
      loading: () => (
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-surface-1 rounded w-3/4" />
          <div className="h-4 bg-surface-1 rounded w-full" />
          <div className="h-4 bg-surface-1 rounded w-5/6" />
        </div>
      ),
    },
  );

  return (
    <BlogArticleLayout article={article} relatedArticles={relatedArticles}>
      <ArticleContent />
    </BlogArticleLayout>
  );
}
