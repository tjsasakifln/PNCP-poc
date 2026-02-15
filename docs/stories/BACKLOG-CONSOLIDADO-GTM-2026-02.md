# Backlog Consolidado — GTM + Technical Debt
## SmartLic — Fevereiro 2026

> **Contexto:** Este backlog unifica as 19 stories de technical debt (TD-001 a TD-019) originadas pela auditoria brownfield com as novas diretrizes estratégicas de GTM recebidas em 2026-02-15. O objetivo é um plano de execução único, sem duplicidade, com priorização clara.

---

## Sumário Executivo

| Categoria | Stories | Esforço Total |
|-----------|---------|---------------|
| **GTM (Novas)** | 10 stories (GTM-001 a GTM-010) | ~98h |
| **TD (Existentes)** | 16 stories ativas + 1 umbrella | ~232h |
| **Absorvidas/Suprimidas** | 3 stories (STORY-173, STORY-244, TD-002 parcial) | — |
| **Completadas** | STORY-257A, STORY-257B | ✅ |
| **Total Backlog Ativo** | 26 stories | ~330h |

---

## PARTE 1: STORIES GTM — REPOSICIONAMENTO ESTRATÉGICO

### Princípios Guia (aplicáveis a TODAS as stories GTM)

1. **Não vendemos busca. Vendemos inteligência de decisão.**
2. **Não vendemos velocidade. Vendemos vantagem competitiva.**
3. **IA não gera resumos. IA avalia oportunidades e orienta decisões.**
4. **PNCP nunca é mencionado. Consultamos "dezenas de fontes oficiais em tempo real".**
5. **Não existem "planos de assinatura". Existem "níveis de compromisso em se destacar no mercado".**
6. **O custo de não usar o SmartLic é tangível: perder contratos por falta de visibilidade.**
7. **Design: glass morphism consistente, minimalista, elegante, com acentos de pedras preciosas translúcidas.**

---

### GTM-001: Reescrita Completa da Copy — Landing Page
**Prioridade:** P0 (GTM-blocker) | **Estimativa:** 12h | **Sprint:** 1
**Absorve:** STORY-173 (Brand Positioning), STORY-244 (Strategic Copy)

#### Problema
A landing page comunica "ferramenta que economiza tempo" — commodity. Headlines como "Encontre em 3 Minutos", "160x Mais Rápido", "95% de Precisão" colocam SmartLic na mesma prateleira de qualquer buscador automatizado. O mercado de licitação compra vantagem competitiva, não velocidade.

#### Escopo — Arquivos Afetados

| Componente | Arquivo | Status Atual → Desejado |
|-----------|---------|------------------------|
| **HeroSection** | `frontend/app/components/landing/HeroSection.tsx` | "Encontre em 3 Minutos" → Inteligência de decisão |
| **BeforeAfter** | `frontend/app/components/landing/BeforeAfter.tsx` | Comparação tempo → Comparação resultado financeiro |
| **DifferentialsGrid** | `frontend/app/components/landing/DifferentialsGrid.tsx` | Features técnicas → Diferenciais de valor |
| **HowItWorks** | `frontend/app/components/landing/HowItWorks.tsx` | Mecânico → Orientado ao resultado |
| **OpportunityCost** | `frontend/app/components/landing/OpportunityCost.tsx` | Custo de horas → Custo de oportunidades perdidas |
| **FinalCTA** | `frontend/app/components/landing/FinalCTA.tsx` | "Economize tempo" → "Comece a ganhar" |
| **StatsSection** | `frontend/app/components/landing/StatsSection.tsx` | Métricas genéricas → Impacto em resultado |
| **DataSourcesSection** | `frontend/app/components/landing/DataSourcesSection.tsx` | Cita PNCP → "fontes oficiais" genérico |
| **valueProps.ts** | `frontend/lib/copy/valueProps.ts` | Reescrita completa (~437 linhas) |
| **comparisons.ts** | `frontend/lib/copy/comparisons.ts` | Reescrita completa (~217 linhas) |

#### Acceptance Criteria

**Copy Estratégica:**
- [ ] **AC1:** Hero headline comunica DECISÃO, não velocidade. Ex: "Saiba onde investir para ganhar mais licitações"
- [ ] **AC2:** Sub-headline posiciona IA como analista de oportunidades (não gerador de resumos)
- [ ] **AC3:** CTA principal usa verbo de resultado: "Descobrir minhas oportunidades"
- [ ] **AC4:** Seção "custo de não usar" é tangível: "Seu concorrente já pode estar se posicionando enquanto você ainda está procurando"
- [ ] **AC5:** BeforeAfter compara cenários de RESULTADO (perder vs ganhar licitações), não de tempo
- [ ] **AC6:** DifferentialsGrid foca em: (1) Priorização inteligente, (2) Análise automatizada, (3) Redução de incerteza, (4) Cobertura nacional
- [ ] **AC7:** HowItWorks: "Diga o que vende → Receba curadoria → Decida com confiança"
- [ ] **AC8:** OpportunityCost quantifica dinheiro perdido, não horas perdidas

