# GTM-RESILIENCE-C01 -- Reescrever Copy de Cobertura Nacional

| Campo | Valor |
|-------|-------|
| **Track** | C: Valorizacao de Percepcao |
| **Prioridade** | P1 |
| **Sprint** | 1 |
| **Estimativa** | 4-6 horas |
| **Gaps Cobertos** | UX-01, UX-02, UX-03 |
| **Dependencias** | Nenhuma (puro frontend copy) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

A investigacao de 6 frentes (GTM-STRATEGIC-INVESTIGATION-REPORT.md, Frente 3) revelou que o copy do frontend degrada sistematicamente a percepcao de valor do sistema. Multiplos componentes da landing page comunicam "2 fontes oficiais", "Duas das maiores bases", e listam PNCP + Portal de Compras Publicas pelo nome -- transmitindo ao usuario a mensagem de que o sistema consulta apenas duas bases publicas gratuitas.

Isso contradiz diretamente a estrategia de posicionamento como "inteligencia de decisao" (GTM-001) e reduz a disposicao de pagar R$1.999/mes. O usuario pensa: "posso consultar esses dois sites eu mesmo".

**Regras de copy existentes violadas:**
- GTM-007: Zero mencoes user-visible de PNCP (parcialmente violado -- PNCP aparece em DifferentialsGrid, DataSourcesSection, valueProps.ts)
- GTM-001 AC9-AC11: BANNED_PHRASES inclui "PNCP" mas componentes da landing nao usam a copy library
- GTM-FIX-003: Eliminou 22 false claims, mas "2 fontes" permaneceu pois era factualmente correto

## Problema

### Ocorrencias Identificadas

| Arquivo | Linha Aprox. | Texto Atual | Impacto |
|---------|-------------|-------------|---------|
| `BeforeAfter.tsx` | L91 | "Visao completa do mercado **em duas fontes oficiais**" | Undersells sistema |
| `DataSourcesSection.tsx` | L31 | "Conectados ao PNCP e ao Portal de Compras Publicas -- as duas maiores bases" | Enumera fontes gratuitas |
| `DataSourcesSection.tsx` | L57 | "Duas das maiores bases de licitacoes publicas do Brasil" | Quantifica fontes |
| `DataSourcesSection.tsx` | L58 | "Portal Nacional de Contratacoes Publicas (PNCP) + Portal de Compras Publicas" | Nomes de fontes gratuitas |
| `DataSourcesSection.tsx` | L71 | Badges: `['PNCP (Federal)', 'Portal de Compras Publicas', 'Novas fontes em breve']` | Enumera fontes por nome |
| `DifferentialsGrid.tsx` | L43 | "Dados do PNCP e Portal de Compras Publicas" | Mencao direta |
| `DifferentialsGrid.tsx` | L52 | "PNCP e Portal de Compras Publicas integrados" | Enumera fontes |
| `EnhancedLoadingProgress.tsx` | L51 | "Conectando a 2 fontes oficiais de contratacoes publicas" | Conta fontes durante loading |
| `EnhancedLoadingProgress.tsx` | L223 | "Buscando em 2 fontes oficiais" | Idem |
| `valueProps.ts` | L41 | trustBadge "2 bases oficiais" | Landing trust badge |
| `valueProps.ts` | L99 | "dados consolidados de 2 fontes oficiais principais (PNCP + Portal de Compras Publicas)" | Enumeracao no long description |
| `valueProps.ts` | L102 | proof: "Dados consolidados de PNCP + Portal de Compras Publicas" | Prova cita nomes |
| `valueProps.ts` | L109 | "Consultamos 2 bases oficiais principais" | Quantifica |
| `valueProps.ts` | L112 | proof: "PNCP + Portal de Compras Publicas" | Nomes |
| `features (nationalCoverage)` | L145 | "Consulta 2 bases principais (PNCP + Portal de Compras Publicas)" | Features page |
| `PREFERRED_PHRASES.coverage` | L417 | "PNCP + Portal de Compras Publicas" | Copy guideline contem violacao |
| `comparisons.ts` | ~L50+ | Potenciais mencoes a fontes | A verificar |
| `api/og/route.tsx` | L82 | Badge "2 Fontes" | OG image meta |
| `SearchResults.tsx` | L706 | "({N} fontes consultadas)" | Conta fontes nos resultados |

**Total: 18+ ocorrencias em 8+ arquivos.**

## Solucao

### Estrategia de Reescrita

