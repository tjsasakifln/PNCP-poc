# GTM-COPY-009: Cobertura Nacional Completa — Correção de Escopo Comunicacional

**Épico:** GTM-COPY — Reposicionamento Estratégico de Comunicação
**Prioridade:** P0 (Percepção de Valor)
**Tipo:** Fix / Copy
**Estimativa:** M (11 ACs)
**Status:** DONE

## Objetivo

Corrigir toda a comunicação do site que atribui nossas fontes de dados exclusivamente ao "Governo Federal", substituindo por linguagem que reflita o escopo real: **licitações federais, estaduais e municipais**, incluindo fundações, autarquias e empresas públicas de todo o território nacional.

## Problema

Múltiplas páginas usam a expressão "fontes oficiais do Governo Federal" ou "portais oficiais de contratações públicas do Governo Federal". Isso:

1. **Subestima o escopo real** — nossas fontes (PNCP, PCP v2, ComprasGov) agregam licitações de todas as esferas: federal, estadual e municipal
2. **Degrada percepção de valor** — visitante que licita para prefeituras ou governos estaduais pode concluir que o sistema não cobre suas oportunidades
3. **Contradiz o que já comunicamos** — a FAQ diz "Órgãos municipais, estaduais e federais que publicam nos portais oficiais são cobertos", mas o restante do site diz "Governo Federal"
4. **Omite entidades** — fundações, autarquias e empresas públicas são publicadores relevantes e não são mencionados

## Contexto Técnico

O PNCP (Portal Nacional de Contratações Públicas), criado pela Lei 14.133/2021, é mandatório para **todas as esferas** — União, estados, DF e municípios. O Portal de Compras Públicas (PCP v2) e o ComprasGov complementam com editais que não aparecem no PNCP. Portanto, nossas 3 fontes consolidadas cobrem:

- **Esferas:** Federal, estadual, distrital e municipal
- **Entidades:** Administração direta, autarquias, fundações, empresas públicas, sociedades de economia mista
- **Cobertura:** 27 UFs, +98% das oportunidades publicadas em portais oficiais

## Mapeamento de Ocorrências

| Arquivo | Linha | Texto Atual | Problema |
|---------|-------|------------|----------|
| `ajuda/page.tsx` | 155 | "fontes oficiais do Governo Federal" | Federal-only |
| `ajuda/page.tsx` | 191 | "portais oficiais de contratações públicas do Governo Federal" | Federal-only |
| `ajuda/FaqStructuredData.tsx` | 57 | "fontes oficiais do Governo Federal" | Federal-only (SEO) |
| `sobre/page.tsx` | 233 | "portais oficiais de contratações públicas do Governo Federal" | Federal-only |
| `components/InstitutionalSidebar.tsx` | 253 | "fontes oficiais federais e estaduais" | Omite municípios |
| `components/LoadingProgress.tsx` | 17-23 | "fonte: Governo Federal" (6 facts) | Atribuição imprecisa |

**Já corretos (não mudar):**
- `ajuda/page.tsx` L165: "Órgãos municipais, estaduais e federais que publicam nos portais oficiais são cobertos" ✓
- `features/page.tsx`: "Fontes oficiais" + "27 UFs cobertas" ✓
- `lib/copy/valueProps.ts` L106: "fontes oficiais federais e estaduais" → **PRECISA CORRIGIR** (omite municípios)
- `components/landing/DataSourcesSection.tsx`: "fontes oficiais de contratações públicas" ✓
- Páginas `/como-*`: nomeiam portais factualmente, não limitam escopo ✓

## Copy Guidelines

### Vocabulário APROVADO
- "fontes oficiais de contratações públicas"
- "portais oficiais de contratações públicas do Brasil"
- "todas as esferas — federal, estadual e municipal"
- "incluindo autarquias, fundações e empresas públicas"
- "cobertura nacional (27 UFs)"
- "todo o território nacional"
- "administração direta e indireta"
- "órgãos e entidades de todas as esferas"

### Vocabulário PROIBIDO
- ~~"Governo Federal"~~ como qualificador exclusivo de fonte
- ~~"fontes federais"~~ sem menção a estados e municípios
- ~~"portais do Governo Federal"~~ (PNCP é de TODAS as esferas)

### Princípio
> As fontes são oficiais e públicas. O escopo é nacional e cobre todas as esferas administrativas. Comunicar isso com clareza, sem jargão jurídico excessivo.

## Acceptance Criteria

### AC1 — `/ajuda` FAQ "Fontes de Dados" (L155)
- [x] Substituir "fontes oficiais do Governo Federal" por texto que explicite cobertura de todas as esferas
- [x] Sugestão: "Todos os dados são obtidos diretamente de **portais oficiais de contratações públicas do Brasil**, que consolidam licitações federais, estaduais e municipais — incluindo autarquias, fundações e empresas públicas."
- [x] Arquivo: `frontend/app/ajuda/page.tsx`

### AC2 — `/ajuda` FAQ "Confiança e Credibilidade" (L191)
- [x] Substituir "portais oficiais de contratações públicas do Governo Federal" por escopo completo
- [x] Manter menção a "cobertura nacional (27 UFs)" e "consolidação automática"
- [x] Sugestão: "Todos os dados são obtidos de **portais oficiais de contratações públicas do Brasil**, que cobrem licitações de todas as esferas — federal, estadual e municipal. O SmartLic consolida automaticamente múltiplas fontes oficiais para garantir cobertura nacional (27 UFs) e atualização contínua."
- [x] Arquivo: `frontend/app/ajuda/page.tsx`