**Eliminações Obrigatórias:**
- [ ] **AC9:** ZERO menções a "160x", "95%", "3 minutos", "8 horas", "economize tempo", "busca rápida"
- [ ] **AC10:** ZERO menções a "PNCP", "Portal Nacional de Contratações Públicas", ou qualquer nome de fonte
- [ ] **AC11:** ZERO testemunhos fictícios (João Silva, Maria Santos, Carlos Oliveira, Ana Costa)

**Novas Inclusões:**
- [ ] **AC12:** Banned phrases atualizadas em `valueProps.ts` incluindo todos termos de eficiência
- [ ] **AC13:** Preferred phrases incluem: "inteligência de decisão", "oportunidades priorizadas", "vantagem competitiva", "orientação estratégica"

**Qualidade:**
- [ ] **AC14:** Mobile responsive em viewport 375px
- [ ] **AC15:** Dark mode legível
- [ ] **AC16:** TypeScript clean

---

### GTM-002: Modelo de Assinatura Único — R$ 1.999/mês
**Prioridade:** P0 (GTM-blocker) | **Estimativa:** 16h | **Sprint:** 1
**Absorve:** TD-002 (Pricing Divergence), TD-018 (Plan Consolidation, parcial)

#### Problema
O modelo atual de 3 planos (Consultor Ágil R$297, Máquina R$597, Sala de Guerra R$1.497) gera comparação interna, dilui valor percebido e comunica "acesso" em vez de "resultado". Múltiplos níveis convidam o usuário a escolher o mais barato.

#### Nova Estrutura

| "Nível de Compromisso" | Preço | Desconto | Equivalência |
|------------------------|-------|----------|--------------|
| **Mensal** | R$ 1.999/mês | — | Avaliação constante |
| **Semestral** | R$ 1.799/mês | 10% | Consistência competitiva |
| **Anual** | R$ 1.599/mês | 20% | Domínio do mercado |

> Argumento: "Quem avalia constantemente oportunidades é quem vence mais licitações."

#### Escopo — Backend

| Arquivo | Mudança |
|---------|---------|
| `backend/quota.py` (L62-135) | Substituir 4 planos por 1 (`smartlic_pro`) + free_trial |
| `backend/quota.py` PLAN_CAPABILITIES | Novo plano com capabilities máximas (Excel, pipeline, 1000 buscas/mês, 5 anos histórico) |
| `backend/quota.py` PLAN_NAMES | `"smartlic_pro": "SmartLic Pro"` |
| `backend/quota.py` PLAN_PRICES | `"smartlic_pro": "R$ 1.999/mês"` |
| `backend/quota.py` UPGRADE_SUGGESTIONS | Simplificar: free_trial → smartlic_pro |
| `backend/routes/billing.py` | Ajustar checkout para 3 billing periods (monthly, semiannual, annual) |
| `backend/services/billing.py` | Ajustar pro-rata para novo modelo |
| `backend/routes/plans.py` | Endpoint retorna plano único |
| `backend/webhooks/stripe.py` | Manter compatibilidade com subscribers existentes |
| **Supabase** | Migration 028: novo plano na tabela `plans`, atualizar `plan_features` |
| **Stripe** | Criar novo Product + 3 Prices (monthly, semiannual, annual) |

