# GTM-GO-005: Runbooks Operacionais Completos e Access Matrix

## Epic
GTM Readiness — Redução de Risco Operacional

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P2 — Risco operacional

## Estimativa
2h

## Status: PENDING

---

## Risco Mitigado

**Risco 1 — Conhecimento tribal:** Toda a operação do SmartLic depende de uma única pessoa (tiago.sasaki@gmail.com). Se essa pessoa estiver indisponível durante um incidente P0, ninguém sabe: quais credenciais usar, como acessar Railway, como fazer rollback, ou sequer para quem ligar.

**Risco 2 — Contatos placeholder:** O `docs/runbooks/rollback-procedure.md` (linhas 548-566) tem 4 campos de contato com "____________" (vazios). O `docs/archive/deployment/incident-response-story165.md` referencia @oncall-dev, @devops-lead, @db-team — aliases que não mapeiam para pessoas reais.

**Risco 3 — Sem access matrix:** Não existe documento que liste quem tem acesso a Railway, Supabase, Stripe, Sentry, GitHub, OpenAI. Se uma credencial for comprometida, não se sabe qual escopo de dano é possível nem quem pode revogar.

**Impacto se materializar:**
- **Incidente P0 com fundador indisponível:** MTTR indefinido. Sistema pode ficar fora do ar por horas sem ninguém capaz de agir.
- **Offboarding futuro:** Sem access matrix, revogar acesso de um membro exige auditoria manual em 7+ serviços.
- **Auditoria de segurança:** Qualquer auditor ou investidor perguntará "quem tem acesso a quê?" — resposta atual: "não sabemos".

## Estado Técnico Atual

### O que existe:

1. **Runbooks robustos para cenários específicos:**
   - `docs/runbooks/monitoring-alerting-setup.md` (887 linhas) — monitoring stack, alerts, incident response
   - `docs/runbooks/PNCP-TIMEOUT-RUNBOOK.md` (450 linhas) — PNCP-specific troubleshooting
   - `docs/runbooks/rollback-procedure.md` (567 linhas) — rollback procedures

2. **Contato primário documentado:** `tiago.sasaki@gmail.com` (24/7) em monitoring-alerting-setup.md L861-877

3. **Escalation path teórico:** incident-response-story165.md L769-773 define P0→P3 escalation com @oncall-dev, @devops-lead, etc. — **aliases sem mapeamento para pessoas reais**.

### O que falta:

1. **Access matrix:** Zero documentação sobre quem tem acesso a quais serviços
2. **Contatos reais preenchidos:** 4 campos vazios em rollback-procedure.md
3. **Runbook genérico de outage:** Runbooks existentes são para cenários específicos (PNCP, rollback), não há "serviço fora do ar — o que fazer primeiro?"
4. **Runbook de third-party failures:** Nada para "Supabase está fora do ar" ou "OpenAI retorna 500"

## Objetivo

Garantir que qualquer membro do time (atual ou futuro) consiga responder a um incidente P0 sem depender de conhecimento verbal ou acesso privilegiado de uma única pessoa, usando apenas documentação versionada no repositório.

## Critérios de Aceite

### Access Matrix

- [ ] AC1: `docs/operations/access-matrix.md` criado com tabela:
  | Serviço | URL Console | Quem tem acesso | Tipo de acesso | Como revogar |
  - Serviços obrigatórios: Railway, Supabase, Stripe, Sentry, GitHub, OpenAI, UptimeRobot, domínio (smartlic.tech)
  - **Evidência:** Arquivo commitado, cada linha preenchida (sem placeholders)
  - **Aceite:** Para cada serviço, "Como revogar" tem instrução executável (ex: "Settings → Team → Remove member")

- [ ] AC2: Seção "Credenciais Emergenciais" com instruções de onde encontrar credenciais de backup (ex: 1Password vault, Bitwarden, ou outro gerenciador usado)
  - **Evidência:** Seção existe no documento
  - **Nota:** NÃO documentar as credenciais em si — apenas onde encontrá-las

### Matriz RACI

- [ ] AC3: Matriz RACI documentada em `docs/operations/access-matrix.md` com responsabilidades por operação crítica:
  | Operação | Responsible | Accountable | Consulted | Informed |
  - Operações obrigatórias: Deploy produção, Rollback, Resposta a incidente P0, Rotação de segredos, Migração de banco, Monitoramento pós-deploy
  - **Evidência:** Tabela RACI preenchida com nomes reais (não aliases)
  - **Aceite:** Para cada operação crítica, há pelo menos 1 Responsible e 1 Accountable

### Contatos Preenchidos

- [ ] AC4: `docs/runbooks/rollback-procedure.md` linhas 548-566 — todos os 4 campos de contato preenchidos com dados reais (nome + email + telefone)
  - **Evidência:** Diff mostrando substituição de "____________" por dados reais
  - **Aceite:** Zero campos vazios no documento

