# CRIT-SEO-011 — `/blog/stats/cidade/{cidade}` retorna 0 editais para cidades com acento

**Status:** Ready
**Type:** Critical Bug (revenue-adjacent — thin content)
**Priority:** 🔴 P0 — afeta SEO indexability + bounce rate organic traffic
**Owner:** @dev
**Origem:** sessão transient-hellman 2026-04-21, descoberta empírica via Playwright
**Audit Ref:** User flag "me preocupa páginas com valor R$0"

---

## Problema

Página programática `/blog/licitacoes/cidade/sao-paulo` em produção mostra:
- **Editais Abertos: 0**
- **Valor Médio: R$ 0**
- "No momento não identificamos editais ativos para São Paulo nos últimos 10 dias."

Para a **maior economia do Brasil**. Isso é empiricamente falso.

### Smoking gun — 2 endpoints, mesma cidade, dados contraditórios

```bash
# Endpoint A (usado pela página programática blog):
$ curl https://api.smartlic.tech/v1/blog/stats/cidade/sao-paulo
{"cidade":"Sao Paulo","uf":"SP","total_editais":0,"orgaos_frequentes":[],
 "avg_value":0.0,"last_updated":"2026-04-22T00:40:02.682396+00:00"}

# Endpoint B (municipios profile, usado pela rota /municipios/):
$ curl https://api.smartlic.tech/v1/municipios/sao-paulo-sp/profile
{"slug":"sao-paulo-sp","nome":"Sao Paulo","uf":"SP",
 "total_licitacoes_abertas":500,
 "valor_total_licitacoes":396959994.0,
 "licitacoes_recentes":[ ... 5 contratos reais ... ]}
```

**500 editais / R$ 396 milhões vs 0 editais / R$ 0.00** — mesmo município.

### Root Cause (diagnóstico empírico)

`backend/routes/blog_stats.py::get_cidade_stats` (linha 610) tem defeito de normalização:

```python
# Linha 616 — BUG:
cidade_normalized = cidade.lower().replace("-", " ").strip()
# NÃO chama _strip_accents()

# Linha 650-651 — BUG:
item_city = _extract_city(item).lower()
if cidade_normalized in item_city or item_city in cidade_normalized:
    city_results.append(item)
```

Fluxo empírico:
1. Request path: `/v1/blog/stats/cidade/sao-paulo`
2. `cidade_normalized = "sao paulo"` (lower, sem acento — slug não tem acento)
3. DataLake (`pncp_raw_bids`) armazena `orgaoEntidade.municipioNome = "São Paulo"` (com acento — fonte PNCP mantém acento)
4. `item_city = "são paulo"` (com acento)
5. Match `"sao paulo" in "são paulo"` = `False` (ã ≠ a em substring Python)
6. Match `"são paulo" in "sao paulo"` = `False` (mesmo motivo)
7. `city_results = []` → `total_editais: 0, avg_value: 0.0`

### Endpoints Irmãos Que Já Têm o Fix (para referência)

```python
# Linha 688-689 (get_cidade_sector_stats — FIXED):
cidade_normalized = cidade.lower().replace("-", " ").strip()
cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())

# Linha 1070-1071 (get_contratos_cidade_stats — FIXED):
cidade_normalized = cidade.lower().replace("-", " ").strip()
cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())

# Linha 1111-1112 (get_contratos_cidade_setor_stats — FIXED):
cidade_normalized = cidade.lower().replace("-", " ").strip()
cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())
```

Apenas `get_cidade_stats` (linha 610) ficou de fora do fix pattern. Regressão de code review.

---

## Impacto

### SEO (thin content deindex risk)

Páginas `/blog/licitacoes/cidade/[cidade]` afetadas: **todas as cidades com acento no nome** — provavelmente 70%+ das capitais e grandes cidades brasileiras. Lista parcial:
- São Paulo, São Luís, São Gonçalo, São José dos Campos, São Bernardo do Campo
- Brasília
- Goiânia
- Maceió
- Vitória
- Curitiba (çura → cura? checar)
- João Pessoa
- Belém
- Rondônia, Roraima (estados mas pode haver cidades)
- ~1200+ municípios com ã, ç, é, á, etc no nome

Todas essas páginas renderizam "Editais Abertos: 0" + "Valor Médio: R$ 0" + "No momento não identificamos editais ativos" → Googlebot interpreta como thin content → **deindexação** ou **ranking tanking**.

Esse é exatamente o tipo de página que STORY-430 / STORY-439 tentaram evitar via noindex — mas essas páginas NÃO estão com noindex porque o gate depende de `total_editais > 5`, que é 0 artificialmente.

### UX (100% bounce para organic)

Quem chega via Google em "licitações em São Paulo" e vê "não identificamos editais ativos" sai imediatamente. **Bounce rate estimado: 95-100%**.

Conversão organic desse tipo de página: **zero**, enquanto não fixar.

### Memory afetada

Memory `project_sitemap_serialize_isr_pattern.md` (2026-04-21) referenciou que o sitemap shard 4 era onde o problema estava. Mas essas páginas `/blog/licitacoes/cidade/*` ficam em **shard 3** (conforme sitemap index) e estão tecnicamente indexadas no Google — só que com conteúdo falso-zero.

---

## Solução

