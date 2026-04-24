# Story SEO-014: Verify + Redeploy Sitemap RPCs em Produção

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🟠 P1
**Story Points:** 2 SP
**Owner:** @data-engineer (Dara)
**Status:** Ready
**Depends on:** SEO-013 (backend responsivo para validar)

---

## Problem

Os handlers de sitemap backend (`backend/routes/sitemap_cnpjs.py`, `sitemap_orgaos.py`) usam RPCs `get_sitemap_cnpjs_json`, `get_sitemap_orgaos_json` para bypassar o limit PostgREST max-rows=1000 e retornar lista completa em 1 call. Migration `supabase/migrations/20260408200000_sitemap_rpc_json.sql` cria essas funções.

**Fallback** (quando RPC não existe ou erra): paginated query `.table("pncp_raw_bids").range(offset, offset+1000)` em loop — scan 1.5M rows, timeout certo sob carga.

**Hipótese não verificada:** RPCs podem não estar deployed em prod (migration não aplicada ou dropada), forçando sempre o fallback lento mesmo após SEO-013 fixar o índice.

### Evidência a coletar

```sql
-- Expected presença:
SELECT proname FROM pg_proc WHERE proname LIKE 'get_sitemap%';
--
-- get_sitemap_cnpjs_json
-- get_sitemap_orgaos_json
-- get_sitemap_fornecedores_cnpj_json (se aplicável)
```

Se resultado vazio OU subset → RPC não deployed → migration não aplicada → aplicar.

---

## Acceptance Criteria

- [ ] **AC1** — Executar `SELECT proname, prosrc, pronargs FROM pg_proc WHERE proname LIKE '%sitemap%'` em prod Supabase e documentar resultado no story (comentário ou seção abaixo).
- [ ] **AC2** — Se `get_sitemap_cnpjs_json` ausente: rodar `npx supabase db push --include-all` para aplicar migration `20260408200000_sitemap_rpc_json.sql`. Se já aplicada mas RPC ausente: re-criar via psql direto.
- [ ] **AC3** — Validar que RPC retorna dados:
  ```sql
  SELECT jsonb_array_length(get_sitemap_cnpjs_json(5000)) AS count;
  -- count >= 1000 (baseline ~4-5k CNPJs esperado per SEO-PLAYBOOK Onda 1)
  ```
- [ ] **AC4** — `curl https://api.smartlic.tech/v1/sitemap/cnpjs` retorna JSON com `total >= 1000` em <3s. Log backend deve mostrar `sitemap_cnpjs (JSON RPC): N buyers + 11 seed suppliers = N+11 total` (não `paginated`).
- [ ] **AC5** — Mesma validação para demais RPCs sitemap existentes (orgaos, fornecedores-cnpj se tiver RPC correspondente). Documentar resultados.
- [ ] **AC6** — Se algum endpoint NÃO tiver RPC equivalente e usa paginated query: criar issue/story separada para adicionar RPC (scope out desta story, mas reportar).
- [ ] **AC7** — `sitemap/4.xml` após ISR revalidation (1h) deve conter `total >= 5000 <loc>` tags. Comprovar: `sleep 3700 && curl -sL https://smartlic.tech/sitemap/4.xml | grep -c '<loc>'`.

---

## Scope IN

- Verificação de presença dos RPCs em prod
- Re-aplicação de migration se faltando
- Validação de latência + contagem
- Trigger de ISR revalidation (pode ser via `revalidatePath` no frontend ou aguardar TTL)

## Scope OUT

- Criação de RPCs novos (se faltarem, issue separada)
- Modificar contratos dos endpoints
- Tuning do RPC (só valida funcionalidade)

---

## Implementation Notes

### Passo 1: verificar presença

```bash
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN /mnt/d/pncp-poc/.env | cut -d'=' -f2)
# OU usar psql direto:
psql "$SUPABASE_DB_URL" <<'SQL'
SELECT
  proname,
  pronargs,
  pg_get_function_arguments(oid) AS args
FROM pg_proc
WHERE proname LIKE '%sitemap%'
ORDER BY proname;
SQL
```

### Passo 2: aplicar se faltando

```bash
cd /mnt/d/pncp-poc
npx supabase db push --include-all
# Se bloqueado por outras migrations pendentes:
psql "$SUPABASE_DB_URL" -f supabase/migrations/20260408200000_sitemap_rpc_json.sql
```

### Passo 3: smoke test

```bash
psql "$SUPABASE_DB_URL" -c "SELECT jsonb_array_length(get_sitemap_cnpjs_json(5000));"
# > 1000 esperado

curl -s https://api.smartlic.tech/v1/sitemap/cnpjs | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'cnpjs total: {d[\"total\"]}, first: {d[\"cnpjs\"][:3]}')
"
# Logs backend (via railway logs):
# [INFO] sitemap_cnpjs (JSON RPC): N buyers + 11 seed suppliers = N+11 total
```

### Passo 4: forçar revalidation sitemap/4.xml

```bash
# ISR TTL é 3600s (frontend/app/sitemap.ts:201). Opções:
# A) Aguardar TTL natural (1h)
# B) Redeploy frontend para bust cache imediato
# C) Chamar endpoint custom revalidate (se existir; verificar frontend/app/api/revalidate)
```

### Verificações finais

```bash
# Total de URLs sitemap
for i in 0 1 2 3 4; do
  count=$(curl -sL "https://smartlic.tech/sitemap/$i.xml" | grep -c '<loc>')
  echo "sitemap/$i.xml: $count URLs"
done
# Esperado: sitemap/4.xml >= 5000 (vs 0 baseline)
```

---

## Dependencies

- **Pre:** SEO-013 (sem índice, validação de latência via curl vai continuar timing out mesmo com RPC OK)
- **Unlocks:** Monitor real de SEO-015 (CDN cache só faz sentido com backend entregando dados)

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada. Hipótese de RPC ausente baseada em advisor alignment; verificação pendente em AC1. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 9/10 → GO. Status Draft → Ready. Gap minor: risks sem seção dedicada — aceitável dado escopo reduzido (2 SP). Pode proceder após SEO-013. |
