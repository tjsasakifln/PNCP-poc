# GTM-GO-003: Rastreabilidade de Release e Rollback Atualizado

## Epic
GTM Readiness — Redução de Risco Operacional

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P1 — Risco operacional

## Estimativa
2h

## Status: PENDING

---

## Risco Mitigado

**Risco 1 — Rastreabilidade:** Em caso de incidente, não é possível determinar rapidamente qual versão está em produção nem quais mudanças ela contém. O CHANGELOG.md existe e é excelente (v0.1.0 a v0.5.0), mas não há git tags vinculando versões a commits específicos. Sem tags, `git describe` não funciona, o deploy não carrega versão semântica, e o rollback exige navegar o git log manualmente.

**Risco 2 — Rollback desatualizado:** O `docs/runbooks/rollback-procedure.md` referencia Vercel para rollback do frontend (linhas 173-242), mas o frontend migrou para Railway na v0.4.0. Se alguém seguir o runbook durante um incidente P0, vai perder tempo tentando rollback no Vercel (que não hospeda mais nada) enquanto o sistema continua fora do ar.

**Impacto se materializar:**
- **Incidente P0 + runbook errado:** MTTR aumenta em 15-30 minutos (tempo de descobrir que Vercel não é mais usado + improvisar rollback no Railway). Em um P0 com SLA informal de 30 min, isso é catastrófico.
- **Sem git tags:** Auditorias e post-mortems ficam imprecisos. "Qual versão causou a regressão?" → resposta é "algum commit da semana passada".

## Estado Técnico Atual

### Rastreabilidade:

1. **CHANGELOG.md** — excelente, 6 versões documentadas (v0.0.1 a v0.5.0) com datas, features, e métricas de teste
2. **Git tags** — zero. `git tag --list` retorna vazio. Nenhuma versão é rastreável por tag.
3. **Versão no código:**
   - `PRD.md` L3: `Versao: 0.5` (manual, pode divergir)
   - `.env.example` L197: `AIOS_VERSION=2.2.0` (framework, não produto)
   - Backend `pyproject.toml` e frontend `package.json` — sem campo `version` do produto

4. **Deploy CI/CD** — `deploy.yml` não injeta versão no artefato. Railway recebe código sem identificador de versão.

### Rollback:

1. **`docs/runbooks/rollback-procedure.md`** (567 linhas) — bem escrito, com severidades, escalation, smoke tests
2. **Erro factual:** Linhas 173-242 descrevem rollback de frontend via Vercel (dashboard + CLI). Frontend está no Railway desde v0.4.0.
3. **Procedimento backend (Railway):** Correto e funcional (linhas 98-168)

## Objetivo

Garantir que em qualquer momento seja possível identificar exatamente qual versão está em produção, qual commit ela representa, e executar rollback do frontend e backend em menos de 5 minutos seguindo documentação precisa e atualizada.

## Critérios de Aceite

### Git Tags

- [ ] AC1: Tags criadas para todas as versões do CHANGELOG: `v0.0.1`, `v0.1.0`, `v0.2.0`, `v0.3.0`, `v0.4.0`, `v0.5.0`
  - **Evidência:** `git tag --list` retorna 6 tags
  - **Nota:** Tags apontam para o commit mais próximo da data de release documentada no CHANGELOG

- [ ] AC2: Tag `v0.5.0` aponta para o SHA do deploy atual em produção
  - **Evidência:** `git log v0.5.0 --oneline -1` mostra commit correto

- [ ] AC3: Script `scripts/create-release.sh` criado para automatizar: `git tag -a vX.Y.Z -m "Release vX.Y.Z"` + `git push origin vX.Y.Z`
  - **Evidência:** Script existe e é executável. `bash scripts/create-release.sh v0.5.1` cria tag e push.
  - **Idempotência:** Se tag já existe, script exibe mensagem e sai sem erro (exit 0)

### Versão no Deploy

- [ ] AC4: Backend `/health` inclui campo `version` populado via env var `APP_VERSION` (default: "dev")
  - **Evidência:** `curl /health | jq .version` retorna "0.5.0" em produção
  - **Nota:** deploy.yml seta `APP_VERSION` automaticamente a partir da tag (se existir) ou do SHA curto