#### Escopo — Frontend

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/planos/page.tsx` (~700 linhas) | Reescrever completamente: plano único, 3 billing periods |
| `frontend/app/pricing/page.tsx` | Atualizar com nova estrutura |
| `frontend/lib/copy/valueProps.ts` (ROI section) | Recalcular com novo preço |
| `frontend/lib/copy/roi.ts` | Atualizar DEFAULT_VALUES |
| `frontend/components/subscriptions/PlanToggle.tsx` | Adaptar para 3 períodos |
| `frontend/app/components/UpgradeModal.tsx` | Simplificar para plano único |
| `frontend/app/components/PlanBadge.tsx` | Simplificar |

#### Acceptance Criteria

- [ ] **AC1:** Backend aceita `plan_id=smartlic_pro` com `billing_period` em `monthly|semiannual|annual`
- [ ] **AC2:** Stripe tem Product "SmartLic Pro" com 3 Prices configurados
- [ ] **AC3:** Frontend /planos exibe plano único com 3 "níveis de compromisso" (NÃO "planos")
- [ ] **AC4:** Copy nunca usa "plano", "assinatura" ou "tier". Usa "nível de compromisso"
- [ ] **AC5:** Preço mensal destacado: R$ 1.999. Semestral: R$ 1.799/mês (-10%). Anual: R$ 1.599/mês (-20%)
- [ ] **AC6:** ROI calculator atualizado: "Uma única licitação ganha pode pagar um ano inteiro"
- [ ] **AC7:** Subscribers existentes (consultor_agil, maquina, sala_guerra) continuam funcionando (backward compatible)
- [ ] **AC8:** Migration 028 cria plano e billing periods no Supabase
- [ ] **AC9:** Calculadora de ROI removida ou simplificada — foco em "quanto você ganha", não "quanto economiza"
- [ ] **AC10:** Zero menção a "busca" na page de planos — é "análise", "inteligência", "avaliação"

---

### GTM-003: Redesign do Trial — 7 Dias, Produto Integral
**Prioridade:** P0 (GTM-blocker) | **Estimativa:** 8h | **Sprint:** 1

#### Problema
Trial atual: 3 buscas, funcionalidades restritas (sem Excel, sem pipeline, IA básica, 7 dias histórico). Isso entrega uma versão "capada" que não demonstra o valor real. Usuário não experimenta o produto premium.

#### Nova Estrutura do Trial

| Aspecto | Atual | Novo |
|---------|-------|------|
| Duração | 7 dias (via `expires_at`) | 7 dias (manter) |
| Limite | 3 buscas/mês | **3 análises completas** |
| Excel | ❌ Desabilitado | ✅ Habilitado |
| Pipeline | ❌ Desabilitado | ✅ Habilitado |
| IA | Básica (200 tokens) | **Completa (10.000 tokens)** |
| Histórico | 7 dias | **365 dias** |
| Processamento | Low priority | **Normal priority** |

#### Escopo — Backend

| Arquivo | Mudança |
|---------|---------|
| `backend/quota.py` PLAN_CAPABILITIES `free_trial` | `allow_excel: True`, `allow_pipeline: True`, `max_summary_tokens: 10000`, `max_history_days: 365`, `priority: "normal"` |
| `backend/quota.py` | Manter `max_requests_per_month: 3` |

#### Escopo — Frontend

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/signup/page.tsx` | Subheadline: "Experimente o SmartLic completo por 7 dias" (não "3 buscas gratuitas") |
| `frontend/lib/copy/valueProps.ts` (trial CTAs) | "Experimente sem compromisso" (não "teste grátis") |
| `frontend/app/features/page.tsx` | "7 dias do produto completo. Sem versão limitada." |

#### Acceptance Criteria

- [ ] **AC1:** Usuário trial tem acesso a Excel, Pipeline, IA completa
- [ ] **AC2:** Limite de 3 análises mantido (quota enforcement)
- [ ] **AC3:** Copy de signup diz "produto completo" não "buscas gratuitas"
- [ ] **AC4:** Ao esgotar 3 análises, mensagem: "Suas 3 análises do trial foram usadas. Uma única licitação ganha pode pagar o sistema. Continue por R$ 1.999/mês"
- [ ] **AC5:** Ao expirar 7 dias, mensagem similar focada em valor gerado
- [ ] **AC6:** Nenhuma feature é "gated" durante o trial — produto 100% funcional

---

### GTM-004: Onboarding Estratégico + Primeiro Resultado Imediato
**Prioridade:** P0 (GTM-blocker) | **Estimativa:** 10h | **Sprint:** 1

#### Problema
O onboarding atual (STORY-247) coleta dados básicos (porte, UFs, experiência) mas não conecta imediatamente ao valor. Após completar, redireciona para `/buscar` onde o usuário precisa explorar manualmente.

#### Novo Fluxo

```
Signup → Onboarding Estratégico (3 steps) → Primeira Análise Automática → Resultados Priorizados
```

#### Escopo — Backend

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/user.py` (profile/context) | Aceitar campos adicionais: `cnae`, `objetivo_principal`, `ticket_medio_desejado` |
| `backend/schemas.py` PerfilContexto | Novos campos opcionais |
| **Novo endpoint** | `POST /api/first-analysis` — Executa busca automática baseada no perfil + retorna oportunidades priorizadas |

#### Escopo — Frontend

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/onboarding/page.tsx` | Step 1: CNAE/segmento + objetivo. Step 2: UFs + faixa valor. Step 3: Confirmação + "Ver oportunidades" |
| | Após save: redirecionar para `/buscar?auto=true` que dispara busca automática |
| | Copy do wizard: "Configure seu perfil para que o SmartLic trabalhe para você" |
| | Copy final: "Vamos encontrar suas primeiras oportunidades agora" |

#### Acceptance Criteria