Substituir TODA mensagem de contagem/enumeracao de fontes por mensagens de **cobertura e confiabilidade**:

| Conceito Atual | Conceito Novo |
|----------------|---------------|
| "2 fontes oficiais" | "Cobertura nacional de licitacoes" |
| "PNCP + Portal de Compras Publicas" | "Fontes oficiais de contratacoes publicas" |
| "Duas das maiores bases" | "+98% das oportunidades publicas do Brasil" |
| Badges com nomes de fontes | Badges com atributos de qualidade (cobertura, atualizacao, confiabilidade) |
| "2 bases oficiais" (trust badge) | "Cobertura +98%" |

### Principios de Copy

1. **Nunca quantificar fontes** -- o numero pode mudar e sempre parece pouco
2. **Nunca enumerar fontes por nome** -- fontes publicas gratuitas degradam valor percebido
3. **Comunicar cobertura percentual** -- "+98% das oportunidades" soa valioso
4. **Comunicar confiabilidade** -- "Dados verificados de fontes oficiais"
5. **Comunicar expansao** -- "Cobertura em constante expansao" (ja existe, manter)

### Variantes A/B Sugeridas

Para copy central, preparar 2 variantes testáveis:

- **Variante A (Cobertura):** "+98% das oportunidades publicas do Brasil analisadas"
- **Variante B (Confianca):** "Cobertura nacional verificada de contratacoes publicas"

---

## Criterios de Aceitacao

### AC1: Eliminar "2 fontes" de BeforeAfter.tsx
- [x] Texto "em duas fontes oficiais" substituido por copy de cobertura (ex: "com cobertura nacional verificada")
- [x] Nenhuma contagem numerica de fontes no componente

### AC2: Reescrever DataSourcesSection.tsx sem enumeracao de fontes
- [x] Subtitulo L31 reescrito sem "PNCP" e sem "Portal de Compras Publicas"
- [x] Heading L57 reescrito: "Duas das maiores bases" -> messaging de cobertura percentual
- [x] Descricao L58 reescrita: sem nomes de fontes
- [x] Badges L71 substituidos: em vez de `['PNCP (Federal)', 'Portal de Compras Publicas', 'Novas fontes em breve']`, usar atributos de qualidade (ex: `['Cobertura +98%', 'Atualizacao continua', 'Dados verificados']`)

### AC3: Limpar DifferentialsGrid.tsx
- [x] Bullet "Dados do PNCP e Portal de Compras Publicas" substituido por "Dados verificados de fontes oficiais"
- [x] Bullet "PNCP e Portal de Compras Publicas integrados" substituido por "Cobertura nacional integrada" ou similar
- [x] Zero mencoes a nomes de fontes especificas

### AC4: Atualizar EnhancedLoadingProgress.tsx
- [x] "Conectando a 2 fontes oficiais" -> "Consultando fontes oficiais" (sem contagem)
- [x] "Buscando em 2 fontes oficiais" -> "Consultando fontes oficiais" (sem contagem)
- [x] Testes em `EnhancedLoadingProgress.test.tsx` atualizados para refletir novo copy

### AC5: Reescrever valueProps.ts
- [x] trustBadge "2 bases oficiais" -> "Cobertura +98%" ou "Cobertura nacional"
- [x] trustBadge detail "PNCP + Portal de Compras Publicas" -> "Fontes oficiais de contratacoes publicas"
- [x] uncertainty.longDescription: remover "2 fontes oficiais principais (PNCP + Portal de Compras Publicas)"
- [x] uncertainty.proof: remover nomes de fontes
- [x] coverage.longDescription: remover "2 bases oficiais principais (PNCP + Portal de Compras Publicas)"
- [x] coverage.proof: remover nomes de fontes
- [x] PREFERRED_PHRASES.coverage: remover "PNCP + Portal de Compras Publicas", substituir por "fontes oficiais" generico
- [x] features.nationalCoverage.withSmartLic: remover "2 bases principais (PNCP + Portal de Compras Publicas)"

### AC6: Atualizar OG image route
- [x] `api/og/route.tsx` L82: badge "2 Fontes" substituido por "Cobertura Nacional" ou "+98%"

### AC7: Ajustar SearchResults.tsx
- [x] L706: "({N} fontes consultadas)" substituido por copy que nao conta fontes (ex: "dados de multiplas fontes" ou remover)
- [x] L714: mensagem de partial failure revisada -- nao mencionar "Uma fonte" como contagem