- [ ] AC5: `deploy.yml` injeta `APP_VERSION` no Railway via `railway variables set APP_VERSION=vX.Y.Z` antes do deploy
  - **Evidência:** Diff do workflow mostrando o step adicionado

### Rollback Atualizado

- [ ] AC6: `docs/runbooks/rollback-procedure.md` seção "Phase 2: Frontend Rollback" atualizada de Vercel para Railway
  - **Evidência:** Diff mostrando substituição completa (dashboard + CLI instructions para Railway)
  - **Aceite:** Zero referências a "Vercel" no documento final

- [ ] AC7: Seção de rollback inclui comando Railway CLI exato: `railway service <frontend-service-id> redeploy --commit <sha>`
  - **Evidência:** Comando funcional verificado em staging

- [ ] AC8: Tempo estimado de rollback atualizado no documento: "< 5 min (backend + frontend)"
  - **Evidência:** Texto atualizado no topo do documento

### Documentação de Processo

- [ ] AC9: Seção "Release Checklist" adicionada ao rollback-procedure.md (ou arquivo separado) com:
  1. Atualizar CHANGELOG.md
  2. Criar git tag: `bash scripts/create-release.sh vX.Y.Z`
  3. Verificar tag no GitHub
  4. Deploy via CI (push to main ou workflow_dispatch)
  5. Verificar `APP_VERSION` via `/health`
  - **Evidência:** Checklist existe no documento

## Testes

### T1: Rastreabilidade via tag
- **Procedimento:** `git describe --tags HEAD`
- **Resultado esperado:** Retorna `v0.5.0` ou `v0.5.0-N-gSHA` (se commits após tag)

### T2: Versão no health endpoint
- **Procedimento:** `curl https://bidiq-backend-production.up.railway.app/health | jq .version`
- **Resultado esperado:** Retorna string não-vazia que corresponde à tag/SHA do deploy

### T3: Script de release idempotente
- **Procedimento:** Executar `bash scripts/create-release.sh v0.5.0` quando tag já existe
- **Resultado esperado:** Mensagem "Tag v0.5.0 already exists" + exit 0 (sem erro)

### T4: Rollback procedure validity
- **Procedimento:** Grep no rollback-procedure.md por "vercel" ou "Vercel" (case-insensitive)
- **Resultado esperado:** Zero matches

## Métricas de Sucesso

| Métrica | Antes | Depois | Verificação |
|---------|-------|--------|-------------|
| Git tags | 0 | 6 | `git tag --list \| wc -l` |
| Versão identificável em prod | Não | Sim | `/health` retorna version |
| Referências Vercel no runbook | ~15 | 0 | `grep -ci vercel rollback-procedure.md` |
| Tempo de rollback documentado | "< 5 min" (mas instrução errada) | "< 5 min" (instrução correta) | Validação manual |

## Rollback

1. **Git tags:** Tags podem ser deletadas com `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`. Sem impacto no código.
2. **APP_VERSION:** Remover env var → `/health` retorna "dev" (default). Sem impacto funcional.
3. **Rollback doc:** Reverter via `git revert`. Documento é markdown puro.
4. **Tempo de rollback:** < 2 minutos

## Idempotência

- `git tag -a v0.5.0` falha se tag existe → script detecta e retorna gracefully
- `railway variables set APP_VERSION=v0.5.0` é idempotente (sobrescreve valor existente)
- Edições no rollback-procedure.md são idempotentes (resultado final é determinístico)

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `scripts/create-release.sh` | Criado |
| `docs/runbooks/rollback-procedure.md` | Modificado — Vercel → Railway |
| `.github/workflows/deploy.yml` | Modificado — injetar APP_VERSION |
| `backend/main.py` | Modificado — ler APP_VERSION no /health (se não existir já) |
| `backend/config.py` | Modificado — `APP_VERSION` env var |
| `.env.example` | Modificado — documentar `APP_VERSION` |

## Dependências

| Tipo | Item | Motivo |
|------|------|--------|
| Nenhuma | — | Pode ser executada independentemente |