- [ ] **AC1:** Wizard coleta CNAE/segmento como campo principal (não apenas setor)
- [ ] **AC2:** Wizard coleta objetivo ("Quero encontrar licitações acima de R$X no meu segmento")
- [ ] **AC3:** Ao completar wizard, sistema executa primeira busca automaticamente (sem clique adicional)
- [ ] **AC4:** Resultados retornam em <15s com oportunidades relevantes ao perfil
- [ ] **AC5:** Se não houver resultados para o perfil exato, sistema sugere filtros mais amplos
- [ ] **AC6:** Copy do wizard nunca menciona "busca" — usa "análise", "oportunidades", "perfil estratégico"
- [ ] **AC7:** Dados do onboarding salvos em `profiles.context_data` (já funcional via STORY-247)

---

### GTM-005: Carrossel de Exemplos Reais — Substituir Testemunhos
**Prioridade:** P1 | **Estimativa:** 8h | **Sprint:** 2

#### Problema
O site tem testemunhos fictícios (Carlos Mendes/Uniformes Excellence, Ana Paula Silva/Facilities Pro, Roberto Santos/Tech Solutions BR) que não transmitem credibilidade. A diretriz é substituir por exemplos reais de análise: "essa licitação → o sistema analisou assim → a decisão foi essa".

#### Escopo

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/components/landing/TestimonialsCarousel.tsx` | Reescrever como `AnalysisExamplesCarousel` |
| `frontend/lib/copy/valueProps.ts` (testimonials section, L374-406) | Substituir por exemplos reais de análise |

#### Acceptance Criteria

- [ ] **AC1:** Carrossel mostra 3-5 exemplos reais de licitações analisadas pelo sistema
- [ ] **AC2:** Cada card mostra: título da licitação (anonimizado se necessário), valor estimado, análise do SmartLic, decisão sugerida
- [ ] **AC3:** Formato: "Licitação de R$ 450.000 para uniformes em SP → SmartLic identificou: prazo adequado, requisitos compatíveis, baixa concorrência → Recomendação: participar com prioridade alta"
- [ ] **AC4:** Zero testemunhos fictícios de pessoas
- [ ] **AC5:** Auto-scroll com pause on hover (manter UX do carrossel atual)
- [ ] **AC6:** Dados podem ser estáticos inicialmente (curados manualmente), com rota para API futura

---

### GTM-006: Unificação do Design System — Glass Morphism Consistente
**Prioridade:** P1 | **Estimativa:** 16h | **Sprint:** 2

#### Problema (Achados da Auditoria)

| Inconsistência | Landing | Área Logada |
|---------------|---------|-------------|
| Glass effects | `backdrop-blur-md` (GlassCard) | Sem glass (LicitacaoCard sólido) |
| Header | `text-2xl`, transparente→glass on scroll | `text-xl`, sempre glass |
| Cards | GlassCard com hover-lift | Solid cards sem efeito |
| Seção backgrounds | Variados (surface-0, surface-1, brand-blue-subtle) | Uniformes |
| Animações | Framer Motion pesado | Mínimas |

#### Diretriz: "Minimalista, moderno, elegante, estilo glass em todos os elementos. Acentos de pedras preciosas translúcidas."

#### Escopo

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/globals.css` | Definir palette de "pedras preciosas" translúcidas (safira, esmeralda, ametista, rubi) como CSS vars |
| `frontend/tailwind.config.ts` | Adicionar tokens para gem-sapphire, gem-emerald, gem-amethyst, gem-ruby (todos translúcidos) |
| `frontend/app/components/ui/GlassCard.tsx` | Adicionar variant `result` para cards de resultado de busca |
| `frontend/app/components/LicitacaoCard.tsx` | Migrar para GlassCard variant="result" |
| `frontend/app/buscar/page.tsx` header | Alinhar estilo com landing (glass consistent) |
| `frontend/app/components/AppHeader.tsx` | Unificar com LandingNavbar (mesma base, adaptar conteúdo) |
| `frontend/app/layout.tsx` | Adicionar viewport meta tag explícita |
| `frontend/app/components/InstitutionalSidebar.tsx` | Adicionar glass effects (atualmente sem) |
| `frontend/app/planos/page.tsx` | Aplicar glass cards aos "níveis de compromisso" |
| `frontend/app/pipeline/page.tsx` | Aplicar glass cards consistentes |

#### Acceptance Criteria

- [ ] **AC1:** Glass effect (`backdrop-blur`) aplicado consistentemente em: header, cards de resultado, cards de plano, modals, sidebar
- [ ] **AC2:** Palette "pedras preciosas" definida: safira (azul), esmeralda (verde/sucesso), ametista (roxo/premium), rubi (vermelho/urgente) — todos com opacidade 10-20%
- [ ] **AC3:** Header idêntico em landing e área logada (mesma base, conteúdo diferente)
- [ ] **AC4:** Logo size consistente (`text-xl sm:text-2xl` em ambos)
- [ ] **AC5:** Nenhum "salto" visual ao navegar de landing para login para busca
- [ ] **AC6:** Viewport meta tag explícita (`width=device-width, initial-scale=1`)
- [ ] **AC7:** Cards de resultado de busca usam GlassCard (não solid)
- [ ] **AC8:** Sidebar institucional (login/signup) tem glass effects
- [ ] **AC9:** Dark mode consistente em todas as áreas
- [ ] **AC10:** Mobile: sem diferença de zoom/tamanho entre landing e área logada

