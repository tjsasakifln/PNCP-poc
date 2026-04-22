import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import PillarPageLayout from '../_components/PillarPageLayout';
import { PILLARS, getPillarBySlug, getAllPillarSlugs } from '@/lib/pillars';
import LicitacoesContent, { sections as licitacoesSections } from '../_content/licitacoes';
import Lei14133Content, { sections as lei14133Sections } from '../_content/lei-14133';
import PncpContent, { sections as pncpSections } from '../_content/pncp';

const SITE = 'https://smartlic.tech';

type PillarSlug = (typeof PILLARS)[number]['slug'];

export async function generateStaticParams() {
  return getAllPillarSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const pillar = getPillarBySlug(slug);
  if (!pillar) return {};

  const canonical = `${SITE}/guia/${pillar.slug}`;
  return {
    title: pillar.title,
    description: pillar.description,
    keywords: pillar.keywords,
    alternates: { canonical },
    robots: { index: true, follow: true },
    openGraph: {
      type: 'article',
      title: pillar.shortTitle,
      description: pillar.description,
      url: canonical,
      siteName: 'SmartLic',
      locale: 'pt_BR',
      publishedTime: pillar.publishDate,
      modifiedTime: pillar.lastModified,
    },
    twitter: {
      card: 'summary_large_image',
      title: pillar.shortTitle,
      description: pillar.description,
    },
  };
}

type ContentRegistry = Record<
  PillarSlug,
  { Component: () => React.ReactElement; sections: { id: string; title: string }[] }
>;

const CONTENT: ContentRegistry = {
  licitacoes: { Component: LicitacoesContent, sections: licitacoesSections },
  'lei-14133': { Component: Lei14133Content, sections: lei14133Sections },
  pncp: { Component: PncpContent, sections: pncpSections },
};

export default async function PillarPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const pillar = getPillarBySlug(slug);
  if (!pillar) notFound();

  const entry = CONTENT[pillar.slug as PillarSlug];
  if (!entry) notFound();

  const Content = entry.Component;
  return (
    <PillarPageLayout pillar={pillar} sections={entry.sections}>
      <Content />
    </PillarPageLayout>
  );
}