### AC8: Adicionar "contagem de fontes" a BANNED_PHRASES
- [x] Adicionar a `BANNED_PHRASES` em valueProps.ts: `"2 fontes"`, `"duas fontes"`, `"2 bases"`, `"duas bases"`, contagem numerica de fontes
- [x] Rodar `validateCopy()` em TODO copy visivel e verificar zero violacoes

### AC9: Manter copy library como source of truth
- [x] Componentes da landing page que tinham copy hardcoded agora importam de `valueProps.ts` ou `comparisons.ts` quando possível
- [x] Pelo menos DataSourcesSection e DifferentialsGrid referenciam constantes de copy centralizadas

### AC10: Zero regressao visual
- [x] Layout e espacamento dos componentes preservados apos mudanca de texto
- [x] Dark mode funcional em todos os componentes alterados
- [x] Responsividade preservada (mobile 375px, tablet 768px, desktop 1280px)

### AC11: Testes atualizados
- [x] `EnhancedLoadingProgress.test.tsx` L39 e L448: assercoes de texto atualizadas
- [x] `source-indicators.test.tsx` L151/L176: assercao "2 fontes consultadas" atualizada ou removida
- [x] Todos os testes existentes passam apos mudancas
- [x] Nenhum novo teste failure introduzido vs baseline (33 frontend pre-existentes)

### AC12: comparisons.ts auditado
- [x] Verificar e limpar qualquer mencao a "PNCP", "Portal de Compras Publicas", contagem de fontes em `comparisons.ts`
- [x] Copy substituido por mensagem de cobertura/confiabilidade

### AC13: Variantes A/B preparadas
- [x] Copy central do DataSourcesSection tem pelo menos 2 variantes documentadas em comentario no codigo
- [x] Variantes sao trocaveis por constante ou feature flag simples (ex: `COPY_VARIANT: 'coverage' | 'confidence'`)

---

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/components/landing/BeforeAfter.tsx` | Reescrever copy L91 |
| `frontend/app/components/landing/DataSourcesSection.tsx` | Reescrever copy L31, L57, L58, L71 |
| `frontend/app/components/landing/DifferentialsGrid.tsx` | Reescrever bullets L43, L52 |
| `frontend/components/EnhancedLoadingProgress.tsx` | Remover contagem L51, L223 |
| `frontend/lib/copy/valueProps.ts` | Reescrever trustBadges, proofs, longDescriptions, PREFERRED_PHRASES, BANNED_PHRASES |
| `frontend/lib/copy/comparisons.ts` | Auditar e limpar mencoes |
| `frontend/app/api/og/route.tsx` | Badge "2 Fontes" -> "Cobertura Nacional" |
| `frontend/app/buscar/components/SearchResults.tsx` | Mensagem L706 fontes consultadas |
| `frontend/__tests__/EnhancedLoadingProgress.test.tsx` | Atualizar assercoes de texto |
| `frontend/__tests__/source-indicators.test.tsx` | Atualizar assercoes de texto |
| `frontend/__tests__/landing/DifferentialsGrid.test.tsx` | Atualizar se existir assercao de texto |
| `frontend/app/components/InstitutionalSidebar.tsx` | "2 bases oficiais" -> "Cobertura nacional de fontes oficiais" |
| `frontend/app/planos/page.tsx` | "PNCP e Portal de Compras Publicas integrados" -> cobertura nacional |

---

## Dependencias

- **Nenhuma dependencia tecnica** -- esta story e puramente frontend copy change
- **Nao depende de backend** -- nenhuma mudanca de schema ou API
- **Pre-requisito para C-02 e C-03** -- estabelece o tom de copy que sera usado nos novos indicadores

---

## Definition of Done

- [x] Zero ocorrencias de "2 fontes", "duas fontes", "2 bases", "duas bases" em qualquer arquivo `.tsx` ou `.ts` do frontend
- [x] Zero mencoes de "PNCP" ou "Portal de Compras Publicas" em componentes user-visible (exceto SearchResults source badges toggle que e power-user feature)
- [x] BANNED_PHRASES atualizado com padroes de contagem de fontes
- [x] `npm run build` passa sem erros (compilacao OK, 46/46 pages; copyfile error e pre-existente Windows-only)
- [x] `npm test` sem novas failures vs baseline (32 fail vs 33 baseline = 1 melhoria)
- [x] `npx tsc --noEmit --pretty` limpo
- [ ] Review visual: landing page, loading, resultados -- copy coerente e sem enumeracao
