# STORY-435: Índice SmartLic de Transparência Municipal — Ranking dos 5.570 Municípios

**Priority:** P2
**Effort:** XL (1-2 semanas)
**Squad:** @dev + @devops
**Status:** InProgress
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 3

---

## Contexto

O **Índice SmartLic de Transparência Municipal** é o ativo de link bait mais ambicioso do epic — e o de maior potencial de backlinks orgânicos de longo prazo.

**Por que funciona para backlinks:**
1. **Prefeituras bem ranqueadas linkam com orgulho:** "Nossa cidade ficou em 3º lugar no Índice SmartLic de Transparência em Compras Públicas" — portais municipais têm DA 30-60 e linkam naturalmente para validar conquistas
2. **Imprensa local cobre obrigatoriamente:** Jornais regionais e sites de notícias municipais cobrem ranking de cidades como pauta local — cada cobertura = 1-3 backlinks
3. **Governo estadual e federal referencia:** TCE (Tribunais de Contas Estaduais), CGU, e portais de transparência citam índices de terceiros quando são metodologicamente sólidos
4. **Acadêmicos usam:** Pesquisadores de administração pública, ciência política e economia citam índices municipais em dissertações e artigos — backlinks `.edu.br`

**Dados disponíveis no datalake (sem coleta adicional):**
- Tempo médio entre publicação e abertura do edital por município (urgência/organização)
- % de licitações conduzidas via pregão eletrônico vs. presencial (modernização)
- Número de fornecedores diferentes que participaram de licitações (diversidade)
- Valor médio de contratos por habitante (proporcionalidade)
- Regularidade de publicação ao longo do ano (consistência)

**Metodologia proposta (5 dimensões, 100 pontos):**

| Dimensão | Peso | Métrica |
|----------|------|---------|
| Transparência Digital | 25pts | % pregão eletrônico vs total |
| Eficiência Temporal | 20pts | Tempo médio publicação→abertura (< 30 dias = full score) |
| Diversidade de Mercado | 20pts | Número de CNPJs distintos como vencedores nos últimos 12 meses |
| Volume de Publicação | 20pts | Total de editais publicados (ajustado por população estimada IBGE) |
| Consistência | 15pts | Coeficiente de variação mensal (publicações regulares = alta nota) |

**Score final:** média ponderada das 5 dimensões, de 0 a 100.

---

## Acceptance Criteria

### AC1: Pipeline de cálculo do Índice

- [x] Criar `backend/services/indice_municipal.py` com função `calcular_indice_municipio(municipio_nome, uf, periodo)` — 5 dimensões de score, cache 1h
- [x] Queries diretas ao Supabase usando campo `municipio TEXT` de `pncp_raw_bids` (campo confirmado no schema)
- [x] Calcular para todos os municípios com ≥ 10 editais no período
- [ ] Job batch de cálculo trimestral: `backend/cron_jobs.py` — pendente (endpoint on-demand implementado como substituto v1)

### AC2: Tabela de persistência do Índice

- [x] Migration Supabase: `supabase/migrations/20260411120000_create_indice_municipal.sql` ✅
  ```sql
  CREATE TABLE indice_municipal (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    municipio_nome TEXT NOT NULL,
    municipio_ibge_code TEXT,
    uf CHAR(2) NOT NULL,
    periodo TEXT NOT NULL,  -- "2026-Q1"
    score_total NUMERIC(5,2),
    score_transparencia_digital NUMERIC(5,2),
    score_eficiencia_temporal NUMERIC(5,2),
    score_diversidade_mercado NUMERIC(5,2),
    score_volume_publicacao NUMERIC(5,2),
    score_consistencia NUMERIC(5,2),
    total_editais INTEGER,
    ranking_nacional INTEGER,
    ranking_uf INTEGER,
    percentil INTEGER,
    calculado_em TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(municipio_nome, uf, periodo)
  );
  CREATE INDEX idx_indice_municipal_periodo ON indice_municipal(periodo);
  CREATE INDEX idx_indice_municipal_uf ON indice_municipal(uf, periodo);
  CREATE INDEX idx_indice_municipal_score ON indice_municipal(score_total DESC);
  ```
- [x] RLS: tabela pública com policy `indice_municipal_public_read` (USING true) + `service_role` write

### AC3: Endpoints da API do Índice

- [x] `GET /v1/indice-municipal?periodo={periodo}&uf={uf}&limit=50&offset=0` — ranking paginado, CORS: `*`
- [x] `GET /v1/indice-municipal/{municipio_slug}` — página individual (`sao-paulo-sp`), CORS: `*`
- [x] `GET /v1/indice-municipal/periodos` — lista de períodos disponíveis
- [ ] `GET /v1/indice-municipal/metodologia` — pendente (adicionado a backlog v2)
- [x] Todos os endpoints públicos (sem autenticação), registrados em `startup/routes.py`

