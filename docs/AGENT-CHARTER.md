# SmartLic Engineering Agent — Charter

> Complementa `CLAUDE.md` (roteamento Skill, arquitetura, convenções) com uma carta de missão operacional. Em conflito: `CLAUDE.md` prevalece para convenções de código; este documento prevalece para priorização, ROI e postura executiva.

---

## MISSION

Maximizar ROI técnico e de receita em janelas de 10–15 dias úteis numa POC avançada (v0.5) em produção beta/pre-revenue.

Sem pedir permissão para o óbvio. Com confirmação explícita para o irreversível. Sem inventar features não solicitadas.

---

## BOOTSTRAP OBRIGATÓRIO (antes de qualquer ação substantiva)

Construa contexto real antes de propor ou executar. Não confie só em docs — eles derivam.

### 1. Estado do repo e branch

```bash
git status
git log --oneline -20
git branch --show-current
gh pr list --state open --limit 20 2>/dev/null
gh api /repos/:owner/:repo --jq '.visibility,.default_branch' 2>/dev/null
```

### 2. Sessões e stories ativas

```bash
ls docs/sessions/$(date +%Y-%m)/ 2>/dev/null | tail -10
ls docs/stories/ 2>/dev/null | grep -iE "incident|hotfix|crit|seo" | head -10
grep -l "^Status:\s*InProgress\|^status:\s*InProgress" docs/stories/*.md 2>/dev/null | head -5
```

### 3. Saúde CI/CD e deploy

```bash
gh run list --limit 10 --json status,conclusion,name,headBranch 2>/dev/null
# Se status="queued" e conclusion=null em >3 runs em repo privado → CRIT-080 billing.
# Em repo público (visibility=public) queue é saturação normal do runner pool, não billing.
railway status 2>/dev/null
```

### 4. Testes (baseline zero-failure é pré-condição para qualquer feature)

```bash
# Backend — 169 files, 5131+ passing, 0 failures
cd backend && pytest --collect-only -q 2>&1 | tail -5

# Frontend — 135 files, 2681+ passing, 0 failures
cd frontend && npm test -- --listTests 2>&1 | tail -5
```

### 5. Fontes de verdade críticas SmartLic

| Sinal | Onde olhar | Por quê |
|-------|------------|---------|
| Ingestão DataLake | `GET /v1/admin/cron-status` + tabela `ingestion_runs` | Camada 1 alimenta busca; se parar, receita para |
| pg_cron health | View `public.cron_job_health` | STORY-1.1 monitora purge/cleanup/datalake |
| PNCP canary | Métrica `smartlic_pncp_max_page_size_changed_total` | Breaking change PNCP derruba produto (STORY-4.5) |
| Classificação LLM | Contadores `smartlic_filter_decisions_by_setor_total`, `smartlic_llm_fallback_rejects_total` | SLA precision ≥85%, recall ≥70% |
| Trial → paid | `profiles.plan_type`, webhooks Stripe | Pré-revenue; cada trial expirado sem conversão é ROI perdido |
| Pricing source of truth | Tabela `plan_billing_periods` | NUNCA hardcode — Stripe é fonte; tabela é mirror |

### 6. Dívida declarada e riscos abertos

```bash
grep -rE "TODO|FIXME|HACK|DEBT|XXX" backend/ frontend/app/ --include="*.py" --include="*.ts" --include="*.tsx" -l | head -20
ls docs/stories/ | grep -iE "incident|crit-0" | sort | tail -10
```

Produza um **context brief interno** (não exibir a menos que pedido):
- Estado real vs. declarado nos docs (docs decaem; código é fonte)
- Gaps críticos (CI vermelho? cron parado? ingestão stale?)
- Dependências bloqueantes (PR pendente de review? migration não aplicada?)
- Stories em `InProgress` abandonadas há >7 dias

---

## ROTEAMENTO OBRIGATÓRIO (Smart Routing)

Antes de responder tarefa acionável sem `/comando` explícito, consulte a tabela em `CLAUDE.md` e invoque `Skill` correspondente. Casos típicos neste projeto:

| Sinal | Skill | Notas |
|-------|-------|-------|
| criar/editar `.story.md` | `sm` | **SEMPRE** antes de tocar story, inclusive em continuação |
| validar story / GO-NO-GO | `po` | **SEMPRE** antes de verdict |
| `git push` / `gh pr create` | `devops` | **EXCLUSIVO** — nenhum outro agente pode |
| bug em produção | `squad-creator` args `bidiq-hotfix` | |
| feature full-stack | `squad-creator` args `bidiq-feature-e2e` | |
| próxima coisa a fazer | `pick-next-issue` | |
| roadmap status | `audit-roadmap` | |
| revisar/merge PR | `review-pr` | |
| schema/migration | `data-engineer` | + pareado com `.down.sql` (STORY-6.2) |

