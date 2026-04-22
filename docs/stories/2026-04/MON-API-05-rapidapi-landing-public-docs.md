# MON-API-05: Distribuição RapidAPI + Landing `/api` + Docs Públicos Separados

**Priority:** P1
**Effort:** M (3 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-API-2026-04](EPIC-MON-API-2026-04.md)
**Sprint:** Wave 1

---

## Contexto

Os endpoints MON-API-03/04 existem mas precisam de **descoberta + docs comerciais + marketplace**:
- Landing `/api` vende pricing tiers
- Swagger público `/api/docs-public` separado do `/docs` interno (que lista endpoints privados)
- Listagem no RapidAPI (DA 91) para SEO + marketplace discovery

---

## Acceptance Criteria

### AC1: Landing page `/api`

- [ ] `frontend/app/api/page.tsx`:
  - Hero: "API de Dados Públicos de Licitações e Contratos — 2M+ registros via REST"
  - Pricing tiers (cards):
    - **Free**: 100 queries/mês grátis, fair-use, sem SLA
    - **Growth R$ 297/mês**: 10.000 queries, p95 SLA 500ms, email support
    - **Scale R$ 997/mês**: 50.000 queries, p95 SLA 300ms, chat support, custom overage R$ 0,50/query
    - **Enterprise (custom)**: volume unlimited, dedicated support, SLA 99.9%
  - Seção "Endpoints disponíveis" com cards resumindo cada endpoint + "Ver docs"
  - Seção "Casos de uso": fintechs, ERPs, compliance platforms, pesquisa acadêmica
  - Código embedding (tabs): cURL, Python, Node.js, Ruby
  - Logos "quem usa" (inicialmente vazio, preencher quando 3+ clientes)
  - CTA "Criar API key grátis" → `/conta/api-keys`

### AC2: Swagger público separado

- [ ] `backend/startup/public_docs.py` configura app FastAPI secundário (ou filtro) que expõe em `/api/docs-public`:
  - Apenas endpoints com decorator/tag `@public_api`
  - OAuth2/JWT removido do spec (mostra só X-API-Key)
  - Custom branding: logo SmartLic, cor, description com contexto
- [ ] `/docs` original permanece com todos endpoints (admin)
- [ ] `openapi.json` público em `/api/openapi.json`

### AC3: Branding headers em todos endpoints

- [ ] Middleware global para rotas `/api/v1/*` adiciona:
  - `X-Data-Source: SmartLic / PNCP (pncp.gov.br)`
  - `X-Rate-Limit-Remaining: N` (usage atual do minuto)
  - `X-Documentation: https://smartlic.tech/api`
  - `Access-Control-Allow-Origin: *` (CORS aberto para dados públicos)

### AC4: RapidAPI submission

- [ ] Criar listagem em https://rapidapi.com:
  - Nome: "Brazilian Public Procurement Data"
  - Categorias: "Government Data", "Business Intelligence", "Finance"
  - 3 endpoints inicialmente: `/supplier/{cnpj}/history`, `/benchmark/price`, `/supplier/{cnpj}/score` (future)
  - Tiers matching pricing SmartLic (RapidAPI cobra 25% commission)
  - Exemplos de request/response
  - SLA declarado 99.5%
- [ ] `docs/api/rapidapi-submission.md` com checklist + prints da submissão
- [ ] Integração técnica: header `X-RapidAPI-Proxy-Secret` valida requests vindo do RapidAPI

### AC5: SEO da landing

- [ ] Title: `"API de Dados de Licitações Públicas — 2M+ Contratos | SmartLic"` (61 chars)
- [ ] Description: `"API REST para acesso a dados de licitações e contratos públicos do Brasil (PNCP). Histórico por CNPJ, benchmark de preços, score de risco. Free tier 100 queries/mês."` (172 chars)
- [ ] JSON-LD `Service` + `Offer` schemas
- [ ] Sitemap: adicionar `/api` com priority=0.9

### AC6: Testes

- [ ] Frontend: landing renderiza sem errors, todos os CTAs funcionam
- [ ] Integration: `X-RapidAPI-Proxy-Secret` rejeita requests sem header válido (quando vindos via RapidAPI)
- [ ] Swagger `/api/docs-public` lista APENAS endpoints públicos (grep contra lista whitelist)
- [ ] CORS funciona: request de origin externa chega com `Access-Control-Allow-Origin: *`

---

## Scope

**IN:**
- Landing `/api` (frontend)
- Swagger público separado
- Middleware branding
- RapidAPI submission + integração
- SEO

**OUT:**
- SDK em linguagens (Python/JS) — v2
- Webhook events (push novos contratos) — v2
- GraphQL — fora de escopo

---

## Dependências

- MON-API-01 + MON-API-02 + MON-API-03 + MON-API-04 (endpoints precisam existir para RapidAPI validar)

---

## Riscos

- **RapidAPI approval delay:** 1-2 semanas; submeter cedo no sprint, não bloqueia release
- **25% commission RapidAPI reduz margem:** aceitável para fase inicial (descoberta > margem); clientes enterprise diretos mantêm 100% margem
- **`/docs` expondo endpoints internos indesejados:** audit manual antes do release; whitelist explícita de endpoints públicos

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `frontend/app/api/page.tsx` (novo)
- `frontend/app/api/layout.tsx` (novo — se diferente do root)
- `backend/startup/public_docs.py` (novo)
- `backend/main.py` (registrar public_docs app)
- `backend/middleware/api_branding.py` (novo)
- `docs/api/rapidapi-submission.md` (novo)
- `frontend/app/sitemap.ts` (estender)

---

## Definition of Done

- [ ] Landing `/api` live em prod, Lighthouse >= 90
- [ ] `/api/docs-public` live + validado: só endpoints públicos aparecem
- [ ] Branding headers em 100% das responses `/api/v1/*`
- [ ] RapidAPI listagem submetida (status: em review OK)
- [ ] CORS validado cross-origin

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — camada comercial e de descoberta sobre endpoints MON-API-03/04 |
