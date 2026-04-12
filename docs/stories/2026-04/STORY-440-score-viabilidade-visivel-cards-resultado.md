# STORY-440: Score de Viabilidade Visível nos Cards de Resultado

**Priority:** P0 — Maior impacto isolado em trial conversion
**Effort:** S (1-2 dias)
**Squad:** @dev + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 1 — Semanas 1-2

---

## Contexto

O `viability.py` no backend calcula score de viabilidade com 4 fatores (modalidade 30%, timeline 25%, valor 25%, geografia 20%) e retorna o dado na resposta de busca. Porém, o `ResultCard.tsx` no frontend ignora completamente esse campo — o usuário trial não vê nenhum indicador de qualidade dos resultados.

Isso faz com que todos os editais pareçam igualmente relevantes, removendo a percepção de valor da classificação IA do SmartLic. Um badge simples de viabilidade transforma cada resultado de "edital genérico" em "oportunidade qualificada" — o exato momento-aha que distingue o SmartLic de um agregador de alertas.

**Impacto estimado:** +3-4pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: Badge visual de viabilidade no ResultCard
- [ ] Badge exibido no card de resultado com 3 estados mapeados do campo `viability_level` do backend: Verde ("alta"), Amarelo ("media"), Vermelho ("baixa")
- [ ] Badge contém ícone colorido + texto curto: "Alta viabilidade", "Média viabilidade", "Baixa viabilidade"
- [ ] Badge posicionado abaixo do título do edital, antes do resumo executivo
- [ ] NÃO calcular thresholds no frontend — usar `viability_level` diretamente (já calculado pelo backend)

### AC2: Tooltip com breakdown dos 4 fatores
- [ ] Ao hover/click no badge, tooltip mostra breakdown detalhado:
  - Modalidade: X/30 pts
  - Timeline: X/25 pts
  - Valor: X/25 pts
  - Geografia: X/20 pts
  - Total: X/100 pts
- [ ] Tooltip funciona em mobile (click) e desktop (hover)

### AC3: Visibilidade universal (não gated por plano)
- [ ] Badge visível para usuários trial E pagantes
- [ ] Badge visível para usuários com trial expirado (até fazerem upgrade e buscarem novamente)

### AC4: Graceful fallback
- [ ] Se `viability_score` ausente, null, ou 0 na resposta de busca, badge NÃO é renderizado
- [ ] Ausência do badge não quebra layout do card

### AC5: Componente ViabilityBadge isolado
- [ ] Componente `ViabilityBadge.tsx` criado em `frontend/app/buscar/components/`
- [ ] Props: `level: "alta" | "media" | "baixa" | null | undefined`, `score?: number`, `factors?: Record<string, number>`
- [ ] Campos mapeados do backend: `viability_level`, `viability_score`, `viability_factors`
- [ ] Componente exportado e usado pelo `ResultCard.tsx`

### AC6: Testes unitários
- [ ] Teste: `level="alta"` → badge verde com texto "Alta viabilidade"
- [ ] Teste: `level="media"` → badge amarelo com texto "Média viabilidade"
- [ ] Teste: `level="baixa"` → badge vermelho com texto "Baixa viabilidade"
- [ ] Teste: `level=null` → badge não renderizado
- [ ] Teste: tooltip mostra valores corretos dos 4 fatores de `viability_factors`

---

## Scope

**IN:**
- Componente `ViabilityBadge.tsx` (novo)
- Integração do badge no `ResultCard.tsx`
- Testes unitários do componente
- Tooltip com breakdown dos 4 fatores

**OUT:**
- Alterações no backend (score já é retornado)
- Mudança na lógica de cálculo de viabilidade
- Filtro por score de viabilidade na busca
- Ordenação por viabilidade

---

## Dependencies

- `viability.py` retorna `viability_score` e breakdown na resposta (verificar campo exato na resposta da API)
- Nenhuma dependência de outras stories deste epic

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Campo `viability_score` não está sendo serializado na resposta SSE | Média | Verificar `schemas.py` e resposta do SSE antes de implementar |
| Breakdown dos 4 fatores pode não estar disponível na resposta atual | Média | Se não disponível, tooltip mostra apenas score total |

---

## File List

- [ ] `frontend/app/buscar/components/ViabilityBadge.tsx` — AC5: novo componente
- [ ] `frontend/app/buscar/components/search-results/ResultCard.tsx` — AC1: integrar badge
- [ ] `frontend/__tests__/buscar/ViabilityBadge.test.tsx` — AC6: testes unitários

---

## Dev Notes

- Verificar no response de `POST /buscar` qual é o campo exato: pode ser `viability_score`, `score_viabilidade`, ou nested em `resumo.score_viabilidade`
- Cores Tailwind sugeridas: verde = `text-green-700 bg-green-50 border-green-200`, amarelo = `text-yellow-700 bg-yellow-50 border-yellow-200`, vermelho = `text-red-700 bg-red-50 border-red-200`
- Usar `@radix-ui/react-tooltip` (já no projeto) para o tooltip
- Badge deve usar classes consistentes com `LlmSourceBadge.tsx` existente (mesmo estilo visual)

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +3-4pp |
| 2026-04-12 | @po | GO — Correção: usar `viability_level` do backend (não calcular thresholds no frontend). Props atualizadas. |