### AC3 — FAQ Structured Data / SEO (L57)
- [x] Alinhar JSON-LD com o texto corrigido no AC1
- [x] Texto deve ser idêntico à FAQ visível (Google penaliza discrepância)
- [x] Arquivo: `frontend/app/ajuda/FaqStructuredData.tsx`

### AC4 — `/sobre` Seção "Fontes de Dados" (L233)
- [x] Substituir "portais oficiais de contratações públicas do Governo Federal" por escopo completo
- [x] Incluir menção explícita às 3 esferas + entidades da administração indireta
- [x] Sugestão: "Todos os dados utilizados pelo SmartLic vêm de **portais oficiais de contratações públicas do Brasil** — que abrangem licitações federais, estaduais e municipais, incluindo autarquias, fundações e empresas públicas. São dados públicos, abertos e acessíveis a qualquer cidadão."
- [x] Arquivo: `frontend/app/sobre/page.tsx`

### AC5 — InstitutionalSidebar Badge (L253)
- [x] Substituir "fontes oficiais federais e estaduais" por texto que inclua municípios
- [x] Espaço curto (badge) — precisa ser conciso
- [x] Sugestão: "Dados oficiais — federal, estadual e municipal"
- [x] Arquivo: `frontend/app/components/InstitutionalSidebar.tsx`

### AC6 — LoadingProgress Facts (L17-23)
- [x] Substituir atribuição `fonte: "Governo Federal"` nos 6 facts que usam esse valor
- [x] Usar atribuições mais precisas:
  - L17 ("portal nacional centraliza"): `fonte: "Lei 14.133/2021, Art. 174"`
  - L18 ("cidadão pode consultar"): `fonte: "Lei 14.133/2021"`
  - L19 ("APIs públicas"): `fonte: "Portais Oficiais"`
  - L20 ("3 milhões de publicações"): `fonte: "PNCP"`
  - L22 ("pregão eletrônico 80%"): `fonte: "Painel de Compras Governamentais"`
  - L23 ("12% do PIB"): `fonte: "OCDE"` (remover "/ Governo Federal")
- [x] Arquivo: `frontend/app/components/LoadingProgress.tsx`

### AC7 — valueProps.ts (L106)
- [x] Substituir "fontes oficiais federais e estaduais" por "fontes oficiais de todas as esferas"
- [x] Arquivo: `frontend/lib/copy/valueProps.ts`

### AC8 — Audit de Consistência
- [x] Busca global por "Governo Federal" em todo o frontend (exceto node_modules)
- [x] Confirmar que ZERO ocorrências restam em texto user-visible
- [x] Ocorrências em código/comentários/testes são aceitáveis

### AC9 — Testes Existentes
- [x] Testes existentes continuam passando (zero novas falhas vs baseline ~50 fail)
- [x] TypeScript compila sem erros: `npx tsc --noEmit --pretty`
- [x] Se algum snapshot/test valida texto exato que mudou → atualizar o test

### AC10 — SEO Consistency
- [x] Structured data (JSON-LD) em `FaqStructuredData.tsx` alinhado com texto visível
- [x] Meta descriptions das páginas `/ajuda` e `/sobre` não mencionam "Governo Federal"
- [x] Verificar `<title>` e `<meta description>` dessas páginas

### AC11 — Verificação Visual
- [x] Abrir `/ajuda`, `/sobre`, `/login`, `/signup` e confirmar que o texto atualizado renderiza corretamente
- [x] Badge da InstitutionalSidebar não quebra layout (texto curto)
- [x] Loading facts exibem atribuições corretas durante busca

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/ajuda/page.tsx` | AC1, AC2 — 2 textos de FAQ |
| `frontend/app/ajuda/FaqStructuredData.tsx` | AC3 — JSON-LD FAQ |
| `frontend/app/sobre/page.tsx` | AC4 — Seção fontes de dados |
| `frontend/app/components/InstitutionalSidebar.tsx` | AC5 — Badge de dados oficiais |
| `frontend/app/components/LoadingProgress.tsx` | AC6 — 6 facts com atribuição |
| `frontend/lib/copy/valueProps.ts` | AC7 — proof text |

## Notas de Implementação

- **Escopo cirúrgico** — apenas substituição de texto, zero mudanças de lógica ou layout
- **Consistência** — todas as páginas devem comunicar o mesmo escopo (3 esferas + entidades)
- **GTM-COPY-005 retrofix** — esta story corrige comunicação introduzida pelo GTM-COPY-005 (que criou `/sobre` e FAQs de confiança)
- **Nenhum componente novo** — todas as mudanças são edições in-place em arquivos existentes

## Definition of Done

- [x] ACs 1-11 verificados
- [x] Zero menções a "Governo Federal" como qualificador exclusivo de fonte em texto user-visible
- [x] Escopo completo (federal + estadual + municipal + entidades) comunicado em todas as páginas afetadas
- [x] Commit: `fix(frontend): GTM-COPY-009 — cobertura nacional completa (federal+estadual+municipal)`
