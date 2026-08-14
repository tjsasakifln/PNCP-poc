/**
 * Declarative public journey — #2114 / #2117
 *
 * route_family → intent → context → CTA → destination → tracking
 *
 * Do not scatter CTA strings across pages. Import resolveJourney().
 */

export type RouteFamily =
  | "home"
  | "tender"
  | "contract"
  | "company"
  | "organ"
  | "municipality"
  | "observatory"
  | "tool"
  | "editorial"
  | "consultoria";

export type DataState = "ok" | "empty" | "stale" | "blocked" | "error" | "unknown";

export interface JourneyContext {
  family: RouteFamily;
  entityType?: string;
  entityPublicId?: string;
  setor?: string;
  uf?: string;
  dataState?: DataState;
  path?: string;
}

export interface JourneyCta {
  id: string;
  label: string;
  href: string;
  intent: string;
  helper: string;
  family: RouteFamily;
}

export interface JourneyDefinition {
  family: RouteFamily;
  intent: string;
  question: string;
  cta: Omit<JourneyCta, "href" | "family">;
  destination: string;
}

export const JOURNEYS: Record<RouteFamily, JourneyDefinition> = {
  home: {
    family: "home",
    intent: "entender o que o SmartLic publica e quando pedir ajuda",
    question: "O que estou vendo e para quem isso serve?",
    cta: {
      id: "cta.home.diagnostico",
      label: "Pedir um diagnóstico à CONFENGE",
      intent: "diagnostico",
      helper: "A CONFENGE interpreta o dado público e opera a decisão comercial.",
    },
    destination: "/consultoria-b2g",
  },
  tender: {
    family: "tender",
    intent: "decidir se vale disputar",
    question: "Esta licitação vale o esforço da minha empresa?",
    cta: {
      id: "cta.tender.go_nogo",
      label: "Pedir go/no-go desta licitação",
      intent: "go_nogo",
      helper: "A CONFENGE monta o dossiê de habilitação e a decisão de participar.",
    },
    destination: "/consultoria-b2g",
  },
  contract: {
    family: "contract",
    intent: "identificar risco ou oportunidade no contrato",
    question: "O que este contrato revela sobre o órgão e o fornecedor?",
    cta: {
      id: "cta.contract.risco",
      label: "Pedir leitura de risco e oportunidade",
      intent: "contract_risk",
      helper: "Histórico, aditivos e reincidência são interpretados pela CONFENGE.",
    },
    destination: "/consultoria-b2g",
  },
  company: {
    family: "company",
    intent: "entender posição e carteira pública",
    question: "Qual é a posição desta empresa no mercado público?",
    cta: {
      id: "cta.company.carteira",
      label: "Pedir leitura da carteira pública",
      intent: "company_position",
      helper: "A CONFENGE cruza carteira, órgãos e concorrência sem login.",
    },
    destination: "/consultoria-b2g",
  },
  organ: {
    family: "organ",
    intent: "entender mercado e histórico do comprador",
    question: "Como este órgão compra e com quem?",
    cta: {
      id: "cta.organ.mercado",
      label: "Pedir mapa de compras deste órgão",
      intent: "organ_market",
      helper: "Padrão de compra, ticket e fornecedores recorrentes.",
    },
    destination: "/consultoria-b2g",
  },
  municipality: {
    family: "municipality",
    intent: "entender oportunidades locais",
    question: "O que este município está comprando?",
    cta: {
      id: "cta.municipality.local",
      label: "Pedir recorte local de oportunidades",
      intent: "local_opportunities",
      helper: "A CONFENGE prioriza o que é disputável no município.",
    },
    destination: "/consultoria-b2g",
  },
  observatory: {
    family: "observatory",
    intent: "ler o recorte de mercado",
    question: "O que este recorte muda na minha decisão?",
    cta: {
      id: "cta.observatory.leitura",
      label: "Pedir leitura deste recorte",
      intent: "market_reading",
      helper: "O dado fica público. A interpretação consultiva é da CONFENGE.",
    },
    destination: "/consultoria-b2g",
  },
  tool: {
    family: "tool",
    intent: "usar a ferramenta e, se fizer sentido, pedir ajuda",
    question: "Este cálculo ou comparação basta, ou preciso de diagnóstico?",
    cta: {
      id: "cta.tool.diagnostico",
      label: "Levar este resultado à CONFENGE",
      intent: "tool_followup",
      helper: "A ferramenta é pública. O diagnóstico é serviço.",
    },
    destination: "/consultoria-b2g",
  },
  editorial: {
    family: "editorial",
    intent: "sair do artigo para um fato ou para a CONFENGE",
    question: "Qual fato público eu consulto a partir daqui?",
    cta: {
      id: "cta.editorial.fato",
      label: "Falar com a CONFENGE sobre este tema",
      intent: "editorial_followup",
      helper: "Conteúdo explica. Dado verifica. Consultoria decide.",
    },
    destination: "/consultoria-b2g",
  },
  consultoria: {
    family: "consultoria",
    intent: "enviar intenção comercial",
    question: "Como a CONFENGE pode atuar neste contexto?",
    cta: {
      id: "cta.consultoria.submit",
      label: "Enviar pedido de diagnóstico",
      intent: "lead_submit",
      helper: "Sem conta. Sem trial. Sem plano.",
    },
    destination: "/consultoria-b2g#diagnostico",
  },
};

function appendQuery(base: string, params: Record<string, string | undefined>): string {
  const url = new URL(base, "https://smartlic.tech");
  for (const [key, value] of Object.entries(params)) {
    if (value) url.searchParams.set(key, value);
  }
  return `${url.pathname}${url.search}${url.hash}`;
}

export function resolveJourney(ctx: JourneyContext): JourneyCta {
  const def = JOURNEYS[ctx.family];
  const href = appendQuery(def.destination, {
    cta: def.cta.id,
    family: ctx.family,
    entity: ctx.entityPublicId,
    setor: ctx.setor,
    uf: ctx.uf,
    state: ctx.dataState && ctx.dataState !== "ok" ? ctx.dataState : undefined,
  });
  return {
    ...def.cta,
    family: ctx.family,
    href,
  };
}

export function familyFromPath(path: string): RouteFamily {
  if (path.startsWith("/licitacoes")) return "tender";
  if (path.startsWith("/contratos")) return "contract";
  if (path.startsWith("/cnpj") || path.startsWith("/fornecedores") || path.startsWith("/inteligencia")) {
    return "company";
  }
  if (path.startsWith("/orgaos")) return "organ";
  if (path.startsWith("/municipios") || path.startsWith("/indice-municipal")) {
    return "municipality";
  }
  if (path.startsWith("/observatorio")) return "observatory";
  if (
    path.startsWith("/calculadora") ||
    path.startsWith("/comparador") ||
    path.startsWith("/compliance")
  ) {
    return "tool";
  }
  if (path.startsWith("/consultoria")) return "consultoria";
  if (path.startsWith("/blog") || path.startsWith("/guia") || path.startsWith("/perguntas")) {
    return "editorial";
  }
  return "home";
}

export const SAAS_CTA_DENYLIST = [
  "/signup",
  "/planos",
  "/pricing",
  "/fundadores",
  "/founding",
  "teste grátis",
  "teste gratis",
  "assine",
  "upgrade",
  "começar trial",
  "comecar trial",
] as const;