### AC4: Páginas frontends do Índice

- [x] `frontend/app/indice-municipal/page.tsx` — hub com Schema.org Dataset, filtros UF/período, tabela via IndiceClient
- [x] `frontend/app/indice-municipal/IndiceClient.tsx` — client component com tabela, loading skeleton, error state
- [x] `frontend/app/indice-municipal/[municipio-uf]/page.tsx` — score + 5 dimensões + CTA Trial
- [x] SEO: `generateMetadata` dinâmico, `robots: { index: true }`, Schema.org Article/Dataset, canonical correto

### AC5: Geração de imagem OG customizada por município

- [ ] Criar rota `frontend/app/api/og/indice-municipal/route.tsx` usando `@vercel/og` (ou alternativa compatível com Next.js standalone)
- [ ] Imagem 1200×630 com: nome do município, score (número grande), posição no ranking, gráfico simplificado das 5 dimensões, logo SmartLic
- [ ] Usada como `og:image` nas páginas municipais dinamicamente
- [ ] Quando prefeitura ou imprensa compartilha a página = preview automático com o score → incentiva compartilhamento

### AC6: Kit de imprensa para divulgação

- [ ] Criar `docs/seo/indice-municipal-press-kit.md` com:
  - Metodologia completa (para que jornalistas possam citar com precisão)
  - Destaques do primeiro índice: top 10 municípios nacionais, top 5 por UF
  - Estatísticas surpreendentes: "X% dos municípios brasileiros ainda não usam pregão eletrônico"
  - Contato para informações: tiago.sasaki@confenge.com.br
  - Embargo: data e hora de publicação
  
- [ ] Lista de alvos para pitch de imprensa:
  - Jornais regionais dos top 10 municípios (buscar em `jornais.com.br` ou Google)
  - TCE dos estados com destaques (cada TCE tem portal de transparência com notícias)
  - Convergência Digital (convergenciadigital.com.br — cobre tecnologia em governo)
  - JOTA (jota.info — cobre poder público)
  - Agência Brasil (agenciabrasil.ebc.com.br — cobertura federal)

### AC7: Atualização trimestral automatizada

- [ ] Job ARQ: `calcular_indice_municipal_trimestral()` no cron de 1º dia do trimestre (março, junho, setembro, dezembro às 6h UTC)
- [ ] Após calcular: enviar summary por email para tiago.sasaki@confenge.com.br via Resend com: total de municípios calculados, top 5 mudanças de ranking, municípios que subiram/desceram mais
- [ ] Publicar automaticamente novo relatório em `/indice-municipal` com dados do novo período

### AC8: Padrão editorial do conteúdo textual (CRÍTICO — este índice será citado por imprensa e governo)

O Índice Municipal será lido por prefeitos, vereadores, jornalistas e pesquisadores. Metodologia e textos interpretativos precisam de qualidade editorial equivalente a publicação técnica.

- [ ] **Nomenclatura oficial dos municípios:** Usar nome exato conforme IBGE — "São Paulo" (não "SP Capital"), "Belo Horizonte" (não "BH"). Tabela de referência: tabela de municípios IBGE (`ibge.gov.br/cidades-e-estados`) como source of truth no código.
- [ ] **Acentuação impecável em todos os textos gerados:** Labels de gráficos, tooltips, textos de insight, legendas — todos em português correto com acentuação. Incluir em CI um teste que valida ausência de palavras comuns sem acento em textos gerados (ex: "municipio" → erro, "município" → correto).
- [ ] **Metodologia em linguagem técnica acessível:** O documento de metodologia deve ser compreensível por gestor público sem formação em TI, e rigoroso o suficiente para ser citado em paper acadêmico. Proibido jargão técnico sem definição. Proibido linguagem de marketing.
- [ ] **Textos interpretativos sem padrões de AI:** Proibido nas descrições automáticas: "é importante destacar", "fica evidente", "no contexto atual", "de maneira abrangente", "de forma significativa". Cada frase interpretativa deve ter sujeito + verbo + dado concreto. Exemplo correto: "Curitiba registrou tempo médio de 18 dias entre publicação e abertura dos editais — o segundo menor entre capitais, atrás apenas de Florianópolis."
- [ ] **Revisão humana do primeiro Índice publicado:** Antes de qualquer pitch de imprensa, o founder lê o texto completo da página do ranking + metodologia + pelo menos 5 páginas municipais. Story não é Done sem essa aprovação explícita.
- [ ] **Formato de números consistente:** Scores com 1 casa decimal (72,4 pontos). Valores em reais com separadores brasileiros (R$ 1.234.567,89). Datas por extenso no texto corrido ("1º trimestre de 2026", nunca "Q1/2026").

