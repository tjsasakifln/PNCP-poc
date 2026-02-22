# CRIT-018 — Dashboard Retry Storm (190+ Erros sem Backoff)

**Tipo:** Bug / Performance Critico
**Prioridade:** P0 (Resource drain + UX degradado)
**Criada:** 2026-02-22
**Status:** Concluida
**Origem:** Teste de primeiro uso real em producao (UX Expert audit)

---

## Problema

A pagina `/dashboard` dispara 4 requests de analytics simultaneamente a cada ~2 segundos, SEM nenhum backoff ou limite de tentativas. Quando o backend esta indisponivel:

- **190 erros no console em <60 segundos**
- **Requests continuam MESMO apos navegar para outra pagina** (memory leak de interval/timeout)
- CPU e rede do browser desperdicados em requests que vao falhar
- Mobile: drena bateria significativamente

### Evidencias (2026-02-22, ~12:14 UTC)

```
Console errors (amostra dos primeiros 30s):
- [ERROR] Failed to load resource: 502 @ /api/analytics?endpoint=summary
- [ERROR] Failed to load resource: 502 @ /api/analytics?endpoint=searches-over-time
- [ERROR] Failed to load resource: 502 @ /api/analytics?limit=7&endpoint=top-dimensions
- [ERROR] [Dashboard] Fetch error: Erro ao carregar dados
... (repete centenas de vezes)
```

**Pior:** Ao navegar para `/pipeline`, os erros do dashboard CONTINUAM aparecendo no console. O fetch loop nao e limpo no unmount.

### Root Cause

O `dashboard/page.tsx` provavelmente usa `setInterval` ou `useEffect` com retry agressivo que:
1. Nao implementa exponential backoff
2. Nao tem max retry count
3. Nao limpa o interval/timer no component unmount
4. Nao respeita o estado do BackendStatusIndicator (que ja sabe que o backend esta offline)

### Impacto

- **Performance:** Centenas de requests/minuto para servidor offline
- **UX:** Console poluido impossibilita debugging
- **Mobile:** Battery drain
- **Infra:** Se muitos usuarios estao na dashboard, bombardeiam o proxy mesmo com backend down

---

## Solucao

### Abordagem: Circuit breaker no frontend para analytics + cleanup no unmount

### Criterios de Aceitacao

#### Retry com Backoff

- [x] **AC1:** Dashboard usa exponential backoff: 2s → 4s → 8s → 16s → 30s (cap)
- [x] **AC2:** Maximo de 5 tentativas antes de mostrar erro definitivo com botao manual "Tentar novamente"
- [x] **AC3:** Apos 5 falhas, nao faz mais requests automaticos — so manual retry
- [x] **AC4:** Timer de retry e LIMPO no component unmount (useEffect cleanup)

#### Integracao com BackendStatusIndicator

- [x] **AC5:** Se BackendStatusIndicator reporta offline, dashboard NAO faz requests de analytics
- [x] **AC6:** Quando BackendStatusIndicator reporta recovery, dashboard faz 1 tentativa
- [x] **AC7:** Usar um shared state (context ou hook) para status do backend, evitando requests duplicados

#### Error State Visual

- [x] **AC8:** Apos timeout dos retries (5 falhas), dashboard mostra:
  - Icone de nuvem com X
  - "Painel temporariamente indisponivel"
  - "Nossos servidores estao sendo atualizados. Seus dados estarao disponiveis em breve."
  - Botao: "Atualizar agora" (retry manual)
- [x] **AC9:** Skeletons desaparecem apos maximo 10 segundos (substitui por erro ou empty state)
- [x] **AC10:** Nao mostra skeletons infinitamente em nenhum cenario

#### Testes

- [x] **AC11:** Teste: apos 5 falhas de fetch, componente para de fazer requests
- [x] **AC12:** Teste: unmount do componente cancela todos os timers pendentes
- [x] **AC13:** Teste: retry manual funciona apos parada automatica
- [x] **AC14:** Teste: backoff intervals sao respeitados (2s, 4s, 8s, 16s, 30s)
- [x] **AC15:** Nenhum teste existente quebra
- [x] **AC16:** Navegar dashboard → pipeline → dashboard nao duplica retry loops

---

## Arquivos Envolvidos

### Modificados
- `frontend/app/dashboard/page.tsx` — refactor fetch com useFetchWithBackoff + useBackendStatusContext + error state
- `frontend/components/BackendStatusIndicator.tsx` — BackendStatusProvider context + useBackendStatusContext hook
- `frontend/app/layout.tsx` — BackendStatusProvider wrapping app
- `frontend/app/buscar/page.tsx` — migrado para useBackendStatusContext (shared polling)
- `frontend/__tests__/dashboard.test.tsx` — atualizado para novas dependencias + comportamento CRIT-018

### Criados
- `frontend/hooks/useFetchWithBackoff.ts` — hook reutilizavel com backoff + max retries + abort
- `frontend/__tests__/dashboard-retry.test.tsx` — 15 testes de backoff, cleanup, e integracao

---

## Relacao com Outras Stories

- **UX-338:** Cobre o sintoma (skeleton eterno). CRIT-018 cobre a causa raiz (retry storm).
- **CRIT-008:** Implementou BackendStatusIndicator + auto-retry na busca, mas nao no dashboard.
- **CRIT-017:** Sanitiza textos de erro. CRIT-018 evita que erros sequer acontecam em excesso.

**Ordem de execucao recomendada:** CRIT-017 (sanitizar erros) → CRIT-018 (limitar retries) → UX-338 (empty state)

---

## Estimativa

- **Complexidade:** Media (hook novo + refactor dashboard + testes)
- **Risco:** Baixo (dashboard isolado)
- **Dependencias:** CRIT-017 (para mensagens de erro amigaveis no state final)
