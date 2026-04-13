# CRIT-082: Eliminar Retry Amplification — Prevenir Auto-DDoS

**Status:** Ready
**Priority:** P1 — HIGH (amplificação de falhas, degrada experiência e sobrecarrega backend)
**Epic:** Resiliência Frontend
**Agent:** @dev
**Depends on:** CRIT-080 (deploy funcional)

---

## Contexto

O frontend possui **3 camadas de retry empilhadas** que se multiplicam:

| Camada | Localização | Tentativas | Códigos Retriáveis |
|--------|------------|------------|-------------------|
| **L1: Proxy** | `api/buscar/route.ts` | 3 (0s, 1s, 2s) | 502, 503, 504, 524 |
| **L2: Client** | `useSearchExecution.ts` | 3 (3s, 8s) | 500, 502, 503 |
| **L3: Auto-retry** | `useSearchRetry.ts` | 3 (5s, 10s, 15s) | 502, 503, 504 |

**Resultado:** Uma busca do usuário pode gerar até **4 ciclos × 3 client × 3 proxy = 36 requests** ao backend. Quando o backend está com problemas, isso amplifica a carga e transforma um problema transitório em uma avalanche.

**Experiência do usuário:** O usuário vê "Serviço temporariamente indisponível. Tentando novamente..." repetidamente por até ~83 segundos antes de finalmente ver "Não foi possível processar sua análise."

## Acceptance Criteria

### Simplificar para 1 Camada de Retry Efetiva

- [ ] **AC1**: **Proxy (L1):** Manter 2 tentativas (1 retry) com backoff 1s. Reduzir de 3 para 2 tentativas
- [ ] **AC2**: **Client (L2):** REMOVER retry loop do `useSearchExecution.ts`. Proxy já faz retry — não empilhar
- [ ] **AC3**: **Auto-retry (L3):** Manter como mecanismo de retry VISUAL para o usuário, mas:
  - Reduzir de 3 para 2 tentativas
  - Primeiro countdown: 10s, segundo: 20s
  - Cada tentativa faz 1 request (não 9 como hoje)

### Total após fix: máximo **2 auto-retry × 2 proxy = 4 requests** (era 36)

### Melhorar Feedback ao Usuário

- [ ] **AC4**: Quando proxy retorna 502/503, mostrar imediatamente:
  - "O servidor está se atualizando. Tentaremos novamente em {countdown}s"
  - Botão "Tentar agora" + "Cancelar"
  - **NÃO** tentar silenciosamente em background — o usuário deve ver o que acontece
- [ ] **AC5**: Após última tentativa falhar, mostrar:
  - "Não foi possível conectar ao servidor. Tente novamente em alguns minutos."
  - Botão "Tentar novamente" (manual, sem auto-retry)
  - **NÃO** incluir texto ambíguo sobre "análise pode ter sido concluída"

### Timeout Alignment

- [ ] **AC6**: Proxy timeout: 60s por tentativa (era 180s). Railway mata em ~300s, não faz sentido esperar 180s
- [ ] **AC7**: Client AbortController: 65s (era 185s). Alinhado com proxy + margem
- [ ] **AC8**: Async safety timeout: 120s (manter — SSE pode demorar legitimamente)

### Testes

- [ ] **AC9**: Teste `retry-simplification.test.tsx` — verifica que no máximo 4 requests são feitos por busca
- [ ] **AC10**: Teste `proxy-retry.test.ts` — verifica 2 tentativas máximo no proxy
- [ ] **AC11**: Teste `error-messages-clarity.test.tsx` — verifica que mensagens são claras e acionáveis

## Antes vs Depois

| Métrica | Antes | Depois |
|---------|-------|--------|
| Max requests por busca | 36 | 4 |
| Tempo até erro final (502) | ~83s | ~35s |
| Camadas de retry | 3 | 2 (proxy + visual) |
| Timeout por request | 180s | 60s |
| Mensagem final | Ambígua ("pode ter sido concluída") | Direta ("servidor indisponível") |

## Complexidade

**S** (1–2 dias) — mudanças cirúrgicas em 3 hooks/arquivos + redução de timeouts + 3 novos testes

## Arquivos a Modificar

1. `frontend/app/api/buscar/route.ts` — reduzir MAX_RETRIES para 2, timeout para 60s
2. `frontend/app/buscar/hooks/useSearchExecution.ts` — remover client retry loop
3. `frontend/app/buscar/hooks/useSearchRetry.ts` — reduzir para 2 tentativas
4. `frontend/lib/error-messages.ts` — simplificar mensagens de erro
5. Testes correspondentes
