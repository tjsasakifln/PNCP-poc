# STORY-355: ROI calculator — defaults honestos e disclaimers

**Prioridade:** P1
**Tipo:** fix (copy + lógica)
**Sprint:** Sprint 2
**Estimativa:** M
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-356, STORY-357

---

## Contexto

O ROI calculator usa defaults agressivos: 8.5h busca manual vs 0.05h SmartLic (170x multiplier). A copy "Investimento se paga na primeira licitação ganha" implica causalidade — SmartLic encontra licitações mas não ajuda a ganhar. Consultorias de licitação (público sofisticado) perceberão a inflação.

## Promessa Afetada

> "Investimento se paga na primeira licitação ganha"
> ROI calculator com 170x multiplier implícito

## Causa Raiz

ROI calculator usa `timeSavedPerSearch: 8.5` (horas) vs `smartlicTimePerSearch: 0.05` (horas) — defaults inflados. A copy "se paga na primeira licitação ganha" é copy de vendas intencional e será mantida. O sistema (defaults do calculator) precisa ser ajustado para que os números sejam defensáveis, sustentando o claim.

## Critérios de Aceite

- [ ] AC1: Adicionar disclaimer ao ROI calculator: "* Valores estimados. SmartLic auxilia na descoberta e priorização de oportunidades, não garante vitória em licitações."
- [ ] AC2: Ajustar `timeSavedPerSearch` de `8.5` para `3.0` em `roi.ts` (default mais conservador — busca + triagem inicial, não análise completa)
- [ ] AC3: Manter "Investimento se paga na primeira licitação ganha" em `valueProps.ts:216` — copy intencional de vendas. O sistema entrega valor suficiente para sustentar o claim com defaults honestos
- [ ] AC4: Ajustar `potentialReturn` para cálculo dinâmico baseado nos inputs reais (não hardcoded "500x")
- [ ] AC5: Adicionar cenário "conservador" ao lado do default na UI do calculator
- [ ] AC6: NÃO banir "se paga na primeira licitação" — copy válida. Apenas garantir que defaults do calculator suportam o claim
- [ ] AC7: Testes: verificar que disclaimer aparece em todos os cenários do calculator

## Arquivos Afetados

- `frontend/lib/copy/roi.ts`
- `frontend/lib/copy/valueProps.ts`
- `frontend/app/pricing/page.tsx`
- `frontend/app/planos/page.tsx`

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| Disclaimer visível | 100% dos cenários | E2E test |
| ROI multiplier default | <50x (era 170x) | Code review |

## Notas

- Copy agressiva é intencional — "se paga na primeira licitação ganha" é provocativo por design.
- O ajuste é nos defaults do calculator (defensáveis), não na copy.
- Disclaimer protege legalmente sem enfraquecer a mensagem.
