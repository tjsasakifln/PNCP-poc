import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getMasterclassByTema, getAllMasterclassTemas } from '@/lib/masterclasses';
import { getAuthorBySlug } from '@/lib/authors';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import MasterclassClient from './MasterclassClient';

export const revalidate = 86400; // ISR 24h

export function generateStaticParams() {
  return getAllMasterclassTemas().map((tema) => ({ tema }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ tema: string }>;
}): Promise<Metadata> {
  const { tema } = await params;
  const mc = getMasterclassByTema(tema);
  if (!mc) return {};

  const title = `${mc.title} | Masterclass SmartLic`;
  const description = mc.description;
  const canonical = buildCanonical(`/masterclass/${tema}`);
  const ogImage = `${SITE_URL}/api/og?title=${encodeURIComponent(mc.title)}&subtitle=Masterclass+Gratuita`;

  return {
    title,
    description,
    keywords: mc.keywords,
    alternates: { canonical },
    openGraph: {
      title,
      description,
      url: canonical,
      type: 'video.other',
      siteName: 'SmartLic',
      images: [{ url: ogImage, width: 1200, height: 630, alt: mc.title }],
    },
    twitter: { card: 'summary_large_image', title, description },
  };
}

const LEVEL_LABEL: Record<string, string> = {
  iniciante: 'Iniciante',
  intermediario: 'Intermediário',
  avancado: 'Avançado',
};

const LEVEL_COLOR: Record<string, string> = {
  iniciante: 'bg-green-100 text-green-800',
  intermediario: 'bg-yellow-100 text-yellow-800',
  avancado: 'bg-purple-100 text-purple-800',
};

export default async function MasterclassPage({
  params,
}: {
  params: Promise<{ tema: string }>;
}) {
  const { tema } = await params;
  const mc = getMasterclassByTema(tema);
  if (!mc) notFound();

  const author = getAuthorBySlug(mc.instructor);
  const canonical = buildCanonical(`/masterclass/${tema}`);
  const ogImage = `${SITE_URL}/api/og?title=${encodeURIComponent(mc.title)}&subtitle=Masterclass+Gratuita`;

  // JSON-LD @graph with Event + VideoObject + Course + BreadcrumbList
  const graphLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Event',
        name: mc.title,
        description: mc.description,
        url: canonical,
        eventStatus: 'https://schema.org/EventScheduled',
        eventAttendanceMode: 'https://schema.org/OnlineEventAttendanceMode',
        location: {
          '@type': 'VirtualLocation',
          url: canonical,
        },
        organizer: {
          '@type': 'Organization',
          name: 'SmartLic',
          url: SITE_URL,
        },
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'BRL',
          availability: 'https://schema.org/InStock',
          url: canonical,
        },
        duration: mc.duration,
        inLanguage: 'pt-BR',
      },
      {
        '@type': 'VideoObject',
        name: mc.title,
        description: mc.description,
        thumbnailUrl: ogImage,
        uploadDate: '2026-04-01',
        duration: mc.duration,
        contentUrl: canonical,
        embedUrl: canonical,
        inLanguage: 'pt-BR',
        isAccessibleForFree: true,
        author: author
          ? {
              '@type': 'Person',
              name: author.name,
              url: buildCanonical(`/blog/author/${author.slug}`),
              image: author.image,
            }
          : undefined,
      },
      {
        '@type': 'Course',
        name: mc.title,
        description: mc.description,
        url: canonical,
        inLanguage: 'pt-BR',
        isAccessibleForFree: true,
        provider: {
          '@type': 'Organization',
          name: 'SmartLic',
          url: SITE_URL,
        },
        hasCourseInstance: {
          '@type': 'CourseInstance',
          courseMode: 'online',
          courseWorkload: mc.duration,
        },
        teaches: mc.topics,
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Início', item: SITE_URL },
          { '@type': 'ListItem', position: 2, name: 'Masterclasses', item: buildCanonical('/masterclass') },
          { '@type': 'ListItem', position: 3, name: mc.title, item: canonical },
        ],
      },
    ],
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* Hero */}
        <section className="bg-gradient-to-br from-brand-blue via-blue-700 to-blue-900 py-16 text-white">
          <div className="mx-auto max-w-3xl px-4">
            {/* Breadcrumb */}
            <nav className="text-sm text-blue-200 mb-6 flex items-center gap-2">
              <Link href="/" className="hover:text-white transition-colors">Início</Link>
              <span>›</span>
              <Link href="/masterclass" className="hover:text-white transition-colors">Masterclasses</Link>
              <span>›</span>
              <span className="text-white line-clamp-1">{mc.title}</span>
            </nav>

            {/* Level + Duration badges */}
            <div className="flex items-center gap-3 mb-4">
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${LEVEL_COLOR[mc.level]}`}>
                {LEVEL_LABEL[mc.level]}
              </span>
              <span className="text-xs text-blue-200">{mc.durationMinutes} minutos</span>
              <span className="text-xs text-blue-200">Gratuito</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold leading-tight">{mc.title}</h1>
            <p className="mt-4 text-lg text-blue-100 leading-relaxed max-w-2xl">{mc.description}</p>
          </div>
        </section>

        <div className="mx-auto max-w-3xl px-4 py-12 space-y-10">
          {/* Topic outline */}
          <section>
            <h2 className="text-xl font-bold text-ink-primary mb-5">O que você vai aprender</h2>
            <ol className="space-y-3">
              {mc.topics.map((topic, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-blue/10 text-brand-blue font-bold text-sm flex items-center justify-center">
                    {i + 1}
                  </span>
                  <span className="text-ink-secondary leading-relaxed pt-0.5">{topic}</span>
                </li>
              ))}
            </ol>
          </section>

          {/* Instructor */}
          {author && (
            <section className="rounded-2xl border border-[var(--border)] bg-surface-1 p-6">
              <h2 className="text-sm font-semibold text-ink-muted uppercase tracking-wide mb-4">Instrutor</h2>
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-brand-blue/10 flex items-center justify-center text-xl font-bold text-brand-blue flex-shrink-0">
                  {author.name.split(' ').map((n: string) => n[0]).join('')}
                </div>
                <div>
                  <p className="font-bold text-ink-primary">{author.name}</p>
                  <p className="text-sm text-brand-blue">{author.role}</p>
                  <p className="mt-2 text-sm text-ink-secondary leading-relaxed">{author.shortBio}</p>
                  <div className="flex gap-3 mt-3">
                    {author.socialLinks.linkedin && (
                      <a
                        href={author.socialLinks.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-ink-muted hover:text-brand-blue transition-colors"
                      >
                        LinkedIn ↗
                      </a>
                    )}
                    <Link
                      href={`/blog/author/${author.slug}`}
                      className="text-xs text-ink-muted hover:text-brand-blue transition-colors"
                    >
                      Ver perfil completo ↗
                    </Link>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Email gate + video */}
          <MasterclassClient tema={mc.tema} title={mc.title} topics={mc.topics} />
        </div>

        {/* JSON-LD */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(graphLd) }}
        />
      </main>
      <Footer />
    </>
  );
}
