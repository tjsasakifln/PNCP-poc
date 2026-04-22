/**
 * JSON-LD Product schema for /planos page (STORY-SEO-004).
 *
 * Emits 2 Products (SmartLic Pro + Consultoria), each with 3 Offers
 * (monthly, semiannual, annual), matching the billing periods shown in the UI.
 *
 * Rich Results eligibility requires: name, offers, brand, description,
 * priceValidUntil, availability. Aligned with schema.org/Product spec.
 */
import {
  CONSULTORIA_PRICING,
  PRO_PRICING,
  PricingTable,
  getPriceValidUntil,
} from "@/lib/plan-pricing";

const SITE_URL = "https://smartlic.tech";

type ProductSpec = {
  name: string;
  description: string;
  pricing: PricingTable;
  urlQueryKey: string;
};

const PRODUCTS: ProductSpec[] = [
  {
    name: "SmartLic Pro",
    description:
      "Inteligência de decisão em licitações públicas para empresas B2G: avaliação de viabilidade, filtragem setorial, pipeline e exportação Excel.",
    pricing: PRO_PRICING,
    urlQueryKey: "pro",
  },
  {
    name: "SmartLic Consultoria",
    description:
      "Plano Consultoria SmartLic: até 5 usuários, 5.000 análises/mês, dashboard consolidado e suporte dedicado para consultorias e assessorias de licitação.",
    pricing: CONSULTORIA_PRICING,
    urlQueryKey: "consultoria",
  },
];

function buildProductSchema(product: ProductSpec, priceValidUntil: string): Record<string, unknown> {
  const offers = Object.entries(product.pricing).map(([period, entry]) => ({
    "@type": "Offer",
    price: entry.monthly.toFixed(2),
    priceCurrency: "BRL",
    availability: "https://schema.org/InStock",
    priceValidUntil,
    category: period,
    url: `${SITE_URL}/planos?plan=${product.urlQueryKey}&period=${period}`,
  }));

  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.description,
    brand: {
      "@type": "Brand",
      name: "SmartLic",
    },
    offers,
  };
}

export function ProductSchema() {
  const priceValidUntil = getPriceValidUntil();
  const schemas = PRODUCTS.map((p) => buildProductSchema(p, priceValidUntil));

  return (
    <>
      {schemas.map((schema, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      ))}
    </>
  );
}