### AC9: Testes

- [x] `pytest tests/test_indice_municipal.py` — **21/21 passed** (endpoints, score calc, cache, 404, CORS)
- [x] `npm test -- --testPathPattern="indice-municipal"` — **11/11 passed**
- [x] `npx tsc --noEmit` — limpo sem erros

---

## Scope

**IN:**
- `backend/services/indice_municipal.py`
- `backend/cron_jobs.py` (job trimestral)
- Migration Supabase `indice_municipal`
- `backend/routes/indice_municipal.py`
- `frontend/app/indice-municipal/` (2 páginas)
- `frontend/app/api/og/indice-municipal/route.tsx`
- `docs/seo/indice-municipal-press-kit.md`

**OUT:**
- Índice por órgão/autarquia (escopo futuro)
- Integração com TCE diretamente (manual por enquanto)
- Histórico retroativo além de 4 trimestres
- Embed de mapa geográfico interativo (mapa de calor Recharts é suficiente para v1)

---

## Dependências

- `pncp_raw_bids` com campo `municipio_nome` ou `municipio_ibge_code` populado (verificar se está presente no schema atual)
- STORY-431 (Observatório) concluída — infraestrutura de relatórios públicos serve de base
- ARQ job queue operacional (já está no projeto)
- Resend configurado (já está no projeto)

---

## Riscos

- **Dados de município inconsistentes:** `municipio_nome` pode ter variações ("São Paulo", "S. Paulo", "SAO PAULO"). Normalização necessária via `slugify` + fuzzy match ou tabela de municípios IBGE.
- **Municípios com poucos dados:** Cidades pequenas podem ter <10 editais no trimestre e serem excluídas. Comunicar claramente na metodologia que o índice cobre apenas municípios com ≥10 editais no período.
- **Reação negativa de prefeituras mal ranqueadas:** Municípios com score baixo podem contestar a metodologia. Mitigação: publicar metodologia completa e aberta, disponibilizar dados brutos para contestação.
- **Escala do job batch:** Calcular 5.570 municípios de uma vez pode ser pesado. Mitigação: processar em batches de 500, timeout de 300s por batch, usar conexão direta ao banco (não via API).

---

## Dev Notes

**2026-04-11 @dev (YOLO implementation):**
- `pncp_raw_bids.municipio` confirmado no schema (migration 20260326000000)
- `query_datalake()` não suporta filtro município → queries diretas ao Supabase via `get_supabase().table("pncp_raw_bids").select(...).eq("municipio", ...)`
- Scores calculados on-demand (cache 1h InMemory) — job trimestral deixado para v2
- Slug format: `{slugify(municipio_nome)}-{uf.lower()}` ex: `sao-paulo-sp`
- Período format: `YYYY-QN` ex: `2026-Q1`
- Mínimo 10 editais para inclusão no ranking (evita ruído estatístico)
- CORS `*` em todos os endpoints (link bait embeddável)

---

## Arquivos Impactados

- `backend/services/indice_municipal.py` ✅ (novo)
- `backend/routes/indice_municipal.py` ✅ (novo)
- `backend/startup/routes.py` ✅ (modificado — import + router registrado)
- `supabase/migrations/20260411120000_create_indice_municipal.sql` ✅ (novo)
- `frontend/app/indice-municipal/page.tsx` ✅ (novo)
- `frontend/app/indice-municipal/IndiceClient.tsx` ✅ (novo)
- `frontend/app/indice-municipal/[municipio-uf]/page.tsx` ✅ (novo)
- `backend/tests/test_indice_municipal.py` ✅ (novo)
- `frontend/__tests__/indice-municipal.test.tsx` ✅ (novo)

---

## Definition of Done

- [ ] Job batch calcula corretamente para pelo menos 100 municípios de teste
- [ ] Migration aplicada em produção sem erros
- [ ] Página de ranking nacional acessível com dados reais
- [ ] Página individual de pelo menos 5 municípios testada
- [ ] Imagem OG gerada corretamente para 3 municípios diferentes
- [ ] Press kit publicado em `docs/seo/`
- [ ] Pitch de imprensa enviado para pelo menos 3 veículos
- [ ] `pytest tests/test_indice_municipal.py` + `npm test` passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — ranking municipal é o ativo de link bait de maior longevidade: prefeituras bem ranqueadas linkam por anos. Atualização trimestral mantém o ativo fresco. |
