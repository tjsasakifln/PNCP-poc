# STORY-352: Ajustar claim "24/7" — manter disponibilidade, corrigir suporte

**Prioridade:** P0
**Tipo:** fix (copy)
**Sprint:** Imediato
**Estimativa:** S
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-350

---

## Contexto

A comparison table e TrustSignals prometem "Disponível 24/7" e "Suporte prioritário 24/7". O sistema teve CRIT-SIGSEGV (crash loop), CRIT-046 (connection pool exhaustion), CRIT-012 (SSE heartbeat gap). Não existe suporte humano 24h para equipe pré-revenue.

## Promessas Afetadas

> "Disponível 24/7"
> "Suporte prioritário 24/7"

## Causa Raiz

"Disponível 24/7" é factualmente correto (Railway não dorme, sistema roda continuamente). Porém "Suporte prioritário 24/7" implica atendimento humano 24h — impossível para equipe pré-revenue. O sistema se adapta à copy: disponibilidade 24/7 é real, suporte 24/7 não é.

## Critérios de Aceite

- [ ] AC1: Manter "Disponível 24/7" em `comparisons.ts:104` — claim factualmente correto. Adicionar tooltip "monitoramento contínuo com alertas automáticos"
- [ ] AC2: Substituir "Suporte prioritário 24/7" por "Suporte dedicado para assinantes" em `TrustSignals.tsx:139`
- [ ] AC3: Adicionar "Suporte 24/7" ao BANNED_PHRASES em `valueProps.ts` (apenas suporte humano — NÃO banir "Disponível 24/7")
- [ ] AC4: Criar Prometheus gauge `smartlic_uptime_pct_30d` calculado a partir dos health checks existentes
- [ ] AC5: Na página `/admin`, exibir uptime real dos últimos 30 dias
- [ ] AC6: Atualizar testes e2e que verificam texto "24/7" se existirem
- [ ] AC7: Revisar `ajuda/page.tsx` para remover "24 horas" se presente

## Arquivos Afetados

- `frontend/lib/copy/comparisons.ts`
- `frontend/components/subscriptions/TrustSignals.tsx`
- `frontend/lib/copy/valueProps.ts`
- `frontend/app/ajuda/page.tsx`

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| `smartlic_uptime_pct_30d` | >99% para claim "alta disponibilidade" | /admin page |

## Notas

- "Disponível 24/7" é factual — Railway mantém containers ativos continuamente.
- "Suporte 24/7" é o único claim que precisa de ajuste (humano ≠ sistema).
- Quando atingir 99.9% consistente por 3 meses, pode publicar SLO formal.
