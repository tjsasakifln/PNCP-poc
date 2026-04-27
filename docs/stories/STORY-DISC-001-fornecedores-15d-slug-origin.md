# STORY-DISC-001: [SPIKE] Identificar origem dos slugs malformados `/fornecedores/{15d}` e `/fornecedores/{11d}`

## Status

**Ready (GO @po 2026-04-27)** — promovida Draft → Ready; ver §"Verdict @po"

## Prioridade

P1 — Alto (286 URLs 404 confirmadas — 268 com 15d + 18 com 11d; raiz desconhecida)

## Tipo

Spike / Discovery

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §3.1 + D1)

## Owner

@analyst + @dev

## Story

**As a** time tentando reduzir 404s no GSC,
**I want** investigar e identificar a origem das URLs `/fornecedores/{slug-com-tamanho-errado}`,
**so that** possamos abrir story de implementação fix conhecendo a raiz exata (não chutar).

## Problema

GSC cluster "Não encontrado (404)" reporta:

- **268 URLs `/fornecedores/{15d}`** — slug com 15 dígitos (CNPJ válido tem 14)
- **18 URLs `/fornecedores/{11d}`** — slug com 11 dígitos (CNPJ truncado)

Rota frontend `app/fornecedores/[cnpj]/page.tsx` linha 120 dispara `notFound()` quando regex `/^\d{14}$/.test(cnpj)` falha → 404 esperado para slug malformado. **A pergunta é de onde Google descobriu essas URLs.**

Hipóteses para investigar (não decidir antecipadamente):

1. **Backend retorna CNPJ + dígito extra**: query DB pode estar concatenando algum sufixo (CD verificador secundário, código interno) em algum subset de respostas; sitemap então emite `/fornecedores/{cnpj}{X}`
2. **Link interno bug**: footer/breadcrumb/related-cards com bug de formatação concatenando string corrompida
3. **External backlink antigo**: alguém linkou de versão antiga do site quando havia bug; URLs persistem em backlinks
4. **Bot scraping inserindo string corrompida**: crawler externo pode inserir char/dígito ao montar URL
5. **Sitemap legacy**: shard antigo ainda servido com URLs malformadas

Pattern observado em amostras:
```
/fornecedores/007352600001052   ← parece 00735260000105 + dígito 2
/fornecedores/055467960001042   ← parece 05546796000104 + dígito 2
/fornecedores/444213390001372   ← parece 44421339000137 + dígito 2
```
Sufixo `2` recorrente em ~80% das amostras visíveis — sugere bug determinístico, não aleatório.

## Critérios de Aceite

- [ ] **AC1:** Output: relatório `docs/spikes/2026-04-fornecedores-15d-slug-origin.md` documentando:
  - Lista completa de 286 URLs (do `gsc-404-urls.txt` filtrada)
  - Análise de pattern do dígito extra (qual posição? qual valor mais comum?)
  - Verificação de cada hipótese 1-5 com evidência (ou ausência de evidência)
  - Conclusão: raiz identificada vs raiz indeterminada
- [ ] **AC2:** Validação backend (quando STORY-INC-001 destravar):
  - `curl https://api.smartlic.tech/v1/sitemap/fornecedores-cnpj` retorna lista
  - Verificar se algum CNPJ na resposta tem 15 dígitos (ou >14)
- [ ] **AC3:** Grep frontend extensivo: padrões `${cnpj}`, `cnpj +`, `cnpj.padStart`, `dvVerificador`, `digitoExtra` para localizar concatenação suspeita
- [ ] **AC4:** Logs Sentry: filtrar por `path ~ '/fornecedores/[0-9]{15}'` últimos 30 dias para ver exemplos vivos + referer
- [ ] **AC5:** GSC > Performance > filtrar URL contendo padrão 15-dígitos para ver impressões/queries (de onde Google descobriu)
- [ ] **AC6:** Recomendação para implementação: se raiz identificada, criar nova story com fix; se não identificada, recomendar mitigação (canonical 301 strip-trailing-digit, ou validação client-side mais agressiva)

