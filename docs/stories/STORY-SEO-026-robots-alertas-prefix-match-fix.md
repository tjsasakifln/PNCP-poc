# STORY-SEO-026: robots.txt prefix-match bloqueia `/alertas-publicos` (RFC 9309)

## Status

**Ready (GO @po 2026-04-27)** — promovida Draft → Ready; ver §"Verdict @po" abaixo

## Prioridade

P1 — Alto (280 URLs SEO públicas inacessíveis a crawlers + 5 indexadas com snippet ruim)

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §3.3 + §3.6)
- Confirmação empírica: rota `/alertas-publicos/[setor]/[uf]/page.tsx` existe e renderiza conteúdo público

## Tipo

SEO / Bug / Configuration

## Owner

@dev

## Story

**As a** time de growth orgânico,
**I want** que o robots.txt bloqueie apenas o painel privado `/alertas` (logged-in), não a rota programmatic pública `/alertas-publicos/{setor}/{uf}`,
**so that** as 280 páginas SEO de alertas-publicos sejam crawladas e indexadas pelo Google.

## Problema

`robots.txt` em produção contém:

```
Disallow: /alertas
```

Conforme RFC 9309 §2.2.2 (matching prefix), essa diretiva bloqueia também `/alertas-publicos/*`. GSC reporta:

- **464 URLs no cluster "Bloqueada pelo robots.txt"** total
- **~280 URLs `/alertas-publicos/{categoria}/{uf}`** dentro desse cluster (SEO público, não deveriam ser bloqueadas)
- **5 URLs `/alertas-publicos/materiais_eletricos/{ac,rr,ba,am,pe}` no cluster "Indexada, mas bloqueada pelo robots.txt"** (Google indexou antes do bloqueio; agora exibe snippet ruim)

Frontend tem rotas reais:
- `app/alertas-publicos/[setor]/[uf]/page.tsx` (público SEO)
- `app/alertas-publicos/page.tsx` (público SEO)
- `app/alertas/page.tsx` (privado, requer login)

## Critérios de Aceite

- [ ] **AC1:** robots.txt em produção (https://smartlic.tech/robots.txt) bloqueia `/alertas` (raiz privada) sem prefix-match em `/alertas-publicos`
- [ ] **AC2:** Solução escolhida e justificada inline:
  - Opção A: `Disallow: /alertas/` (com slash final — bloqueia `/alertas/foo` mas não `/alertas-publicos`)
  - Opção B: `Disallow: /alertas$` (Google extension — match exato)
  - Opção C: listar rotas privadas explicitamente (`Disallow: /alertas/page`, etc.)
  - Opção D: adicionar `Allow: /alertas-publicos` defensivo (override por specificity)
- [ ] **AC3:** Validação via Google Robots Testing Tool (ou equivalente curl + parser): `/alertas-publicos/saude/sp` permitido; `/alertas` (raiz privada) ainda bloqueada
- [ ] **AC4:** Teste backend: snapshot de robots.txt commitado em `backend/tests/test_robots_txt.py` ou `frontend/__tests__/robots.test.ts` validando os 4 casos (alertas blocked, alertas-publicos allowed, etc.)
- [ ] **AC5:** Pós-deploy: GSC > Indexação > "Bloqueada pelo robots.txt" cai para <50 URLs em 21 dias (excluindo `/api/og`)
- [ ] **AC6:** Pós-deploy: Solicitar reindexação via GSC para as 5 URLs do cluster "Indexada mas bloqueada" (`/alertas-publicos/materiais_eletricos/{ac,rr,ba,am,pe}`)

### Anti-requisitos

- NÃO permitir `/alertas` raiz a crawlers — é página privada com dados de usuário
- NÃO remover blocks de `/api`, `/dashboard`, `/conta`, `/buscar`, `/pipeline`, `/historico`, `/mensagens`, `/onboarding`, `/recuperar-senha`, `/redefinir-senha`, `/admin`, `/auth/callback` — todos legítimos

## Tasks / Subtasks

- [ ] Task 1 — Decisão técnica (AC: 2)
  - [ ] @dev escolhe entre opções A-D, documenta inline em `frontend/app/robots.ts` (ou `public/robots.txt`)
  - [ ] Preferência sugerida: Opção A (mais portable RFC-compliant) + Opção D defensiva
- [ ] Task 2 — Implementação (AC: 1)
  - [ ] @dev edita `frontend/app/robots.ts` (Next.js dynamic) ou `public/robots.txt` estático
  - [ ] Validar localmente com `curl http://localhost:3000/robots.txt`
- [ ] Task 3 — Testes (AC: 4)
  - [ ] @qa adiciona teste validando 4 casos (alertas/alertas-publicos com e sem subpath)
- [ ] Task 4 — Deploy + validação produção (AC: 3, 5)
  - [ ] Deploy via @devops
  - [ ] Validar com Google Robots Testing Tool ou equivalente
  - [ ] Solicitar reindexação para 5 URLs órfãs

## Referência de implementação

- `frontend/app/robots.ts` (suspeitar — verificar)
- OR `public/robots.txt` estático
- `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx` (rota pública afetada)
- `frontend/app/alertas/page.tsx` (rota privada que deve permanecer bloqueada)
- RFC 9309 §2.2.2: https://www.rfc-editor.org/rfc/rfc9309#name-the-allow-and-disallow-line

## Riscos

- **R1 (Baixo):** Mudança em robots.txt pode demorar até 24h para Google re-fetch — não crítico, mas comunicar timeline
- **R2 (Baixo):** Se Opção A escolhida, garantir que `/alertas-publicos` NÃO termina em `/` redirect para `/alertas/` (não deveria, mas validar)

## Dependências

- **Não bloqueada por STORY-INC-001** — esse fix é puramente frontend/static
- **Coordena com STORY-SEO-019** (`crawler-protection-robots-ratelimit`) — verificar se houve mudança recente

## Verdict @po (2026-04-27)

**GO — Ready (6/6 sections PASS, sem conflito).**

| Section | Status | Notas |
|---------|--------|-------|
| 1. Goal & Context Clarity | PASS | Goal claro: 280 URLs SEO bloqueadas; valor business explícito |
| 2. Technical Implementation Guidance | PASS | 4 opções A-D com trade-offs; arquivos identificados (`frontend/app/robots.ts` ou `public/robots.txt`); RFC 9309 referenciado |
| 3. Reference Effectiveness | PASS | Brief §3.3 + §3.6 + STORY-SEO-022 (Done) + RFC URL específica |
| 4. Self-Containment | PASS | Domínio explicado, anti-requisitos cobrem todas rotas privadas a manter |
| 5. Testing Guidance | PASS | AC4 explicita teste, AC3 valida via Robots Testing Tool, AC5/AC6 mensuração pós-deploy |
| 6. CodeRabbit Integration | N/A | `coderabbit_integration` não configurado em `.aiox-core/core-config.yaml` |

**IDS Article IV-A check:** ADAPT a partir de SEO-022 (Done) — diff <30%, não quebra consumidores. STORY-SEO-019 (crawler-protection) toca robots.txt mas escopo não-overlapping (Crawl-delay vs Disallow rules).

**Sem mudanças solicitadas.** Pode ser puxada imediatamente — não bloqueada por incident backend (puramente frontend/static).

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Story criada a partir do brief GSC root-cause §3.3 + S3 |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: 6/6 PASS → GO**. Status: Draft → Ready. Não bloqueada por incident backend. ADAPT de SEO-022 (Done) — IDS-compliant. |
