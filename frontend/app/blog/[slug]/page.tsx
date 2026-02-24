import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  getAllSlugs,
  getArticleBySlug,
  getRelatedArticles,
} from '@/lib/blog';
import BlogArticleLayout from '../../components/BlogArticleLayout';

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
  const article = getArticleBySlug(slug);

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
  const article = getArticleBySlug(slug);

  if (!article) {
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