Replicar o pattern usado nas funções irmãs (linhas 688-689, 1070-1071):

```python
# backend/routes/blog_stats.py, linha 616:
async def get_cidade_stats(cidade: str):
    cidade_normalized = cidade.lower().replace("-", " ").strip()
    cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())  # ADD
    cache_key = f"cidade:{cidade_normalized}"

    cached = _cache_get(cache_key)
    if cached:
        return CidadeStats(**cached)

    # Determine UF for city
    uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)  # CHANGE
    if not uf:
        raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")

    # ... query_datalake ...

    # Filter by city name (linha 649):
    city_results = []
    for item in all_results:
        item_city = _extract_city(item).lower()
        item_city_ascii = _strip_accents(item_city)  # ADD
        if cidade_ascii in item_city_ascii or item_city_ascii in cidade_ascii:  # CHANGE
            city_results.append(item)
```

3 mudanças mínimas: 2 adições + 2 alterações de condição. Pattern já validado nas funções irmãs.

---

## Acceptance Criteria

- [ ] **AC1:** `backend/routes/blog_stats.py::get_cidade_stats` usa `_strip_accents()` + `cidade_ascii` igual às funções irmãs (linhas 683/1065/1106)
- [ ] **AC2:** `curl /v1/blog/stats/cidade/sao-paulo` retorna `total_editais > 0` em produção pós-deploy
- [ ] **AC3:** Sample de 5 cidades com acento retornam dados non-zero:
  - São Paulo / São Luís / Brasília / Goiânia / Maceió
- [ ] **AC4:** Teste unitário em `backend/tests/test_blog_stats.py` valida:
  - Slug "sao-paulo" → match com item_city "São Paulo"
  - Slug "sao-paulo" → match com item_city "sao paulo"
  - Slug "brasilia" → match com item_city "Brasília"
- [ ] **AC5:** Invalidar cache Redis `cidade:*` pós-deploy (cache 6h pode servir valores stale 0):
  ```bash
  railway run --service bidiq-backend 'redis-cli --scan --pattern "cidade:*" | xargs redis-cli DEL'
  ```
- [ ] **AC6:** Verificar via Playwright que `/blog/licitacoes/cidade/sao-paulo` exibe editais/valor reais (não "R$ 0" + "0 editais")

---

## Scope IN

- `backend/routes/blog_stats.py::get_cidade_stats` — fix normalização
- `backend/tests/test_blog_stats.py` — teste regressão

## Scope OUT

- Refatoração de `_extract_city()` — já funciona
- Adição de `_strip_accents` em outras funções — já está OK em irmãs

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Cache Redis 6h serve valor zero pós-deploy | AC5 — flush cache `cidade:*` pós-deploy |
| Regressão em outros endpoints | AC4 — testes unitários |
| Fornecedores podem ter nomes de cidade em outros campos | _extract_city já lida com múltiplos campos |

---

## Priority Rationale (por que é P0)

1. **Revenue-adjacent**: SEO páginas programáticas são o motor de inbound (STORY-324 programmatic pages)
2. **Baixa complexidade** do fix: 3 linhas
3. **Alta severidade** do bug: 70%+ das cidades afetadas
4. **Evidência empírica clara**: 2 endpoints com outputs contraditórios no mesmo dado
5. **SEO hit imediato**: cada dia que passa, Google vê páginas "thin content" e downgrades

---

## Implementação sugerida (código completo)

```python
# backend/routes/blog_stats.py

@router.get("/cidade/{cidade}", response_model=CidadeStats)
async def get_cidade_stats(cidade: str):
    """City stats: count, frequent buying orgs, avg values.

    Public (no auth). Cached 6h.
    Uses the first sector with results to get city data.
    """
    cidade_normalized = cidade.lower().replace("-", " ").strip()
    cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())  # NEW
    cache_key = f"cidade:{cidade_ascii}"  # CHANGED (use ascii for cache key consistency)

    cached = _cache_get(cache_key)
    if cached:
        return CidadeStats(**cached)

    # Determine UF for city
    uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)  # CHANGED
    if not uf:
        raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")

    # Query datalake for this UF without sector keyword filter
    from datalake_query import query_datalake

    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    all_results: list[dict] = []
    try:
        all_results = await query_datalake(
            ufs=[uf],
            data_inicial=data_inicial,
            data_final=data_final,
            keywords=None,
            limit=2000,
        )
    except Exception as e:
        logger.debug("Datalake query failed for cidade=%s uf=%s: %s", cidade, uf, e)

    # Filter by city name in orgaoEntidade.municipioNome — accent-insensitive
    city_results = []
    for item in all_results:
        item_city = _extract_city(item).lower()
        item_city_ascii = _strip_accents(item_city)  # NEW
        if cidade_ascii in item_city_ascii or item_city_ascii in cidade_ascii:  # CHANGED
            city_results.append(item)

    # ... resto do código idêntico ...
```

---

## Definition of Done

- `/blog/licitacoes/cidade/sao-paulo` mostra editais/valor reais em produção
- `curl /v1/blog/stats/cidade/sao-paulo` retorna `total_editais > 400` (similar ao `/v1/municipios/sao-paulo-sp/profile`)
- Cache Redis flush efetuado (AC5)
- 5 cidades sample validadas via Playwright — todas non-zero
