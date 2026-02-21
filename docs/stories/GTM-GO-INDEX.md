# GTM-GO: Stories para GO Definitivo

## Contexto

Stories criadas a partir da **Auditoria GTM SmartLic** (2026-02-21) que identificou gaps nos critérios A-J do checklist de GO. Cada story elimina uma vulnerabilidade operacional, financeira ou reputacional concreta — sem adicionar funcionalidades.

**Critério de GO do checklist:** A+B+C+D+E+I a 100% + H1/H2 validados.
**Bloqueador hard:** C4 (alertas), B2 (readiness), D1 (auth 401), I1/I2 (testes) = NO-GO se falhar.

## Status da Auditoria (Baseline)

| Seção | Status Pré-Stories | Bloqueador? |
|-------|-------------------|-------------|
| A — Release & Deploy | ⚠️ 7.7/10 | Não |
| B — Healthchecks | ✅ 10/10 | GO |
| C — Observabilidade | ⚠️ C4 = 5/10 | **SIM (C4)** |
| D — Segurança | ⚠️ D2 = 6/10 | Não (D1 OK) |
| E — Resiliência | ✅ 9/10 | GO |
| F — Performance | ✅ 9.5/10 | GO |
| G — Dados & Custos | ⚠️ G3 = 5/10 | Não |
| H — Fluxo Produto | ✅ 10/10 | GO |
| I — Testes & CI | ✅ 8/10 | GO (I1/I2 OK) |
| J — Operação | ⚠️ 7/10 | Não |

## Stories

| ID | Título | Gap | Prioridade | Est. | Risco |
|----|--------|-----|------------|------|-------|
| **GTM-GO-001** | [Alertas Operacionais Ativos](GTM-GO-001-alertas-operacionais-ativos.md) | C4 | **P0 (NO-GO)** | 2h | Indisponibilidade não detectada |
| **GTM-GO-002** | [Rate Limiting Anti-Abuso](GTM-GO-002-rate-limiting-anti-abuso.md) | D2 | P1 | 4h | Abuso degrada serviço para todos |
| **GTM-GO-003** | [Rastreabilidade de Release](GTM-GO-003-rastreabilidade-release.md) | A1+A3 | P1 | 2h | MTTR aumentado por rollback errado |
| **GTM-GO-004** | [Estimativa de Custo Operacional](GTM-GO-004-estimativa-custo-operacional.md) | G3 | P2 | 3h | Pricing sem base de custo |
| **GTM-GO-005** | [Runbooks e Access Matrix](GTM-GO-005-runbooks-access-matrix.md) | J1+J2 | P2 | 2h | Bus factor = 1 pessoa |
| **GTM-GO-006** | [Security Gates no CI](GTM-GO-006-security-gates-ci.md) | I3+D4 | P2 | 2h | CVE CRITICAL entra silenciosamente |

**Total estimado: 15h**

## Ordem de Execução Recomendada

```
GTM-GO-001 (30 min, NO-GO blocker, zero código)
    ↓
GTM-GO-003 (2h, rastreabilidade, prepara deploy pipeline)
    ↓
GTM-GO-006 (2h, security gates, requer CI green)
    ↓
GTM-GO-002 (4h, rate limiting, maior story com código)
    ↓
GTM-GO-005 (2h, docs operacionais, parallelizável)
    ↓
GTM-GO-004 (3h, custo, requer acesso a dashboards)
```

## Critério de GO Pós-Stories

Quando todas as 6 stories estiverem COMPLETED:

| Seção | Antes | Depois | Delta |
|-------|-------|--------|-------|
| A — Release | 7.7 | 9.5 | +1.8 (tags + rollback) |
| C — Observabilidade | 8.3 | 10 | +1.7 (alertas ativos) |
| D — Segurança | 8.7 | 9.5 | +0.8 (rate limit + HSTS) |
| G — Dados | 8.0 | 9.5 | +1.5 (custo documentado) |
| I — Testes | 8.0 | 9.0 | +1.0 (security blocking) |
| J — Operação | 7.0 | 9.5 | +2.5 (runbooks + access) |

**Score projetado: 100% dos critérios de GO atendidos.**

## Padrão de Cada Story

Toda story neste pacote segue o padrão:

1. **Risco explícito** — qual vulnerabilidade concreta é mitigada
2. **Estado técnico atual** — descrição precisa da fragilidade, sem suposição
3. **Objetivo como efeito no sistema** — não "instalar X" mas "garantir detecção em < 5 min"
4. **Critérios de aceite verificáveis** — com evidência concreta (screenshot, log, CI output)
5. **Métricas definidas** — números, antes/depois, verificação
6. **Teste de falha** — prova de robustez sob erro, não só no happy path
7. **Rollback documentado** — executável em < 5 min, sem conhecimento tribal
8. **Idempotência** — re-executável sem efeitos colaterais
