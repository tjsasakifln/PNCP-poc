# UX-348 — Alinhar Promessa da Landing Page com Entrega da Area Logada

**Status:** pending
**Priority:** P0 — Churn direto (expectation mismatch)
**Created:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** CRIT-027 (busca precisa funcionar primeiro)
**Estimativa:** L

---

## Problema

A landing page promete uma experiencia sofisticada que NAO existe na area logada:

| Landing page promete | Area logada entrega |
|---|---|
| Badge "Recomendada" / "Descartada" por edital | Nenhum badge de recomendacao |
| Score de compatibilidade (8.5/10) | Nenhum score |
| "Por que foi recomendada" com 4 criterios | Nenhuma justificativa por edital |
| Viabilidade Alta/Media/Baixa por edital | Feature flag desligada (VIABILITY_ASSESSMENT_ENABLED=false) |
| Cards elegantes com prazo, valor, UF, modalidade | Cards basicos sem contexto |
| "87% descartados" (framing positivo) | "302 eliminados" (numero cru, framing negativo) |
| Analise de concorrencia e requisitos | Inexistente |

### Impacto

Esse gap e a causa #1 de churn em SaaS: usuario converte pela promessa, cancela pela entrega. Todo o investimento em copy da landing page e anulado no primeiro login.

---

## Solucao

Ativar funcionalidades existentes no backend que ja foram implementadas mas estao desligadas, e ajustar o frontend para exibir informacoes que ja existem na resposta da API.

### Criterios de Aceitacao

**Viabilidade (ja implementada no backend — D04)**
- [ ] **AC1:** Ligar feature flag `VIABILITY_ASSESSMENT_ENABLED=true` em producao
- [ ] **AC2:** Badge de viabilidade (Alta/Media/Baixa) visivel em cada card de resultado
- [ ] **AC3:** Tooltip do badge mostra os 4 fatores (modalidade, prazo, valor, geografia)

**Links para fonte oficial**
- [ ] **AC4:** Cada resultado tem botao/link "Ver edital completo" que abre URL do PNCP/ComprasGov
- [ ] **AC5:** URL construida a partir do `link_edital` ou `numero_controle` presente na resposta da API
- [ ] **AC6:** Link abre em nova aba (target="_blank" com rel="noopener")

**Framing positivo**
- [ ] **AC7:** Header de resultados: "X oportunidades selecionadas de Y analisadas" (nao "Y eliminados")
- [ ] **AC8:** Subtitulo: "Analisamos Y editais em Z estados e selecionamos X com maior aderencia ao seu perfil"
- [ ] **AC9:** Se 0 resultados: "Analisamos Y editais e nenhum correspondeu ao seu perfil no momento. Volte amanha para novas oportunidades."

**Metadados nos cards de resultado**
- [ ] **AC10:** Cada card mostra: valor estimado, UF, prazo restante, modalidade (como na landing)
- [ ] **AC11:** Prazo com cor: verde (>15 dias), amarelo (8-15 dias), vermelho (<8 dias)
- [ ] **AC12:** Valor formatado em R$ com separador de milhar

**Testes**
- [ ] **AC13:** Teste: viability badge renderiza com dados corretos
- [ ] **AC14:** Teste: link para fonte oficial presente em cada card
- [ ] **AC15:** Teste: framing positivo com contagem correta
- [ ] **AC16:** Zero regressoes

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `backend/config.py` | `VIABILITY_ASSESSMENT_ENABLED` default true (ou env var producao) |
| `frontend/app/buscar/components/SearchResults.tsx` | AC7-AC9 framing, AC10-AC12 cards |
| `frontend/app/buscar/components/ViabilityBadge.tsx` | Ja existe — verificar rendering |
| `frontend/app/buscar/page.tsx` | Passar viability data aos componentes |
| `frontend/__tests__/` | Testes AC13-AC16 |

---

## Notas de Implementacao

- `ViabilityBadge.tsx` ja foi implementado em GTM-RESILIENCE-D04 — so precisa ser ativado
- O backend ja calcula viability no pipeline (stage 4.5) — so precisa do feature flag
- `link_edital` ja vem na resposta da API para resultados PNCP (`link_publicacao` no schema)
- Para PCP v2 e ComprasGov, verificar se ha campo de URL no resultado

---

## Referencias

- Audit: C01
- GTM-RESILIENCE-D04: Viability Assessment (implementacao backend + frontend)
- Landing page: secao "SmartLic em Acao" como referencia visual
