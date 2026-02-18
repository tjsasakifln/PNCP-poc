# Story UX-319: Heartbeat em Progresso "Em Tempo Real"

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev

## Problem
Texto diz "em tempo real" mas fica congelado em 18% por 30s+. Parece travado.

## Acceptance Criteria
- [ ] Backend emite heartbeat SSE a cada 5s (mesmo sem progresso)
- [ ] Frontend detecta falta de heartbeat >10s
- [ ] Mostra "Processando..." com spinner quando sem heartbeat
- [ ] Timeout SSE após 30s sem heartbeat → reconnect
- [ ] Telemetria de heartbeat gaps (Sentry)

**Files:** `backend/progress.py`, `app/buscar/useSearchProgress.ts`