- [ ] AC5: Mapeamento de aliases para pessoas reais adicionado como seção no access-matrix.md:
  | Alias | Pessoa | Contato |
  | @oncall-dev | Nome Real | email + telefone |
  - **Evidência:** Todos os aliases usados nos runbooks têm mapeamento

### Runbook de Outage Genérico

- [ ] AC6: `docs/runbooks/general-outage.md` criado com fluxo decisório:
  1. **Verificar:** É o sistema ou é o usuário? (check de device/rede/DNS)
  2. **Classificar:** Backend down / Frontend down / Ambos / Parcial
  3. **Diagnosticar:** Railway logs, Sentry, UptimeRobot (com comandos exatos)
  4. **Agir:** Rollback / Restart / Escalar (com links para runbooks específicos)
  5. **Comunicar:** Template de mensagem para stakeholders
  - **Evidência:** Arquivo commitado com fluxo completo
  - **Aceite:** Uma pessoa que nunca operou o sistema consegue seguir o fluxo apenas com o doc

- [ ] AC7: Seção "Primeiros 5 minutos" com checklist numerado de ações imediatas:
  1. `railway logs --tail` (ou URL do Railway dashboard)
  2. Verificar UptimeRobot status
  3. Verificar Sentry para erros recentes
  4. `curl https://bidiq-backend-production.up.railway.app/health`
  5. Decidir: rollback vs. fix forward
  - **Evidência:** Checklist existe com comandos copy-pasteable

### Runbook de Third-Party Failures

- [ ] AC8: Seção em general-outage.md (ou doc separado) com procedimentos para:
  - **Supabase down:** Sintomas, verificação (`npx supabase status`), impacto (auth + data), mitigação (cache serve stale)
  - **OpenAI down:** Sintomas, verificação, impacto (LLM classification falha), mitigação (fallback REJECT, feature flag `LLM_ARBITER_ENABLED=false`)
  - **Redis down:** Sintomas, verificação, impacto (cache + rate limit + CB state), mitigação (InMemory fallback automático)
  - **Stripe down:** Sintomas, verificação, impacto (billing não funciona), mitigação (grace period 3 dias, plano local funciona)
  - **Evidência:** Cada serviço tem seção com: sintomas, verificação, impacto, mitigação

## Testes de Validação

### T1: Dry-run do runbook de outage
- **Procedimento:** Alguém que NÃO é o autor do runbook lê `general-outage.md` e executa os "Primeiros 5 minutos" em staging
- **Resultado esperado:** Todas as 5 ações são executáveis sem perguntar "como?" ou "onde?"
- **Evidência:** Feedback escrito da pessoa que fez o dry-run

### T2: Access matrix completude
- **Procedimento:** Para cada serviço na matrix, verificar que a URL do console funciona e que as instruções de revogação são válidas
- **Resultado esperado:** 100% dos links funcionam, 100% das instruções são executáveis
- **Evidência:** Checklist verificado

### T3: Contatos funcionais
- **Procedimento:** Para cada contato preenchido, verificar que email é válido (enviar teste)
- **Resultado esperado:** 100% dos emails são entregáveis
- **Evidência:** Confirmação de recebimento

## Métricas de Sucesso

| Métrica | Antes | Depois | Verificação |
|---------|-------|--------|-------------|
| Serviços na access matrix | 0 | 8 | Linhas no documento |
| Operações na RACI matrix | 0 | 6 | Linhas no documento |
| Contatos placeholder | 4 | 0 | Grep "___" em rollback-procedure.md |
| Runbook de outage genérico | 0 | 1 | Arquivo existe |
| Third-party failure procedures | 0 | 4 (Supabase, OpenAI, Redis, Stripe) | Seções no documento |
| Aliases mapeados | 0 | 5+ | Tabela de mapeamento |
| Bus factor | 1 pessoa | 2+ pessoas (doc permite) | Dry-run com 2ª pessoa |

## Rollback

1. **Rollback:** `git revert` do commit. Perde-se apenas a documentação.
2. **Impacto:** Volta ao estado atual (conhecimento tribal, contatos vazios).
3. **Tempo:** < 1 minuto
4. **Nenhuma alteração de código.** Stories são 100% documentação.

## Idempotência

- Documentos são determinísticos. Re-executar produz o mesmo resultado.
- Preencher contatos já preenchidos: sobrescreve com os mesmos dados (idempotente).

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `docs/operations/access-matrix.md` | Criado |
| `docs/runbooks/general-outage.md` | Criado |
| `docs/runbooks/rollback-procedure.md` | Modificado — contatos preenchidos |

## Dependências

| Tipo | Item | Motivo |
|------|------|--------|
| Requisito | Dados de contato reais do time | Preencher contatos |
| Requisito | Inventário de acessos por serviço | Preencher access matrix |
| Paralela | GTM-GO-001 | Runbook referencia alertas que serão ativados em GO-001 |
