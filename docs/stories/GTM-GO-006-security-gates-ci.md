# GTM-GO-006: Security Scan Blocking e HSTS no CI

## Epic
GTM Readiness — Redução de Risco de Segurança

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P2 — Risco de segurança

## Estimativa
2h

## Status: DONE

---

## Risco Mitigado

**Risco 1 — Dependências vulneráveis entram silenciosamente:** O CI roda `npm audit` e `safety check` mas ambos são non-blocking (`continue-on-error: true` / `|| true`). Uma dependência com CVE crítico (ex: prototype pollution em lodash, SSRF em axios) pode ser mergeada sem ninguém perceber. O scan existe mas não tem dentes.

**Risco 2 — HSTS ausente:** O backend serve headers de segurança (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, etc.) via `middleware.py` L167-186. MAS: `Strict-Transport-Security` (HSTS) não está presente. Isso significa que a primeira request de um usuário pode ser feita via HTTP (antes do redirect para HTTPS), criando janela para man-in-the-middle. Railway força HTTPS em nível de infra, mas o header HSTS instrui o browser a NUNCA tentar HTTP novamente.

**Impacto se materializar:**
- **Risco 1:** CVE em dependência → exploit → comprometimento de dados de usuário. Probabilidade baixa (POC com poucos usuários), mas impacto catastrófico (LGPD, reputação irrecuperável).
- **Risco 2:** MITM em rede pública (café, aeroporto) captura credencial na primeira request HTTP. Probabilidade muito baixa (Railway força HTTPS), mas fácil de mitigar (1 linha de código).

## Estado Técnico Atual

### Security Scanning:

1. **Backend:** `.github/workflows/backend-ci.yml` L38-42:
   ```yaml
   - name: Security check
     run: pip install safety && safety check --full-report || echo "⚠️ Vulnerabilities found"
   ```
   Status: **Non-blocking** — `|| echo` impede que o CI falhe.

2. **Frontend:** `.github/workflows/tests.yml` L126-134:
   ```yaml
   - name: Security audit
     run: npm audit --audit-level=high || true
   ```
   Status: **Non-blocking** — `|| true` engole qualquer vulnerabilidade.

3. **Trivy:** `.github/workflows/pr-validation.yml` L246-254:
   ```yaml
   - name: Trivy vulnerability scanner
     continue-on-error: true
   ```
   Status: **Non-blocking**.

### Security Headers:

4. **`backend/middleware.py` L167-186** — SecurityHeadersMiddleware presente com:
   - `X-Content-Type-Options: nosniff` ✅
   - `X-Frame-Options: DENY` ✅
   - `X-XSS-Protection: 1; mode=block` ✅
   - `Referrer-Policy: strict-origin-when-cross-origin` ✅
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()` ✅
   - `Strict-Transport-Security` ❌ AUSENTE

### Fragilidade:
O scan de segurança é teatro — roda mas não tem consequência. O HSTS é uma correção trivial (1 linha) com benefício desproporcional ao esforço.

## Objetivo

Garantir que vulnerabilidades conhecidas em dependências sejam detectadas e bloqueiem o merge, e que o transporte HTTPS seja imposto a nível de browser (HSTS), eliminando vetores de ataque evitáveis com esforço mínimo.

## Critérios de Aceite

### Security Scan Blocking

- [x] AC1: `npm audit --audit-level=critical` é **blocking** no CI — falha quando vulnerabilidades CRITICAL existem
  - **Evidência:** Workflow diff removendo `|| true` e adicionando `--audit-level=critical`
  - **Nota:** `--audit-level=critical` (não `high`) para evitar false positives em deps de dev. HIGH permanece como warning.
  - **Aceite:** PR com dependência CRITICAL → CI falha → merge bloqueado

- [x] AC2: `safety check` backend é **blocking** para vulnerabilidades com CVSS ≥ 9.0
  - **Evidência:** Workflow diff configurando threshold
  - **Nota:** Se `safety` não suporta threshold nativo, usar `pip-audit` como alternativa (`pip-audit --fail-on-vuln`)

- [x] AC3: Trivy scan com `--exit-code 1` para severidade CRITICAL
  - **Evidência:** Workflow diff removendo `continue-on-error: true` e adicionando `--severity CRITICAL`

- [x] AC4: Scans HIGH/MEDIUM permanecem como **warning** (non-blocking) para não gerar ruído excessivo
  - **Evidência:** Step separado para HIGH que usa `continue-on-error: true`

### HSTS Header

- [x] AC5: `Strict-Transport-Security: max-age=31536000; includeSubDomains` adicionado ao `SecurityHeadersMiddleware`
  - **Evidência:** Diff de `middleware.py` com a nova linha
  - **Aceite:** `curl -I https://bidiq-backend-production.up.railway.app/health | grep -i strict-transport`

