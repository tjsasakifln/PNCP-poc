interface FAQItem {
  question: string;
  answer: string;
}

interface PlanFAQProps {
  items: FAQItem[];
  openIndex: number | null;
  onToggle: (index: number) => void;
}

export function PlanFAQ({ items, openIndex, onToggle }: PlanFAQProps) {
  return (
    <div className="mt-16 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-[var(--ink)] mb-6 text-center">
        Perguntas Frequentes
      </h2>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div
            key={index}
            className="backdrop-blur-md bg-white/60 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-card overflow-hidden"
          >
            <button
              id={`faq-btn-${index}`}
              onClick={() => onToggle(index)}
              aria-expanded={openIndex === index}
              aria-controls={`faq-panel-${index}`}
              className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="font-medium text-[var(--ink)]">{item.question}</span>
              <svg
                className={`w-5 h-5 text-[var(--ink-muted)] transition-transform ${openIndex === index ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {openIndex === index && (
              <div
                id={`faq-panel-${index}`}
                role="region"
                aria-labelledby={`faq-btn-${index}`}
                className="px-6 pb-4"
              >
                <p className="text-sm text-[var(--ink-secondary)]">{item.answer}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
