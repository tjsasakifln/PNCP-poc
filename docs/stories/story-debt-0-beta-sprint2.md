# Story: Beta Sprint 2 — Polish & Minor Issues

**Epic:** Beta Issues Resolution
**Status:** Ready
**Sprint:** 2 (Polish)
**Esforço estimado:** ~10h
**Prioridade:** MEDIUM — post-launch OK

---

## Scope

8 issues P3 + 1 P2 (dedup):

### Task 1: ISSUE-027 (P2) — Dedup + agrupamento visual [4h]

- [ ] `backend/consolidation.py`: Parsear `objetoCompra` para indicadores de lote ("lote N", "item N", "grupo N")
- [ ] Se mesmo CNPJ + Jaccard ≥ 0.85 + lotes diferentes → NÃO deduplicar
- [ ] Se mesmo CNPJ + Jaccard ≥ 0.85 + sem lote → relaxar threshold valor 5% → 20%
- [ ] Frontend `SearchResults`: Agrupar bids do mesmo CNPJ + objeto similar sob card pai
- [ ] Mostrar "N lotes do mesmo órgão" com expand
- [ ] Testes: unit test lot detection, regressão cross-source dedup

### Task 2: ISSUE-005 (P3) — Autocomplete no signup [0.25h]

- [ ] `frontend/app/signup/` (SignupForm): Adicionar `autoComplete` nos 4 inputs
- [ ] name→"name", email→"email", password→"new-password", confirmPassword→"new-password"

### Task 3: ISSUE-009 (P3) — Title tag duplicado /status [0.25h]

- [ ] `frontend/app/status/page.tsx`: Usar `title: { absolute: "Status do Sistema | SmartLic" }`

### Task 4: ISSUE-010 (P3) — Fontes de Dados vazio [0.25h]

- [ ] `frontend/app/status/components/StatusContent.tsx:162-180`: Adicionar fallback "Informação de fontes indisponível no momento."

### Task 5: ISSUE-023 (P3) — Flash botão /planos [0.5h]

- [ ] `frontend/app/planos/components/PlanProCard.tsx`: Adicionar prop `loading`
- [ ] Quando `planLoading=true`: skeleton/spinner no CTA (não "Assinar agora")
- [ ] `planos/page.tsx`: Passar `planLoading || profileLoading`

### Task 6: ISSUE-007 (P3) — Conta/Perfil lento [2h]

- [ ] Skeleton loading para sidebar (manter layout estável durante auth)
- [ ] Fetch profile em paralelo com auth (não sequencial)
- [ ] Considerar prefetch via `middleware.ts` ou `getServerSideProps`

### Task 7: ISSUE-018 (P3) — Admin dropdown duplicados [1h]

- [ ] `frontend/lib/plans.ts`: Labels distintos para legacy plans
- [ ] "Consultor Ágil (legacy)", "Máquina (legacy)", "Sala de Guerra (legacy)"
- [ ] Adicionar `consultoria` ao `PLAN_CONFIGS`
- [ ] Filtrar legacy do dropdown a menos que user já tenha o plano

### Task 8: ISSUE-019 (P3) — Admin Uptime/Fontes [1.5h]

- [ ] Verificar se backend `/api/status` retorna `uptime_pct_30d` e `sources`
- [ ] Se não implementado: esconder widgets quando dados indisponíveis
- [ ] Adicionar retry no fetch com backoff

---

## Acceptance Criteria

- [ ] AC1: Bids do mesmo órgão + objeto similar agrupados visualmente
- [ ] AC2: Signup inputs sem warnings no console
- [ ] AC3: Title /status sem duplicação
- [ ] AC4: Fontes de Dados mostra fallback quando vazio
- [ ] AC5: /planos sem flash de estado no CTA
- [ ] AC6: /conta carrega sem layout shift
- [ ] AC7: Admin dropdown sem items duplicados
- [ ] AC8: Admin widgets escondidos quando dados indisponíveis
- [ ] AC9: Todos os testes existentes passam

---

## File List

| File | Change |
|------|--------|
| `backend/consolidation.py` | Lot detection + relaxed value threshold |
| `frontend/app/buscar/components/SearchResults.tsx` | Visual grouping |
| `frontend/app/signup/` (SignupForm) | autocomplete attributes |
| `frontend/app/status/page.tsx` | absolute title |
| `frontend/app/status/components/StatusContent.tsx` | empty-state fallback |
| `frontend/app/planos/components/PlanProCard.tsx` | loading state |
| `frontend/app/planos/page.tsx` | pass loading prop |
| `frontend/app/conta/` | skeleton + parallel fetch |
| `frontend/lib/plans.ts` | distinct legacy labels |
| `frontend/app/admin/` | widget visibility + retry |