---

### GTM-007: Sanitização PNCP — Remoção Completa de Referências
**Prioridade:** P0 (GTM-blocker) | **Estimativa:** 6h | **Sprint:** 1

#### Problema
PNCP é portal gratuito. Mencionar como fonte degrada valor percebido e convida usuário a ir direto na fonte. SmartLic "consulta dezenas de fontes oficiais em tempo real" — e basta.

#### Mapeamento de Ocorrências

**Frontend (user-facing):**

| Arquivo | Linha | Texto Atual | Substituição |
|---------|-------|-------------|--------------|
| `lib/copy/valueProps.ts` | 33 | "PNCP + 27 portais" | "dezenas de fontes oficiais" |
| `lib/copy/valueProps.ts` | 52 | "PNCP + 27 portais" | "cobertura nacional completa" |
| `lib/copy/valueProps.ts` | 97 | "PNCP + 27 portais estaduais" | "fontes governamentais em todos os 27 estados" |
| `lib/copy/comparisons.ts` | 61 | "Apenas PNCP" vs "PNCP + 27" | "Fonte única" vs "Dezenas de fontes oficiais consolidadas" |
| `lib/copy/comparisons.ts` | 174 | "consolidamos PNCP + 27" | "consolidamos dezenas de fontes oficiais" |
| `app/components/Footer.tsx` | 148 | "PNCP e outras fontes públicas" | "fontes oficiais de contratações públicas" |
| `app/buscar/page.tsx` | 126 | "Busca inteligente de licitações" | "Inteligência de decisão em licitações" |
| `app/features/page.tsx` | vários | "PNCP federal + portais" | "todas as fontes federais e estaduais" |

**Backend (error messages):**

| Arquivo | Linha | Texto Atual | Substituição |
|---------|-------|-------------|--------------|
| `routes/search.py` | 225 | "O Portal Nacional de Contratações (PNCP) está temporariamente indisponível" | "Nossas fontes de dados estão temporariamente indisponíveis" |
| `routes/search.py` | 210 | "O PNCP está limitando requisições" | "As fontes de dados estão temporariamente limitando consultas" |

**Backend (technical, manter):**
- `pncp_client.py` — nome técnico do módulo, OK manter internamente
- `schemas.py` — documentação técnica de API, OK manter com nota "internal only"

#### Acceptance Criteria

- [ ] **AC1:** ZERO ocorrências de "PNCP" em qualquer texto visível ao usuário (landing, buscar, planos, features, error messages)
- [ ] **AC2:** Footer diz "fontes oficiais de contratações públicas" (não nomes específicos)
- [ ] **AC3:** Error messages do backend usam "nossas fontes" (já parcialmente feito em STORY-257A/B)
- [ ] **AC4:** `pncp_id` e links para pncp.gov.br nos resultados podem permanecer (são links diretos úteis)
- [ ] **AC5:** Banned phrases em `valueProps.ts` atualizadas com todas variações de "PNCP"
- [ ] **AC6:** Grep de `PNCP` no frontend retorna ZERO matches em arquivos .tsx/.ts (exceto imports técnicos e types)

---

### GTM-008: Reposicionamento da IA — De "Resumos" para "Decisão"
**Prioridade:** P1 | **Estimativa:** 6h | **Sprint:** 2

#### Problema
A IA é apresentada como geradora de resumos ("resumos executivos de 3 linhas", "GPT-4 analisa editais"). Isso é commodity — qualquer ferramenta faz. O diferencial é: IA avalia a oportunidade e orienta a decisão.

#### Copy Atual → Copy Nova

| Onde | Atual | Novo |
|------|-------|------|
| Hero | "IA analisa milhares de editais" | "IA avalia cada oportunidade e indica onde focar para ganhar" |
| Feature | "Resumos executivos de 3 linhas" | "Avaliação objetiva: vale a pena ou não, e por quê" |
| Value prop | "IA que Trabalha para Você" | "Inteligência que reduz incerteza" |
| Feature detail | "GPT-4 analisa editais" | "Análise automatizada de critérios de elegibilidade, competitividade e adequação" |
| Plan feature | "IA Basico/Detalhado/Prioritário" | "Análise Estratégica" (único nível) |
| Email | "Filtramos X licitações" | "Identificamos X oportunidades com alta adequação ao seu perfil" |