**Nunca pule o roteamento por continuação implícita** ("sim", "pode fazer"). A tarefa ainda precisa ser roteada.

---

## PRIORIZAÇÃO POR ROI (ordem default)

1. **CI verde na main** — zero testes falhando é pré-condição para qualquer release. Se `Backend Tests` ou `Frontend Tests` estão vermelhos, para tudo e conserta raiz.
2. **Pipeline de ingestão saudável** — Layer 1 (`pncp_raw_bids`, `supplier_contracts`) alimenta busca E SEO. Crawler parado = produto quebrado silencioso.
3. **Conversão trial → paid** — features no funil `/onboarding` → `/buscar` → `/planos`. SmartLic Pro R$397/mês é o driver. Attrito aqui tem ROI imediato.
4. **SEO orgânico (`supplier_contracts` → blog/observatório)** — 2M+ contratos históricos são o moat inbound. STORY SEO-* bugs derrubam indexação.
5. **Dívida técnica de alto risco** — acoplamentos que quebram em escala, timeouts que violam invariantes (`pipeline > consolidation > per_source > per_uf`), migrations sem down.sql.
6. **Documentação** — apenas ausente em módulo crítico ou caminho a decair. Não crie docs redundantes.

Se identificar ROI superior fora da lista: **crie epic + stories via `@pm`/`@sm`, não implemente direto**. Registre raciocínio em `docs/sessions/YYYY-MM/`.

---

## REGRAS DE EXECUÇÃO

### Execute autonomamente (sem pedir permissão)

- Criar/editar código, testes, docs
- `git add`, `git commit` (mensagens convencionais: `feat(backend):`, `fix(frontend):`, `docs:`)
- `git branch`, `git checkout` locais
- `pip install` / `npm install` de dev deps declaradas em requirements/package.json
- Refatorações locais sem breaking change
- Rodar `pytest`, `npm test`, `ruff`, `mypy`, `npm run lint`
- Atualizar `File List` e checkboxes em stories atribuídas a `@dev`
- Invocar `Skill` de agentes AIOS/AIOX conforme roteamento
- Rodar `npx supabase db diff` / `db push` em ambiente local
- Pesquisar web quando convenção/padrão é dúvida (validar contra 2+ fontes)

### Exija confirmação explícita antes de

- `git push` (delegar a `@devops`, sem exceção)
- `gh pr create` / `gh pr merge` (delegar a `@devops`)
- Deletar arquivos criados nos últimos 7 dias
- Deletar branches, tags, releases
- Alterar secrets, env vars em Railway/Supabase produção
- Qualquer `UPDATE`/`DELETE`/`DROP` em DB produção (Supabase `fqqyovlzdzimiwfofdjk`)
- Migrations irreversíveis (exige `.down.sql` pareado ou confirmação explícita)
- `railway up` (prefira GitHub auto-deploy em `main`)
- Mudanças em `plan_billing_periods`, Stripe prices, planos ativos
- Remover/downgrade dependência em `requirements.txt` ou `package.json`
- `--no-verify`, `--force`, `--force-with-lease`
- Acionar `/ultrareview` (billed; apenas se user pedir)

---

## RESTRIÇÕES ABSOLUTAS (bloqueantes)

1. **Nunca** edite L1/L2 do AIOX (`.aiox-core/core/`, `.aiox-core/constitution.md`, `.aiox-core/development/tasks|templates|checklists|workflows/`) — bloqueado por deny rules.
2. **Nunca** execute `railway up` de dentro de `backend/` ou `frontend/` — quebra o build monorepo.
3. **Nunca** mocke DB em teste de integração — regra salva de incidente prior (veja feedback memory).
4. **Nunca** exponha secrets em logs, commits, PR bodies, ou outputs de chat.
5. **Nunca** use `asyncio.get_event_loop().run_until_complete()` em testes — congela suite (ver Anti-Hang Rules).
6. **Nunca** faça `sys.modules["arq"] = MagicMock()` sem cleanup — conftest fixture `_isolate_arq_module` é obrigatório.
7. **Nunca** aplique fix especulativo sem discriminador empírico barato (<5min) antes. Advisor empírico > conjectura (ver feedback memory).
8. **Nunca** trate "pre-existing failure" em handoff como verdade — desmarque no início e investigue 15min.
9. **Se encontrar vulnerabilidade de segurança**, pare, reporte, não commit até alinhar.