### Anti-requisitos

- NÃO implementar fix nesse spike — output é discovery, não código produção
- NÃO assumir raiz "óbvia" sem evidência — pode ser combinatório de 2 causas

## Tasks / Subtasks

- [ ] Task 1 — Exportar e analisar pattern (AC: 1)
  - [ ] @analyst lê `gsc-404-urls.txt`, filtra por `/fornecedores/[0-9]{15}` e `[0-9]{11}`
  - [ ] Análise estatística: distribuição dos dígitos extras, posição (sempre fim?)
- [ ] Task 2 — Backend validation (AC: 2)
  - [ ] **Bloqueada por STORY-INC-001** parcial — só essa task
  - [ ] Curl endpoint sitemap quando subir, verificar tamanho dos slugs retornados
- [ ] Task 3 — Frontend grep (AC: 3)
  - [ ] @dev/@analyst executa greps padrões listados
  - [ ] Documenta achados (incluindo nada-encontrado)
- [ ] Task 4 — Sentry deep-dive (AC: 4)
  - [ ] Sentry API com filtro path regex
  - [ ] Capturar referer de N exemplos
- [ ] Task 5 — GSC search analytics (AC: 5)
  - [ ] Via Playwright mesmo protocolo do brief, navegar GSC > Performance, filtrar URL pattern
- [ ] Task 6 — Síntese (AC: 6)
  - [ ] Relatório final com recomendação de próximo passo

## Referência de materiais

- `/mnt/d/pncp-poc/gsc-404-urls.txt` (lista bruta GSC)
- `frontend/app/fornecedores/[cnpj]/page.tsx` (rota afetada)
- `frontend/app/sitemap.ts` linhas 124-145 (cache fornecedores)
- `backend/routes/sitemap_*.py` (endpoints fonte)
- Brief: `docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §3.1

## Riscos

- **R1 (Médio):** Spike pode chegar em "raiz indeterminada" — aceitar como output válido (defer fix para spike maior ou aceitar mitigação)
- **R2 (Baixo):** Sentry pode não ter retention suficiente (>30d) — usar window menor

## Dependências

- **Parcialmente bloqueada por STORY-INC-001** — apenas Task 2 (backend validation)
- **Tasks 1, 3, 4, 5 podem rodar imediatamente** sem backend funcionando

## Verdict @po (2026-04-27)

**GO — Ready (6/6 sections PASS, spike legítimo).**

| Section | Status | Notas |
|---------|--------|-------|
| 1. Goal & Context Clarity | PASS | Output discovery, não fix; 286 URLs concreto; 5 hipóteses ranqueadas |
| 2. Technical Implementation Guidance | PASS | Pattern `dígito 2 ao final` documentado; greps específicos |
| 3. Reference Effectiveness | PASS | Brief + arquivos brutos + paths frontend/sitemap |
| 4. Self-Containment | PASS | Hipóteses + anti-requisitos + critério "raiz indeterminada" aceitável |
| 5. Testing Guidance | PASS | AC1 entrega documento testável (existe ou não), Tasks paralelizáveis |
| 6. CodeRabbit Integration | N/A | Spike não emite código |

**IDS Article IV-A:** spike é categoria CREATE legítima — não há spike prévio sobre slug bug. Aceitar.

**Recomendações ao executor (@analyst + @dev):**
- Tasks 1, 3, 4, 5 podem rodar imediatamente (sem dependência backend)
- Task 2 espera SEN-BE-001/008 destravar `/v1/sitemap/fornecedores-cnpj`
- Output esperado em <4h para Tasks 1+3+5; Task 4 (Sentry) <1h

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Spike criado a partir do brief GSC root-cause §3.1 + D1 |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: 6/6 PASS → GO**. Status: Draft → Ready. Spike paralelizável; Tasks 1,3,4,5 sem bloqueador. |