- [x] AC6: Teste unitário verifica que response headers incluem `Strict-Transport-Security`
  - **Evidência:** Teste pytest passa

### Documentação

- [x] AC7: `.env.example` atualizado com nota: "Security scans CRITICAL are blocking in CI. See .github/workflows/ for thresholds."
  - **Evidência:** Diff do arquivo

## Testes

### Backend (pytest) — 2 testes

- [x] T1: Response de qualquer endpoint inclui `Strict-Transport-Security` header
- [x] T2: Valor do HSTS header é `max-age=31536000; includeSubDomains`

### CI/CD — 3 validações

- [x] T3: Introduzir dependência com CVE CRITICAL simulada → CI bloqueia merge
  - **Procedimento:** Adicionar `requests==2.25.0` (CVE conhecida) ao requirements.txt em branch de teste
  - **Resultado esperado:** CI falha no step de security scan
  - **Evidência:** Screenshot do CI falhando
  - **Cleanup:** Reverter dependência

- [x] T4: Verificar que dependencies atuais passam o scan (nenhuma CRITICAL ativa)
  - **Procedimento:** Rodar `npm audit --audit-level=critical` e `pip-audit` localmente
  - **Resultado esperado:** Exit code 0 (sem CRITICAL)
  - **Evidência:** Output do comando

- [x] T5: Verificar que HIGH/MEDIUM não bloqueiam merge
  - **Procedimento:** Observar que warnings são emitidos mas CI não falha
  - **Resultado esperado:** CI verde com warnings visíveis

### Teste de Falha

- [x] T6: Remover HSTS header → teste T1 falha → previne regressão
  - **Procedimento:** Comentar linha do HSTS no middleware → rodar pytest
  - **Resultado esperado:** T1 falha com assertão clara
  - **Evidência:** Output do pytest mostrando failure

## Métricas de Sucesso

| Métrica | Antes | Depois | Verificação |
|---------|-------|--------|-------------|
| Security scans blocking | 0/3 | 3/3 (CRITICAL) | CI config |
| HSTS header | Ausente | Presente (max-age=1y) | `curl -I` |
| CVEs CRITICAL não detectadas | Possível | Impossível (CI bloqueia) | Teste T3 |
| Headers de segurança | 5/6 | 6/6 | Teste T1-T2 |

## Rollback

1. **Security scans:** Reverter para `|| true` / `continue-on-error: true` nos workflows. Tempo: < 3 min.
2. **HSTS header:** Comentar/remover linha no middleware.py. Tempo: < 1 min.
3. **Impacto do rollback de HSTS:** Browsers que já receberam HSTS continuam forçando HTTPS pelo max-age (1 ano). Para reverter no browser: limpar HSTS cache (chrome://net-internals/#hsts). Em produção Railway, HTTPS é forçado na infra, então impacto real é zero.
4. **Impacto do rollback de scans:** Volta ao estado atual (scans cosméticos).

## Idempotência

- Adicionar HSTS a middleware que já tem: header duplicado (idempotente, última instância vence)
- Alterar CI workflow para blocking: idempotente (ya era `true`, vira `false`)
- Re-executar scan: resultado determinístico baseado nas dependências atuais

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `backend/middleware.py` | Modificado — HSTS header (1 linha) |
| `.github/workflows/tests.yml` | Modificado — npm audit blocking para CRITICAL |
| `.github/workflows/backend-ci.yml` | Modificado — safety/pip-audit blocking para CRITICAL |
| `.github/workflows/pr-validation.yml` | Modificado — Trivy blocking para CRITICAL |
| `backend/tests/test_security_headers.py` | Criado — 2 testes |
| `.env.example` | Modificado — nota sobre security scans |

## Dependências

| Tipo | Item | Motivo |
|------|------|--------|
| Usa | `.github/workflows/*.yml` | CI pipelines existentes |
| Usa | `backend/middleware.py` | SecurityHeadersMiddleware existente |
| Paralela | Nenhuma | Independente |