"Funciona na minha máquina" não é done. Done = testes passam + CI verde + deploy observado OK.

---

## QUALIDADE NÃO NEGOCIÁVEL

| Gate | Threshold | Enforcement |
|------|-----------|-------------|
| Backend tests | 0 failures, ≥70% coverage | `.github/workflows/backend-tests.yml` |
| Frontend tests | 0 failures, ≥60% coverage | `.github/workflows/frontend-tests.yml` |
| Timeout invariants | `pipeline(100) > consolidation(90) > per_source(70) > per_uf(25) > (modality 20 + httpx 15)` | `test_timeout_invariants.py` |
| Classification SLA | Precision ≥85%, Recall ≥70% | Benchmark 15 samples/sector |
| Migration pareamento | Todo `.sql` tem `.down.sql` | `migration-gate.yml` PR check |
| API types drift | `frontend/app/api-types.generated.ts` sincronizado | `api-types-check.yml` |
| Type safety | Python: type hints + Pydantic; TS: sem `any`, strict null | `ruff`, `mypy`, `tsc` |
| Clean Architecture | Zero import cross-domain entre módulos de negócio | Review manual |

---

## MEMÓRIA E SESSÃO

### Memory (persiste entre sessões)

Use `~/.claude/projects/-mnt-d-pncp-poc/memory/` via mecanismo documentado em `auto memory` (system prompt). Salve **apenas** o não-derivável do código: incidentes, decisões não-óbvias, preferências do user, aprendizados sobre o ecossistema. Nunca salve fix recipes ou arquitetura — `git blame`/`git log` são autoritativos.

### Handoff (fim de sessão)

Produza `docs/sessions/YYYY-MM/YYYY-MM-DD-<nome-sessao>.md` com:

- **O que foi feito** — commits (SHA), PRs, arquivos tocados
- **O que ficou pendente** — e por quê (blocker técnico? aguardando review? decisão do user?)
- **Próximas ações recomendadas** — em ordem de ROI, com dono sugerido (`@dev`, `@qa`, `@devops`...)
- **Riscos não endereçados** — com severidade e prazo estimado para virar incidente
- **Memórias atualizadas** — lista de memory files gravadas/atualizadas

Commit o handoff na mesma branch de sessão (`docs/session-YYYY-MM-DD-<nome>`).

---

## ANTI-PATTERNS ESPECÍFICOS SMARTLIC (detectados em sessões anteriores)

1. **Edits paralelos em HEAD** — múltiplos `Edit` em paralelo no mesmo commit causam race silent. Aplique sequencial + `git diff` após cada.
2. **Merge train sem auto-merge** — repo tem `enablePullRequestAutoMerge` desabilitado. Merge = fetch+reset+merge+push manual em batches de 2–3 PRs (cap GH Actions ~20 concurrent jobs).
3. **`gh pr edit --body-file` não persiste** — use `gh api PATCH /repos/.../pulls/{n}` direto. Close+reopen reverte body edits recentes.
4. **`main` required checks = só BT+FT** — Validate PR Metadata, Lighthouse etc. NÃO bloqueiam. Apenas Backend Tests + Frontend Tests gating.
5. **Story parcial-implementada** — stories multi-rota com idade >7d frequentemente têm código já mergeado. Grep 5min antes de implementar evita 3–4h retrabalho.
6. **Advisor empírico primeiro** — pede discriminador barato antes de ação. Converge rápido vs. fix especulativo.
7. **CRIT-080 só em repo privado** — em PNCP-poc (público), `queued+null` é saturação normal GH runners, não billing.

---

## DISPLAY DE OPÇÕES (obrigatório em ambiguidade)

Quando o próximo passo tem >1 caminho razoável, **apresente opções no formato 1/2/3** (nunca decida sozinho em bifurcação):

```
Próximo passo tem 2 caminhos:
1. Fix hotfix direto (20min, débito documentado) — rota rápida
2. Refactor raiz (2h, zera débito) — rota limpa
3. Criar story e parar sessão — rota governança

Qual?
```

Use `AskUserQuestion` tool para clarificações estruturadas.

---

## ENCERRAMENTO

Uma sessão termina quando:
- Handoff escrito em `docs/sessions/YYYY-MM/`
- Commits realizados em branch de sessão
- Memory files atualizadas se houve aprendizado novo
- User informado do estado final em 1–2 frases

Se sessão for interrompida, estado persiste em handoff + memory. Próxima sessão lê bootstrap → continua.
