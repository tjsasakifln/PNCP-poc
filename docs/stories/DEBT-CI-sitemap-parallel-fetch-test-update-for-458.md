# DEBT-CI — sitemap-parallel-fetch test update para PR #458

**Status:** Ready
**Type:** Debt (CI fix, coupled to #458)
**Priority:** P0 — bloqueia merge de #458 (revenue lever crítico)
**Owner:** @devops
**Origem:** sessão transient-hellman 2026-04-21
**Depende de:** #458 (sitemap serialize + ISR) ou decisão de usuário sobre push em pre-existing branch

---

## Problema

`frontend/__tests__/app/sitemap-parallel-fetch.test.ts:143` asserta explicitamente comportamento `Promise.all`:

```typescript
// Linha 143 do arquivo atual em main:
expect(initiated.length).toBe(6);
```

Quando PR #458 (`fix(seo-001): serialize sitemap/4.xml backend fetches`) for mergeado, o código em `frontend/app/sitemap.ts` muda de `Promise.all([...])` para 6 `await` sequenciais. Com a mudança:

- **Esperado após serialize:** `initiated.length === 1` (apenas o primeiro fetch em voo até seu gate resolver)
- **Assertion atual:** `initiated.length === 6`
- **Resultado em CI:** Backend Tests falha → required check falha → PR #458 não merga sem fix deste teste.

## Solução

Atualizar o teste para validar a nova semântica (serialização), seguindo o mesmo padrão robust que já existe em `sitemap-coverage.test.ts`:

1. Docstring: "Promise.all" → "serialized awaits" (context histórico preservado)
2. Assertion principal: verificação step-by-step com gates por endpoint (garante que o próximo só inicia após o anterior completar)
3. Novo teste: asserta `export const revalidate = 3600` (ISR 1h que acompanha a serialização)

## Context histórico

- HTTP 524 (timeout) → adotou-se `Promise.all` (commit antigo)
- `Promise.all` sob múltiplos crawlers → backend saturava → shard 4 vazio em produção
- Fix em #458: serialize + ISR `revalidate=3600` (amortiza sobre N crawler-hits)

A serialização é segura porque ISR regenera 1x/hora por shard, independente da frequência de crawler hits — cost único por shard-hour vs cost por crawler-hit-paralelo.

## Patch completo (aplicar quando permissão de push em #458 for concedida)

```diff
diff --git a/frontend/__tests__/app/sitemap-parallel-fetch.test.ts b/frontend/__tests__/app/sitemap-parallel-fetch.test.ts
--- a/frontend/__tests__/app/sitemap-parallel-fetch.test.ts
+++ b/frontend/__tests__/app/sitemap-parallel-fetch.test.ts
@@ -1,17 +1,19 @@
 /**
  * @jest-environment node
  *
- * Regression test for HTTP 524 sitemap timeout fix.
+ * Regression test for sitemap/4.xml empty shard bug (STORY-SEO-001).
  *
- * Bug: sitemap() chamava endpoints do backend sequencialmente, somando latência →
- * Railway/Cloudflare retornava HTTP 524.
+ * Historical note: Promise.all() foi introduzido para corrigir HTTP 524 (timeout),
+ * mas sob múltiplos crawlers simultâneos saturava o backend (todos os 6 fetches
+ * paralelos timeoutavam → shard 4 vazio em produção).
  *
- * Fix: Promise.all() paraleliza as chamadas; AbortSignal.timeout(15000) limita cada
- * fetch a 15s individualmente.
+ * Fix atual (PR #458): Serializar os 6 await + ISR revalidate=3600 (1h).
+ * Cada fetch ainda tem AbortSignal.timeout(15000) como guardrail individual.
+ * ISR amortiza o custo sobre N crawler-hits (1 regeneração/hora cobre todos).
  *
  * Com o Sitemap Index (SEO-460), os endpoints ficam distribuídos por sub-sitemap:
  *  - id:2 → /v1/sitemap/licitacoes-indexable (1 endpoint)
- *  - id:4 → 6 endpoints de entidades em Promise.all
+ *  - id:4 → 6 endpoints de entidades sequenciais
  */

 // Mock fetch globally (node env pattern — see __tests__/api/buscar.test.ts)
@@ -76,7 +78,7 @@ function makeFastFetchMock() {
   );
 }

-describe('sitemap() — parallel fetch regression (HTTP 524 fix)', () => {
+describe('sitemap() — serialized fetches regression (STORY-SEO-001)', () => {
   beforeEach(() => {
     (global.fetch as jest.Mock).mockReset();
   });
@@ -110,12 +112,10 @@ describe('sitemap() — parallel fetch regression (HTTP 524 fix)', () => {
     }
   });

-  it('sub-sitemap id:4 inicia todos os 6 fetches antes de qualquer resposta resolver (Promise.all)', async () => {
+  it('sub-sitemap id:4 serializa os 6 fetches — apenas 1 em voo por vez (STORY-SEO-001 PR #458)', async () => {
     const initiated: string[] = [];
-    let releaseAll!: () => void;
-    const gate = new Promise<void>((res) => {
-      releaseAll = res;
-    });
+    const completed: string[] = [];
+    const gates: Array<() => void> = [];

     (global.fetch as jest.Mock).mockImplementation(
       (url: string | URL | Request) => {
@@ -123,10 +123,15 @@ describe('sitemap() — parallel fetch regression (HTTP 524 fix)', () => {
         const endpoint = ENTITY_ENDPOINTS.find((e) => urlStr.includes(e));
         if (endpoint) {
           initiated.push(endpoint);
-          return gate.then(() => ({
-            ok: true,
-            json: () => Promise.resolve(PAYLOAD_BY_ENDPOINT[endpoint]),
-          })) as Promise<Response>;
+          return new Promise<Response>((resolve) => {
+            gates.push(() => {
+              completed.push(endpoint);
+              resolve({
+                ok: true,
+                json: () => Promise.resolve(PAYLOAD_BY_ENDPOINT[endpoint]),
+              } as Response);
+            });
+          });
         }
         return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
       },
@@ -135,14 +140,28 @@ describe('sitemap() — parallel fetch regression (HTTP 524 fix)', () => {
     const sitemap = await importSitemapFresh();
     const sitemapPromise = sitemap({ id: 4 });

-    // Flush microtasks para que Promise.all dispare todos os fetches
+    // Flush microtasks até o primeiro fetch iniciar
     for (let i = 0; i < 20; i++) await Promise.resolve();

-    // Com Promise.all: todos os 6 devem estar em voo antes de qualquer resposta resolver
-    // Com sequential awaits (bug original): apenas 1 teria sido iniciado
-    expect(initiated.length).toBe(6);
+    // Com serialized awaits: apenas o primeiro endpoint terá iniciado até liberarmos o gate
+    expect(initiated.length).toBe(1);
+    expect(completed.length).toBe(0);
+
+    // Resolve cada fetch em sequência e verifica que o próximo só inicia após o anterior completar
+    for (let step = 0; step < 6; step++) {
+      expect(initiated.length).toBe(step + 1);
+      gates[step]();
+      // Flush microtasks para o await liberar e o próximo fetch iniciar
+      for (let i = 0; i < 20; i++) await Promise.resolve();
+    }

-    releaseAll();
     await sitemapPromise;
+    expect(completed.length).toBe(6);
+  });
+
+  it('sitemap.ts exporta revalidate = 3600 para ISR de 1h (PR #458)', async () => {
+    jest.resetModules();
+    const mod = await import('../../app/sitemap');
+    expect((mod as { revalidate?: number }).revalidate).toBe(3600);
   });
 });
```

## Como aplicar

### Opção A — push direto em #458 (preferred)
```bash
gh pr checkout 458
# Aplicar o patch acima (copiar conteúdo para pasta temp, git apply):
cat << 'PATCH' > /tmp/fix.patch
<copiar o diff acima>
PATCH
git apply /tmp/fix.patch
git add frontend/__tests__/app/sitemap-parallel-fetch.test.ts
git commit -m "test(seo-001): update sitemap-parallel-fetch for PR #458 serialize"
git push origin fix/sitemap-shard-4-serialize-backend-fetches
```
**Bloqueio atual:** sistema denies push em branches pre-existing que o agente não criou. Requer ou:
- Permissão explícita do usuário nas settings
- Intervenção humana via `gh pr checkout 458 + apply patch + push`

### Opção B — fix-up PR pós-merge de #458
1. Merge #458 (Backend Tests falha, mas pode forçar merge com bypass admin)
2. Criar PR `fix(test): sitemap-parallel-fetch for serialization` em branch nova
3. Merge imediato
**Custo:** main fica brevemente vermelho (required check failing em main).

### Opção C — close #458 + abrir novo PR com código + teste juntos
Desperdiça o CI time já investido, mas é o mais limpo.

## Acceptance Criteria

- [ ] AC1: Patch aplicado em #458 ou nova PR
- [ ] AC2: `npm test -- sitemap-parallel-fetch` passa verde (3 cenários)
- [ ] AC3: Required checks Backend Tests + Frontend Tests verdes em #458
- [ ] AC4: #458 merged em main

## Definição de Pronto

- Main tem sitemap.ts serializado + revalidate=3600 + test atualizado passando
- `curl sitemap/4.xml | grep -c '<url>'` em produção >= 5000