#### Acceptance Criteria

- [ ] **AC1:** ZERO menções a "resumo", "resumo executivo", "resumos" em copy user-facing
- [ ] **AC2:** IA posicionada como "avaliação de oportunidade" e "orientação de decisão"
- [ ] **AC3:** Feature de IA descrita como "redução de incerteza", não "redução de texto"
- [ ] **AC4:** Planos não diferenciam "nível de IA" (produto único, IA completa)
- [ ] **AC5:** Email templates atualizados com nova linguagem

---

### GTM-009: Reescrita da Features Page — Transformação, Não Tarefa
**Prioridade:** P1 | **Estimativa:** 6h | **Sprint:** 2

#### Problema
A features page compara "busca manual vs busca automatizada" — básico demais. Precisa comparar cenários: com SmartLic (foco no que importa, entra preparado, taxa de sucesso alta) vs sem SmartLic (perde tempo, entra em licitações ruins, perde oportunidades boas).

#### Escopo

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/features/page.tsx` | Reescrita completa de 5 features + hero + CTA |

#### Features Novas (substituem as atuais)

1. **"Priorização Inteligente"** (substitui "Busca por Setor")
   - Antes: "selecione seu setor e encontramos variações"
   - Agora: "O sistema avalia cada oportunidade com base no seu perfil e indica quais merecem sua atenção"

2. **"Análise de Adequação"** (substitui "Filtragem Inteligente")
   - Antes: "95% de precisão, zero ruído"
   - Agora: "Não precisa ler editais para decidir se vale a pena. O SmartLic avalia requisitos, prazos e valores contra seu perfil"

3. **"Cobertura Nacional Consolidada"** (mantém conceito, muda narrativa)
   - Antes: "PNCP + 27 portais"
   - Agora: "Consulta em tempo real dezenas de fontes oficiais, federais e estaduais. Você nunca perde uma oportunidade por não saber que ela existe"

4. **"Inteligência de Decisão"** (substitui "Resultado em 3 Minutos")
   - Antes: "160x mais rápido, 3 minutos"
   - Agora: "Avalie uma oportunidade em segundos com base em critérios objetivos. Não é sobre ser rápido — é sobre decidir melhor"

5. **"Vantagem Competitiva"** (substitui "Resumos Executivos IA")
   - Antes: "Decida em 30 segundos, não em 20 minutos"
   - Agora: "Enquanto seu concorrente ainda está procurando, você já está se posicionando. Quem encontra antes, compete melhor"

#### Acceptance Criteria

- [ ] **AC1:** Cada feature narra transformação (cenário ruim → cenário bom), não tarefa
- [ ] **AC2:** ZERO métricas de eficiência (tempo, velocidade, %)
- [ ] **AC3:** Custo de não usar presente em pelo menos 2 features
- [ ] **AC4:** Competição/concorrente mencionado para criar urgência real
- [ ] **AC5:** Hero da features page: "O que muda no seu resultado" (não "funcionalidades")
- [ ] **AC6:** CTA final: "Começar a ganhar mais licitações" (não "economizar tempo")

---

### GTM-010: Fluxo de Conversão Trial → Assinatura
**Prioridade:** P1 | **Estimativa:** 10h | **Sprint:** 2

#### Problema
Não há fluxo otimizado para converter trial em assinante. O trial expira e o usuário vê "Trial expirado. Faça upgrade" — genérico, não conecta com valor gerado.

#### Novo Fluxo

```
Trial ativo (dia 1-5) → Valor sendo gerado (analytics)
Trial ativo (dia 6) → Notificação: "Amanhã seu acesso ao SmartLic expira"
Trial expira → Tela de conversão com valor gerado
                ↳ "Você analisou X oportunidades totalizando R$ Y"
                ↳ "Uma única licitação ganha pode pagar o sistema por um ano"
                ↳ CTA: "Continuar por R$ 1.999/mês"
                ↳ 3 níveis de compromisso (mensal/semestral/anual)
