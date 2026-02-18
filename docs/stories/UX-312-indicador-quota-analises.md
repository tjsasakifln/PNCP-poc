# Story UX-312: Indicador de Quota de Análises

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 3 SP
**Owner:** @dev

## Problem
Usuário não sabe quantas buscas restam no mês. Descobre só quando quota acaba.

## Acceptance Criteria
- [ ] Badge no header: "342/1000 análises"
- [ ] Tooltip: "Renova em 01/03/2026"
- [ ] Cores: verde (>50%), amarelo (20-50%), vermelho (<20%)
- [ ] Link para planos quando <10%
- [ ] Endpoint `/v1/quota/status` retorna: used, total, reset_date

**Files:** `components/QuotaIndicator.tsx`, `routes/quota.py`
