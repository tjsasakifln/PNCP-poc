import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getAuthorBySlug, getAllAuthorSlugs } from '@/lib/authors';
import { getArticlesByAuthor } from '@/lib/blog';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 3600;

export function generateStaticParams() {
  return getAllAuthorSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const author = getAuthorBySlug(slug);
  if (!author) return {};

  const title = `${author.name} — ${author.role}`;
  const description = author.shortBio;

  return {
    title,
    description,
    alternates: { canonical: buildCanonical(`/blog/author/${slug}`) },
    openGraph: {
      title,
      description,
      url: buildCanonical(`/blog/author/${slug}`),
      type: 'profile',
      siteName: 'SmartLic',
      images: [{ url: author.image, width: 400, height: 400, alt: author.name }],
    },
    twitter: { card: 'summary', title, description },
  };
}

export default async function AuthorPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const author = getAuthorBySlug(slug);
  if (!author) notFound(); // adr-seo-001-allow: slug not in static author catalog — true 404

  const articles = getArticlesByAuthor(slug);

  const personLd = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: author.name,
    url: buildCanonical(`/blog/author/${slug}`),
    image: author.image,
    jobTitle: author.role,
    description: author.bio,
    sameAs: author.sameAs,
    worksFor: {
      '@type': 'Organization',
      name: 'CONFENGE Avaliações e Inteligência Artificial LTDA',
      url: SITE_URL,
    },
    knowsAbout: author.knowsAbout,
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Blog', item: buildCanonical('/blog') },
      { '@type': 'ListItem', position: 3, name: author.name, item: buildCanonical(`/blog/author/${slug}`) },
    ],
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* Hero */}
        <section className="bg-surface-1 border-b border-[var(--border)] py-16">
          <div className="mx-auto max-w-4xl px-4">
            <nav className="text-sm text-ink-muted mb-6">
              <Link href="/" className="hover:text-ink-primary transition-colors">Início</Link>
              <span className="mx-2">›</span>
              <Link href="/blog" className="hover:text-ink-primary transition-colors">Blog</Link>
              <span className="mx-2">›</span>
              <span className="text-ink-primary">{author.name}</span>
            </nav>

            <div className="flex flex-col sm:flex-row items-start gap-6">
              <div className="w-24 h-24 rounded-full bg-brand-blue/10 flex items-center justify-center text-3xl font-bold text-brand-blue flex-shrink-0">
                {author.name.split(' ').map((n: string) => n[0]).join('')}
              </div>
              <div>
                <h1 className="text-3xl font-bold text-ink-primary">{author.name}</h1>
                <p className="text-lg text-brand-blue font-medium mt-1">{author.role}</p>
                <p className="text-ink-secondary mt-3 max-w-2xl leading-relaxed">{author.bio}</p>

                {/* Social links */}
                <div className="flex gap-4 mt-4">
                  {author.socialLinks.linkedin && (
                    <a href={author.socialLinks.linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-ink-muted hover:text-brand-blue transition-colors">
                      LinkedIn ↗
                    </a>
                  )}
                  {author.socialLinks.github && (
                    <a href={author.socialLinks.github} target="_blank" rel="noopener noreferrer" className="text-sm text-ink-muted hover:text-brand-blue transition-colors">
                      GitHub ↗
                    </a>
                  )}
                  <Link href={`/blog/author/${slug}/rss.xml`} className="text-sm text-ink-muted hover:text-brand-blue transition-colors">
                    RSS Feed ↗
                  </Link>
                </div>
              </div>
            </div>

            {/* Credentials */}
            <div className="flex flex-wrap gap-2 mt-6">
              {author.credentials.map((c: string) => (
                <span key={c} className="px-3 py-1 rounded-full text-xs font-medium bg-brand-blue/10 text-brand-blue">
                  {c}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Articles */}
        <section className="mx-auto max-w-4xl px-4 py-12">
          <h2 className="text-2xl font-bold text-ink-primary mb-8">
            Artigos publicados ({articles.length})
          </h2>
          <div className="space-y-6">
            {articles
              .sort((a: { publishDate: string }, b: { publishDate: string }) => new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime())
              .map((article: { slug: string; category: string; publishDate: string; readingTime: string; title: string; description: string }) => (
                <Link
                  key={article.slug}
                  href={`/blog/${article.slug}`}
                  className="block p-6 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 hover:shadow-sm transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-surface-1 text-ink-muted">
                      {article.category}
                    </span>
                    <time className="text-xs text-ink-muted">{article.publishDate}</time>
                    <span className="text-xs text-ink-muted">{article.readingTime}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-ink-primary group-hover:text-brand-blue">
                    {article.title}
                  </h3>
                  <p className="text-sm text-ink-secondary mt-2 line-clamp-2">{article.description}</p>
                </Link>
              ))}
          </div>

          {/* CTA */}
          <div className="mt-12 rounded-2xl bg-brand-blue p-8 text-center text-white">
            <h2 className="text-2xl font-bold">Descubra editais do seu setor</h2>
            <p className="mt-2 text-blue-100 max-w-lg mx-auto">
              Análise de viabilidade com IA para cada edital — sem login, dado verificável.
            </p>
            <Link
              href="/consultoria-b2g?source=author"
              className="mt-6 inline-block rounded-lg bg-white text-brand-blue font-semibold px-6 py-3 hover:bg-blue-50 transition-colors"
            >
              Pedir um diagnóstico à CONFENGE →
            </Link>
          </div>
        </section>

        {/* JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(personLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
      </main>
      <Footer />
    </>
  );
}