```

#### Escopo

| Arquivo | Mudança |
|---------|---------|
| `backend/quota.py` (L651-665) | Mensagem de trial expirado atualizada |
| **Novo componente** | `frontend/app/components/TrialConversionScreen.tsx` |
| `frontend/app/buscar/page.tsx` | Exibir TrialConversionScreen quando trial expirado |
| **Backend analytics** | Endpoint para retornar "valor analisado durante trial" (soma dos valores das licitações retornadas) |

#### Acceptance Criteria

- [ ] **AC1:** Tela de conversão mostra valor gerado durante trial (R$ total de oportunidades analisadas)
- [ ] **AC2:** Mensagem âncora: "Uma única licitação ganha pode pagar o sistema por um ano inteiro"
- [ ] **AC3:** 3 níveis de compromisso apresentados (mensal/semestral/anual) sem comparação de features
- [ ] **AC4:** Tom: confiante, não desesperado. "Continue tendo vantagem" (não "não perca")
- [ ] **AC5:** Se usuário não converter, acesso bloqueado mas dados anteriores acessíveis (via buscas salvas)
- [ ] **AC6:** Notificação proativa no dia 6 do trial (via sistema de mensagens existente)

---

## PARTE 2: STORIES TECHNICAL DEBT — STATUS E AJUSTES

### Legenda de Status

| Símbolo | Significado |
|---------|-------------|
| ✅ | Mantida sem alterações |
| 🔄 | Mantida com ajustes (anotados) |
| ⛔ | Absorvida por story GTM (suprimida) |
| ✓✓ | Já completada |

---

### Sprint 0: Verificação & Quick Wins

| Story | Status | Notas |
|-------|--------|-------|
| **TD-001: Production Verification & Migration 027** | ✅ Mantida | P0 prerequisite. Ajuste: migration 028 (GTM-002) depende desta |
| **TD-002: Fix Pricing Divergence & UX Trust** | ⛔ Absorvida por GTM-002 | Pricing muda completamente. O "9.6x" issue não existe mais |
| **TD-003: Split Requirements + Repository Cleanup** | ✅ Mantida | Independente. Screenshots, dead code, timezone fixes |

### Sprint 1: Segurança & Correções

| Story | Status | Notas |
|-------|--------|-------|
| **TD-004: Remaining Database Security** | ✅ Mantida | Webhook INSERT policy, trigger docs |
| **TD-005: Dialog Primitive & Accessibility** | ✅ Mantida | Reusable `<Dialog>` component — beneficia GTM-006 |
| **TD-006: Error Messages & Navigation UX** | 🔄 Ajustada | Error dictionary DEVE incluir mensagens sem PNCP (alinha com GTM-007) |
| **TD-007: Async Fixes & CI Quality Gates** | ✅ Mantida | `time.sleep` fix + mypy in CI |

### Sprint 2: Consolidação & Refatoração

| Story | Status | Notas |
|-------|--------|-------|
| **TD-008: PNCP Client Consolidation — Investigation** | ✅ Mantida | Necessária independente de GTM |
| **TD-009: PNCP Client Consolidation — Completion** | ✅ Mantida | Reduzir 1585→900 linhas |
| **TD-010: search_pipeline.py Decomposition** | ✅ Mantida | Pipeline modular facilita GTM-004 (first-analysis) |
| **TD-016: Database Improvements** | ✅ Mantida | FK, analytics, triggers |
| **TD-017: Backend Scalability (Redis, Storage)** | ✅ Mantida | Necessária para scale pós-GTM |
| **TD-018: Plan Data Consolidation + Sticky Button** | 🔄 Ajustada | Plan consolidation absorvida por GTM-002. Sticky button permanece |

### Sprint 3: Qualidade & Cobertura

| Story | Status | Notas |
|-------|--------|-------|
| **TD-011: Unquarantine Tests + E2E** | ✅ Mantida | Necessária para qualidade |
| **TD-012: Search State Refactor (Context + useReducer)** | ✅ Mantida | Facilita GTM stories de frontend |
| **TD-013: Unit Tests for New Search Architecture** | ✅ Mantida | Cobertura 60% target |
| **TD-014: Dynamic Imports + Icons** | 🔄 Ajustada | Plan consolidation part absorvida por GTM-002 |
| **TD-015: Tests Pipeline, Onboarding, Middleware** | ✅ Mantida | |
| **TD-019: Backlog (51 items)** | ✅ Mantida | Umbrella story |

### Completadas

| Story | Status |
|-------|--------|
| **STORY-257A: Backend Busca Inquebrável** | ✓✓ Merged |
| **STORY-257B: Frontend UX Transparente** | ✓✓ Merged |

---

## PARTE 3: ROADMAP DE EXECUÇÃO PRIORIZADO

### Sprint 1 (Semana 1-2): Foundation + GTM Core — ~55h

| # | Story | Tipo | Estimativa | Dependência |
|---|-------|------|------------|-------------|
| 1 | **TD-001** | TD | 8h | Nenhuma (prerequisite) |
| 2 | **TD-003** | TD | 3h | Nenhuma |
| 3 | **GTM-007** | GTM | 6h | Nenhuma (pode parallelizar) |
| 4 | **GTM-001** | GTM | 12h | GTM-007 (PNCP removido primeiro) |
| 5 | **GTM-002** | GTM | 16h | TD-001 (migration depends) |
| 6 | **GTM-003** | GTM | 8h | GTM-002 (plano único deve existir) |
| 7 | **GTM-004** | GTM | 10h | GTM-003 (trial configrado) |

> **Paralelismo sugerido:** TD-001 + TD-003 + GTM-007 podem rodar em paralelo. GTM-001 depende de GTM-007. GTM-002/003/004 são sequenciais.

### Sprint 2 (Semana 3-4): Design + Conversão + TD Security — ~60h

| # | Story | Tipo | Estimativa | Dependência |
|---|-------|------|------------|-------------|
| 8 | **TD-004** | TD | 4h | TD-001 |
| 9 | **TD-005** | TD | 4h | Nenhuma |
| 10 | **TD-006** | TD | 8h | GTM-007 (error msgs alinhadas) |
| 11 | **TD-007** | TD | 4h | Nenhuma |
| 12 | **GTM-006** | GTM | 16h | GTM-001 (copy pronta para design) |
| 13 | **GTM-005** | GTM | 8h | GTM-001 (landing redesign pronto) |
| 14 | **GTM-008** | GTM | 6h | GTM-001 (alinhamento de narrativa) |
| 15 | **GTM-009** | GTM | 6h | GTM-008 (IA reposicionada) |
| 16 | **GTM-010** | GTM | 10h | GTM-002 + GTM-003 (plano e trial definidos) |

### Sprint 3 (Semana 5-6): Consolidação Técnica — ~52h

| # | Story | Tipo | Estimativa | Dependência |
|---|-------|------|------------|-------------|
| 17 | **TD-008** | TD | 5h | Nenhuma |
| 18 | **TD-009** | TD | 11h | TD-008 |
| 19 | **TD-010** | TD | 16h | Nenhuma |
| 20 | **TD-011** | TD | 16h | Nenhuma |
| 21 | **TD-018** (sticky btn) | TD | 4h | Nenhuma |

### Sprint 4 (Semana 7-8): Qualidade & Escala — ~72h

| # | Story | Tipo | Estimativa | Dependência |
|---|-------|------|------------|-------------|
| 22 | **TD-012** | TD | 32h | TD-011 |
| 23 | **TD-013** | TD | 16h | TD-012 |
| 24 | **TD-016** | TD | 16h | TD-001 |
| 25 | **TD-014** | TD | 12h | Nenhuma |

### Sprint 5+ (Semana 9+): Escala & Polish — ~48h+

| # | Story | Tipo | Estimativa | Dependência |
|---|-------|------|------------|-------------|
| 26 | **TD-017** | TD | 24h | Nenhuma |
| 27 | **TD-015** | TD | 24h | TD-012 |
| 28 | **TD-019** | TD | Incremental | Ongoing |

---

## PARTE 4: MATRIZ DE IMPACTO

### Impacto no Negócio (por story)

| Story | Impacto | Métrica |
|-------|---------|---------|
| **GTM-001** | 🔴 Crítico | Percepção de marca, posicionamento, conversão |
| **GTM-002** | 🔴 Crítico | Receita por usuário (R$297→R$1999), ticket médio |
| **GTM-003** | 🔴 Crítico | Trial→conversão rate |
| **GTM-004** | 🟠 Alto | Time-to-first-value, activation rate |
| **GTM-005** | 🟡 Médio | Credibilidade, social proof |
| **GTM-006** | 🟠 Alto | Percepção premium, bounce rate |
| **GTM-007** | 🔴 Crítico | Proteção de valor percebido |
| **GTM-008** | 🟠 Alto | Diferenciação competitiva |
| **GTM-009** | 🟡 Médio | Conversão da features page |
| **GTM-010** | 🔴 Crítico | Trial→paid conversion rate |
| **TD-001** | 🔴 Crítico | Segurança, novos signups |
| **TD-012** | 🟠 Alto | Velocidade de desenvolvimento futuro |
| **TD-017** | 🟡 Médio | Escalabilidade horizontal |

### Dependências Críticas

```
TD-001 ──→ GTM-002 ──→ GTM-003 ──→ GTM-004
                              └──→ GTM-010

GTM-007 ──→ GTM-001 ──→ GTM-005
                   └──→ GTM-006
                   └──→ GTM-008 ──→ GTM-009

TD-011 ──→ TD-012 ──→ TD-013
TD-008 ──→ TD-009
TD-001 ──→ TD-016
```

---

## APÊNDICE: Stories Suprimidas/Absorvidas

| Story Original | Absorvida Por | Justificativa |
|---------------|---------------|---------------|
| STORY-173 (Brand Positioning) | GTM-001 | Escopo menor que a reescrita completa |
| STORY-244 (Strategic Copy Landing) | GTM-001 | Mesmo escopo, GTM-001 é mais abrangente |
| TD-002 (Pricing Divergence) | GTM-002 | Pricing muda completamente — "9.6x" issue não existe mais |

---

*Documento gerado em 2026-02-15 com base em auditoria completa de 4 domínios: copy/marketing, backend/billing, design system, backlog existente.*
