/**
 * SmartLic brand system — #2114 / ADR-STRAT-001
 *
 * Single source for descriptor, CONFENGE relationship, voice and
 * institutional copy. Pages must import from here instead of inventing
 * SaaS slogans.
 */

export const BRAND = {
  name: "SmartLic",
  legalName: "CONFENGE Avaliações e Inteligência Artificial LTDA",
  descriptor: "Inteligência pública B2G da CONFENGE",
  tagline: "Fatos públicos verificáveis sobre o mercado de licitações.",
  relationship:
    "O SmartLic é o braço público de inteligência e inbound da CONFENGE. Não é um SaaS de assinatura.",
  planes: {
    extraCli: "truth / data plane",
    smartlic: "discovery / intelligence / inbound",
    confenge: "service / conversion / delivery",
  },
  urls: {
    site: "https://smartlic.tech",
    confenge: "https://confenge.com.br",
    consultoria: "/consultoria-b2g",
    sobre: "/sobre",
  },
  contact: {
    public: "contato@smartlic.tech",
    confenge: "tiago.sasaki@confenge.com.br",
  },
  voice: {
    do: [
      "dado verificável",
      "fonte e data à vista",
      "limitação explícita",
      "próxima ação contextual",
    ],
    dont: [
      "teste grátis",
      "assine agora",
      "upgrade",
      "plano mensal",
      "IA mágica",
      "promessa vazia",
    ],
  },
} as const;

export const DEFAULT_TITLE =
  "SmartLic — Inteligência pública de licitações da CONFENGE";

export const DEFAULT_DESCRIPTION =
  "Consulte empresas, contratos, licitações, órgãos e municípios com dados públicos verificáveis. O SmartLic é o braço de inbound da CONFENGE.";

export const ORGANIZATION_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: BRAND.legalName,
  alternateName: BRAND.name,
  url: BRAND.urls.site,
  description: BRAND.relationship,
  parentOrganization: {
    "@type": "Organization",
    name: BRAND.legalName,
    url: BRAND.urls.confenge,
  },
  contactPoint: {
    "@type": "ContactPoint",
    email: BRAND.contact.public,
    contactType: "customer service",
    availableLanguage: "Portuguese",
  },
  sameAs: [BRAND.urls.confenge],
} as const;

export const WEBSITE_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: BRAND.name,
  url: BRAND.urls.site,
  description: DEFAULT_DESCRIPTION,
  publisher: {
    "@type": "Organization",
    name: BRAND.legalName,
  },
} as const;
