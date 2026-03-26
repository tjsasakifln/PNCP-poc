# /check-gtm — GTM Production Verification

**Squad:** `squad-check-gtm`
**Mode:** Verification (read-only, nunca modifica código)

## Activation

```
/check-gtm
```

## What This Does

Verifica o GTM Production Checklist item a item contra produção (`https://smartlic.tech`), marcando cada item como PASS ou FAIL. Ao encontrar o **primeiro FAIL**, a verificação é **interrompida** e o foco muda para **diagnóstico de causa raiz** com nível de detalhe suficiente para um dev corrigir o problema definitivamente.

**3 checklists verificados em ordem:**
1. **Go/No-Go** (26 itens) — P0 Blockers → P1 Critical → P2 Important
2. **Security & Compliance** (43 itens) — Auth, Data, Input, Deps, Secrets, LGPD
3. **UX Production** (53 itens) — Search Flow, Progress, Errors, Onboarding, Nav, Visual, A11y, Mobile

**Total: 122 itens**

## Execution Protocol

Quando o usuário invoca `/check-gtm`, execute este protocolo:

### Phase 1: Load State

1. Ler `docs/gtm-checks/check-gtm-state.md` (se existir) para determinar onde parou a última execução
2. Ler os 3 checklists:
   - `squads/gtm-readiness-squad/checklists/go-nogo-checklist.md`
   - `squads/gtm-readiness-squad/checklists/security-compliance-checklist.md`
   - `squads/gtm-readiness-squad/checklists/ux-production-checklist.md`
3. Identificar o **próximo item não verificado** (itens marcados `[x]` são pulados)

### Phase 2: Sequential Verification (stop-on-fail)

Para cada item não verificado, **na ordem dos checklists**:

1. **Determinar método de verificação** adequado ao item:

   | Tipo de Item | Método | Ferramenta |
   |-------------|--------|------------|
   | UI/UX funcional | Browser | Playwright MCP — navegar, clicar, verificar |
   | API endpoint | HTTP request | `curl` ou `fetch` via Bash |
   | Código/implementação | Code inspection | Grep + Read nos arquivos relevantes |
   | Infra/config | CLI check | Railway CLI, Supabase CLI, headers check |
   | Security | Multi-method | Headers + código + deps audit |

2. **Executar verificação** com evidência concreta:
   - Para browser: navegar em `https://smartlic.tech`, tomar screenshot se relevante
   - Para API: fazer request real e verificar response
   - Para código: localizar implementação e confirmar que existe e está correta
   - Para infra: verificar configuração via CLI

3. **Registrar resultado:**

   ```markdown
   ### [LABEL] — PASS ✅
   **Método:** {método usado}
   **Evidência:** {o que foi verificado e resultado}
   ```

4. **Se PASS:** marcar `[x]` no checklist, atualizar state, avançar para próximo item
5. **Se FAIL:** INTERROMPER verificação, ir para Phase 3

### Phase 3: Root Cause Diagnosis (apenas no FAIL)

Quando um item falha, executar diagnóstico profundo:

1. **Documentar sintoma** — o que foi observado em produção (resposta da API, comportamento do browser, erro no console)

2. **Investigar causa raiz** usando múltiplas fontes:
   - Inspecionar código-fonte relevante (Grep + Read)
   - Verificar configuração de infra (env vars, Railway, Supabase)
   - Analisar logs se acessíveis (Railway logs)
   - Verificar dependências e versões
   - Cruzar com git log para mudanças recentes

3. **Produzir diagnóstico estruturado:**

   ```markdown
   ## 🔴 FALHA: [ITEM_LABEL] — [ITEM_DESCRIPTION]

   ### Sintoma Observado
   {Descrição precisa do que ocorre em produção}

   ### Causa Raiz
   {Explicação técnica da causa — não sintomas, mas a RAIZ}

   ### Localização no Código
   | Arquivo | Linha(s) | Problema |
   |---------|----------|----------|
   | {path}  | {lines}  | {issue}  |

   ### Contexto Arquitetural
   {Fluxo de dados, dependências, por que isso acontece}

   ### Fix Spec
   **Complexidade:** {Trivial | Simples | Moderada | Complexa}
   **Arquivos a alterar:**
   1. `{file}` — {o que mudar}

   **Lógica esperada:**
   {Pseudocódigo ou código real do fix}

   **Testes a adicionar:**
   1. `{test_file}` — {cenário}

   **Riscos/Side-effects:**
   - {risco 1}
   ```

### Phase 4: Save State

1. Atualizar o checklist com `[x]` nos itens PASS
2. Salvar estado em `docs/gtm-checks/check-gtm-state.md`:
   ```markdown
   # GTM Check State
   **Last run:** {ISO timestamp}
   **Checklist:** {qual checklist atual}
   **Last passed item:** {LABEL do último PASS}
   **Next item:** {LABEL do próximo a verificar}
   **Total:** {N}/{122} PASS, {M} FAIL
   **Status:** {in-progress|blocked-on-fix|complete}
   ```
3. Apresentar resumo ao usuário

## Output Format

### Durante verificação (itens passando):

```
## GTM Check — Verificação em Andamento

### Go/No-Go Checklist

| # | Item | Status | Método |
|---|------|--------|--------|
| 1 | AUTH | ✅ PASS | API — JWT ES256 validado |
| 2 | CSP  | ✅ PASS | Browser — frontend↔API OK |
| 3 | PLANS | ❌ FAIL | Browser — preço incorreto |

⏸️ Verificação interrompida no item 3/122. Iniciando diagnóstico...
```

### Após diagnóstico (item com falha):

O diagnóstico completo no formato da Phase 3 acima.

### Se todos passam:

```
## GTM Check — ✅ COMPLETE

122/122 itens verificados. Todos PASS.

**Verdict: GO** 🚀
```

## Resumption

Cada invocação de `/check-gtm` retoma de onde parou:
- Itens `[x]` são pulados
- Se o último run parou em FAIL e o fix foi aplicado, a verificação continua do item que falhou
- Para **resetar** e re-verificar tudo: deletar `docs/gtm-checks/check-gtm-state.md` e desmarcar `[x]` nos checklists

## Important Notes

- **Nunca modifica código** — apenas lê e diagnostica
- **Sempre verifica em produção** (`https://smartlic.tech`), não localhost
- **Credenciais de teste:** `tiago.sasaki@gmail.com` com senha de `SEED_ADMIN_PASSWORD`
- **Playwright MCP** para verificações de browser
- **Stop-on-first-fail** é intencional — corrigir um item de cada vez evita regressões cascata
- **O diagnóstico é o entregável principal** — deve ter detalhe suficiente para um `@dev` corrigir sem investigação adicional
