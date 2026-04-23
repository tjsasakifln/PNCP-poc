"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/app/components/AuthProvider";
import { FAQ_DATA as FAQ_DATA_SOURCE, type FAQItem } from "../faqData";

// ---- FAQ Data ----
// Question/answer content lives in ../faqData.ts so the server component
// can import it for FAQPage JSON-LD schema emission. Icons are defined
// here because they contain client-side JSX/SVG.

interface FAQCategory {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: FAQItem[];
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  "como-buscar": (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  "planos": (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  "pagamentos": (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  ),
  "fontes-dados": (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  ),
  "confianca": (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  "minha-conta": (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
};

const FAQ_DATA: FAQCategory[] = FAQ_DATA_SOURCE.map((category) => ({
  ...category,
  icon: CATEGORY_ICONS[category.id] ?? null,
}));


// ---- Accordion Item Component ----

function AccordionItem({
  item,
  isOpen,
  onToggle,
}: {
  item: FAQItem;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-b border-[var(--border)] last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-4 px-1 text-left
                   hover:text-[var(--brand-blue)] transition-colors
                   focus-visible:outline-none focus-visible:ring-2
                   focus-visible:ring-[var(--brand-blue)] focus-visible:ring-offset-2
                   rounded"
        aria-expanded={isOpen}
      >
        <span className="text-sm font-medium text-[var(--ink)] pr-4">
          {item.question}
        </span>
        <svg
          className={`w-5 h-5 flex-shrink-0 text-[var(--ink-muted)] transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div
        className={`overflow-hidden transition-all duration-200 ${
          isOpen ? "max-h-96 pb-4" : "max-h-0"
        }`}
      >
        <p className="text-sm text-[var(--ink-secondary)] leading-relaxed px-1">
          {item.answer}
        </p>
      </div>
    </div>
  );
}

// ---- Interactive FAQ Widget (Client Component) ----
// Renders the full page content: hero section (title + search), FAQ categories, contact section.

export default function AjudaFaqClient() {
  const { user, loading } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Filter FAQ items by search query
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) {
      return activeCategory
        ? FAQ_DATA.filter((cat) => cat.id === activeCategory)
        : FAQ_DATA;
    }

    const query = searchQuery.toLowerCase().trim();
    const result: FAQCategory[] = [];

    for (const category of FAQ_DATA) {
      if (activeCategory && category.id !== activeCategory) continue;

      const matchingItems = category.items.filter(
        (item) =>
          item.question.toLowerCase().includes(query) ||
          item.answer.toLowerCase().includes(query)
      );

      if (matchingItems.length > 0) {
        result.push({ ...category, items: matchingItems });
      }
    }

    return result;
  }, [searchQuery, activeCategory]);

  const totalResults = filteredData.reduce((sum, cat) => sum + cat.items.length, 0);

  const toggleItem = (key: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  return (
    <>
      {/* Hero Section with Search Input */}
      <div className="bg-[var(--surface-0)] border-b border-[var(--border)]">
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          <h1 className="text-3xl font-display font-bold text-[var(--ink)] mb-3">
            Central de Ajuda
          </h1>
          <p className="text-[var(--ink-secondary)] mb-8 max-w-lg mx-auto">
            Encontre respostas para as dúvidas mais comuns sobre o SmartLic.
          </p>

          {/* Search Input */}
          <div className="relative max-w-xl mx-auto">
            <svg
              className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--ink-muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="search"
              placeholder="Buscar nas perguntas frequentes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Buscar nas perguntas frequentes"
              className="w-full pl-12 pr-4 py-3 rounded-button border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         placeholder:text-[var(--ink-muted)]
                         focus:border-[var(--brand-blue)] focus:outline-none
                         focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--ink-muted)]
                           hover:text-[var(--ink)] transition-colors"
                aria-label="Limpar busca"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Category Pills */}
        <div className="flex flex-wrap gap-2 mb-8">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
              ${
                activeCategory === null
                  ? "bg-[var(--brand-navy)] text-white"
                  : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2)] border border-[var(--border)]"
              }`}
          >
            Todas
          </button>
          {FAQ_DATA.map((category) => (
            <button
              key={category.id}
              onClick={() =>
                setActiveCategory(activeCategory === category.id ? null : category.id)
              }
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                flex items-center gap-1.5
                ${
                  activeCategory === category.id
                    ? "bg-[var(--brand-navy)] text-white"
                    : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2)] border border-[var(--border)]"
                }`}
            >
              {category.icon}
              {category.title}
            </button>
          ))}
        </div>

        {/* Search Results Count */}
        {searchQuery.trim() && (
          <p className="text-sm text-[var(--ink-muted)] mb-4">
            {totalResults === 0
              ? "Nenhum resultado encontrado"
              : `${totalResults} resultado${totalResults !== 1 ? "s" : ""} encontrado${totalResults !== 1 ? "s" : ""}`}
          </p>
        )}

        {/* FAQ Categories */}
        {filteredData.length === 0 ? (
          <div className="text-center py-16">
            <svg
              className="w-16 h-16 mx-auto text-[var(--ink-muted)] mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-[var(--ink)] mb-2">
              {searchQuery.trim()
                ? `Nenhuma pergunta encontrada para "${searchQuery.trim()}"`
                : "Nenhuma pergunta encontrada"}
            </h3>
            <p className="text-[var(--ink-secondary)] mb-4">
              Tente buscar com termos diferentes ou <a href="#contato" className="underline hover:text-[var(--brand-blue)]">entre em contato conosco</a>.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {filteredData.map((category) => (
              <div
                key={category.id}
                className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card overflow-hidden"
              >
                {/* Category Header */}
                <div className="flex items-center gap-3 px-6 py-4 bg-[var(--surface-1)] border-b border-[var(--border)]">
                  <span className="text-[var(--brand-blue)]">{category.icon}</span>
                  <h2 className="text-lg font-semibold text-[var(--ink)]">
                    {category.title}
                  </h2>
                  <span className="text-xs text-[var(--ink-muted)] ml-auto">
                    {category.items.length} pergunta{category.items.length !== 1 ? "s" : ""}
                  </span>
                </div>

                {/* Accordion Items */}
                <div className="px-6">
                  {category.items.map((item, index) => {
                    const key = `${category.id}-${index}`;
                    return (
                      <AccordionItem
                        key={key}
                        item={item}
                        isOpen={openItems.has(key)}
                        onToggle={() => toggleItem(key)}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Contact Section */}
        <div id="contato" className="mt-12 text-center bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 scroll-mt-24">
          <h3 className="text-xl font-semibold text-[var(--ink)] mb-2">
            Ainda tem dúvidas?
          </h3>
          <p className="text-[var(--ink-secondary)] mb-6">
            Nossa equipe está pronta para ajudar.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {loading ? (
              <div className="h-12 w-48 bg-[var(--surface-1)] rounded-lg animate-pulse" />
            ) : user ? (
              <Link
                href="/mensagens"
                className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                           rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Enviar Mensagem
              </Link>
            ) : (
              <Link
                href="/signup?source=ajuda-contato"
                className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                           rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Criar Conta para Contato
              </Link>
            )}
          </div>
        </div>

        {/* Back Link */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-[var(--ink-muted)] hover:underline">
            Voltar para a página inicial
          </Link>
        </div>
      </div>
    </>
  );
}
