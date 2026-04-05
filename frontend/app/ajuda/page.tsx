import LandingNavbar from "@/app/components/landing/LandingNavbar";
import AjudaFaqClient from "./components/AjudaFaqClient";
import SchemaMarkup from "@/components/blog/SchemaMarkup";
import { getAllFAQs } from "./faqData";
import { buildCanonical } from "@/lib/seo";

/**
 * STORY-226 AC25-AC28: FAQ / Central de Ajuda
 *
 * Server Component shell: renders the static outer wrapper, navbar, and
 * FAQPage JSON-LD (via SchemaMarkup). All interactive FAQ content (hero with
 * search, accordion, category filter) is handled by AjudaFaqClient.
 *
 * SEO: FAQPage structured data exposes every question/answer to Google's
 * rich-results crawler. Schema is emitted at the top of the page body so
 * crawlers encounter it before the interactive shell.
 */
export default function AjudaPage() {
  const faqs = getAllFAQs();
  const url = buildCanonical('/ajuda');

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <SchemaMarkup
        pageType="faq"
        title="Central de Ajuda — SmartLic"
        description="Respostas para as dúvidas mais comuns sobre o SmartLic: busca de licitações, planos, pagamentos, fontes de dados e conta."
        url={url}
        faqs={faqs}
        breadcrumbs={[
          { name: 'Início', url: buildCanonical('/') },
          { name: 'Central de Ajuda', url },
        ]}
      />
      <LandingNavbar />
      <AjudaFaqClient />
    </div>
  );
}
