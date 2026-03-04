# STORY-COPY-373: Substituir "24h atualização diária" por claim verificável no InstitutionalSidebar

**Prioridade:** P1 (conversão — sidebar é visto por 100% dos visitantes de login/signup)
**Escopo:** `frontend/app/components/InstitutionalSidebar.tsx`, `frontend/__tests__/components/InstitutionalSidebar.test.tsx`
**Estimativa:** XS
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

O stat "24h — atualização diária" é enganoso: SmartLic faz buscas on-demand + digests diários, não monitoramento 24h contínuo.

- **Cluster 1 (Hopkins):** Claims verificáveis convertem; claims vagos criam ceticismo.
- **Cluster 3 (Laja):** Substituir por stat que o usuário pode verificar imediatamente.
- **Cluster 5 (Cialdini):** "Fontes oficiais" ativa heurística de autoridade em público B2G.

## Critérios de Aceitação

- [ ] AC1: `InstitutionalSidebar.tsx:157` — `{ value: "24h", label: "atualização diária" }` → `{ value: "3", label: "fontes oficiais integradas" }`
- [ ] AC2: Teste atualizado
- [ ] AC3: Nenhuma outra referência a "24h atualização" em texto user-facing

## Copy Recomendada

```typescript
{ value: "3", label: "fontes oficiais integradas" }
```

## Princípios Aplicados

- **Hopkins (Direct Response):** Claim específico e verificável sempre vence claim vago
- **Cialdini (Psicologia):** Autoridade — "fontes oficiais" ativa heurística de credibilidade em público B2G

## Evidência

- Atual: `InstitutionalSidebar.tsx:157` — "24h atualização diária"
- Auditoria: Flagged como "misleading — implies 24h automation"
