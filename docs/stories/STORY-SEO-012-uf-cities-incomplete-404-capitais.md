# STORY-SEO-012 — `UF_CITIES` incompleto: 11 capitais brasileiras retornam 404 em `/blog/stats/cidade/*`

**Status:** InReview
**Type:** Critical Bug (revenue-adjacent — thin content / deindex risk)
**Priority:** 🔴 P0 — mesmo vetor SEO do CRIT-SEO-011, escala comparable
**Owner:** @dev
**Origem:** sessão snappy-treehouse 2026-04-24, descoberta via smoke test AC3 de CRIT-SEO-011
**Dependency:** none (CRIT-SEO-011 já Done; este é follow-up independente)
**Complexity:** S (single file, dict literal expansion, ~140 entries)

---

## Problema

`backend/routes/blog_stats.py:49-66` define `UF_CITIES` como dict hardcoded mapeando UF → lista de cidades reconhecidas. O dict cobre apenas **16 de 27 UFs** brasileiras. Resultado: `/v1/blog/stats/cidade/{slug}` retorna **404 "Cidade não encontrada"** para qualquer cidade de uma UF faltante — incluindo **11 capitais estaduais**.

### UFs faltantes no dict

```python
# backend/routes/blog_stats.py:49-66 (UF_CITIES atual)
UF_CITIES: dict[str, list[str]] = {
    "SP": [...], "RJ": [...], "MG": [...], "DF": [...], "PR": [...],
    "BA": [...], "RS": [...], "GO": [...], "PE": [...], "SC": [...],
    "CE": [...], "PA": [...], "AM": [...], "MA": [...], "ES": [...],
    "RN": ["Mossoró"],  # UF presente mas SEM capital Natal!
}

# UFs FALTANDO (11):
# AL, PB, SE, PI, AC, RO, RR, AP, TO, MT, MS
#
# Também: RN presente mas só com Mossoró — falta Natal (capital!)
```

### Capitais que hoje retornam 404

| UF | Capital | Slug 404 |
|----|---------|----------|
| AL | Maceió | `/blog/stats/cidade/maceio` |
| PB | João Pessoa | `/blog/stats/cidade/joao-pessoa` |
| SE | Aracaju | `/blog/stats/cidade/aracaju` |
| PI | Teresina | `/blog/stats/cidade/teresina` |
| AC | Rio Branco | `/blog/stats/cidade/rio-branco` |
| RO | Porto Velho | `/blog/stats/cidade/porto-velho` |
| RR | Boa Vista | `/blog/stats/cidade/boa-vista` |
| AP | Macapá | `/blog/stats/cidade/macapa` |
| TO | Palmas | `/blog/stats/cidade/palmas` |
| MT | Cuiabá | `/blog/stats/cidade/cuiaba` |
| MS | Campo Grande | `/blog/stats/cidade/campo-grande` |
| **RN** | **Natal** | `/blog/stats/cidade/natal` (UF presente, capital não) |

**12 capitais** no total (11 UFs faltantes + Natal em RN parcialmente presente).

### Smoking gun

```bash
$ curl https://api.smartlic.tech/v1/blog/stats/cidade/maceio
{"detail":"Cidade 'maceio' não encontrada"}  # HTTP 404

# Comparação — capitais presentes no dict retornam OK:
$ curl https://api.smartlic.tech/v1/blog/stats/cidade/salvador
{"cidade":"Salvador","uf":"BA","total_editais":348,...}  # HTTP 200
```

### Root cause

Linha 628 (e duplicatas em 702, 1083, 1124):

```python
uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)
if not uf:
    raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")
```

`_CITY_TO_UF` é construído em linhas 81-86 a partir de `UF_CITIES`. Se UF não está listada OU cidade não está na lista daquela UF, lookup falha → 404.

Não é bug de normalização (acento já corrigido em CRIT-SEO-011) — é **allowlist estática incompleta**. Curadoria parcial na criação original do dict.

---

## Impacto

### SEO — thin content / deindex risk (idêntico a CRIT-SEO-011)

Páginas programáticas `/blog/licitacoes/cidade/{slug}` afetadas por UFs faltantes:

- **12 capitais estaduais** renderizam como thin content ou 404 na camada frontend
- **Cidades interioranas** dessas 11 UFs também afetadas (fallback não existe — dict é literal)
- Estimativa ~800-1500 cidades não-reconhecidas no total (IBGE: 5570 municípios, Brasil)

Googlebot → 404 = remove da index. Googlebot → "cidade não encontrada" em HTML = thin content → deindex.

Páginas que **JÁ ESTÃO indexadas** (se sitemap inclui essas cidades): risco imediato de downgrade ranking. Páginas que **NÃO ESTÃO indexadas**: oportunidade SEO perdida.

### Funil B2G organic

Pergunta: "licitações em Maceió" no Google. SmartLic é invisível (404 ou thin content). Concorrentes ranqueiam. Perda de leads inbound qualificados.

### Relação com CRIT-SEO-011

Mesmo endpoint, mesmo vetor de risco SEO, causa diferente:
- CRIT-SEO-011: match falha por acento mismatch (retornava 200 + 0 editais)
- STORY-SEO-012: lookup falha por dict incompleto (retorna 404 direto)

---

## Solução

Expandir `UF_CITIES` em `backend/routes/blog_stats.py:49-66` para cobrir **27 UFs** com:

1. **Capital de cada UF** (27 capitais total)
2. **Top 5-10 cidades por UF** por relevância econômica/demográfica (IBGE população + PIB)

Total estimado: **~110-140 cidades** curadas (vs ~90 atuais).

### Fontes para curadoria

- IBGE Cidades — lista oficial de municípios por UF
- População estimada — ordenar top N
- PIB municipal — ajuste para cidades com atividade econômica relevante (algumas não-capitais grandes: Sorocaba/SP, Canoas/RS, Campos dos Goytacazes/RJ etc — já parcialmente cobertas)

### Código (estrutura)

```python
# backend/routes/blog_stats.py:49-76 (expandido)
UF_CITIES: dict[str, list[str]] = {
    "AC": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira"],
    "AL": ["Maceió", "Arapiraca", "Palmeira dos Índios"],
    "AM": ["Manaus", "Parintins", "Itacoatiara", "Manacapuru"],
    "AP": ["Macapá", "Santana", "Laranjal do Jari"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Juazeiro", "Ilhéus", "Itabuna"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral"],
    "DF": ["Brasília"],
    "ES": ["Vitória", "Vila Velha", "Serra", "Cariacica", "Cachoeiro de Itapemirim"],
    "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Águas Lindas de Goiás"],
    "MA": ["São Luís", "Imperatriz", "Timon", "Caxias"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Ribeirão das Neves"],
    "MS": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá"],
    "MT": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá", "Castanhal"],
    "PB": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos"],
    "PE": ["Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina"],
    "PI": ["Teresina", "Parnaíba", "Picos", "Floriano"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Cascavel", "Ponta Grossa", "São José dos Pinhais", "Foz do Iguaçu"],
    "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias", "Nova Iguaçu", "São Gonçalo", "Belford Roxo", "São João de Meriti", "Campos dos Goytacazes", "Petrópolis"],
    "RN": ["Natal", "Mossoró", "Parnamirim", "São Gonçalo do Amarante"],
    "RO": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Vilhena"],
    "RR": ["Boa Vista", "Rorainópolis"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria", "Viamão", "Novo Hamburgo"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "São José", "Chapecó", "Criciúma"],
    "SE": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto", "Itabaiana"],
    "SP": ["São Paulo", "Campinas", "Guarulhos", "São Bernardo do Campo", "Osasco", "Santo André", "Mauá", "Mogi das Cruzes", "Diadema", "Sorocaba", "Ribeirão Preto", "São José dos Campos"],
    "TO": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional"],
}
```

27 UFs, ~140 cidades. Números exatos a curar em implementação.

---

## Acceptance Criteria

- [x] **AC1:** `backend/routes/blog_stats.py:UF_CITIES` cobre as 27 UFs brasileiras (sigla + capital + ≥2 cidades secundárias)
- [x] **AC2:** `curl /v1/blog/stats/cidade/{slug-capital}` retorna HTTP 200 (não 404) para todas as 27 capitais:
  ```bash
  for slug in maceio joao-pessoa aracaju teresina rio-branco porto-velho boa-vista macapa palmas cuiaba campo-grande natal; do
    curl -s -o /dev/null -w "$slug: %{http_code}\n" https://api.smartlic.tech/v1/blog/stats/cidade/$slug
  done
  # Esperado: todas retornam 200
  ```
- [x] **AC3:** Testes unitários em `backend/tests/test_blog_stats.py` adicionam:
  - `test_all_27_state_capitals_return_200` — parametrized com todas capitais
  - `test_uf_cities_dict_has_27_entries` — validação estrutural
  - `test_cidade_stats_newly_added_capitals_work` — sample com ≥5 capitais novas
- [x] **AC4:** ~~Cache Redis~~ Cache InMemory `_blog_cache` (linhas 31-33) verificar — `_cache_get/_cache_set` apenas armazena successful responses (linha 679 cache após sucesso); 404 raise antes de cache. **SKIP flush** — não cacheia errors. Documentar em Dev Notes.
- [x] **AC5:** Sitemap shard de cidades regenera (se pipeline SEO materializa páginas por cidade, inclui novas UFs) — verificar `frontend/app/sitemap*.xml.ts` ou equivalente
- [ ] **AC6 (smoke prod, pendente devops merge):** Smoke test 12 capitais faltantes via `curl` produção pós-deploy — todas HTTP 200 com `total_editais ≥ 0` (pode ser 0 se cidade não tem dados recentes, mas não 404)

---

## Scope IN

- `backend/routes/blog_stats.py:UF_CITIES` — expansão do dict para 27 UFs
- `backend/tests/test_blog_stats.py` — testes regressão + cobertura 27 capitais
- Possível: `frontend/app/sitemap*.xml.ts` se sitemap estático por cidade

## Scope OUT

- Extensão para **todos** os ~5570 municípios IBGE (too much, diminishing return)
- Normalização de slugs (já tratada em CRIT-SEO-011)
- Refatoração de `_extract_city()` (funciona)
- Mudança de arquitetura de allowlist para lookup dinâmico em DB (story própria se for necessária depois)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Cache Redis serve 404 cached | AC4 — verificar e flush se aplicável |
| Cidades novas têm 0 editais em período curto | Aceitável — 200 + 0 é melhor que 404 (permite ISR cache gap + rebuild futura) |
| UF_CITIES duplicata entre acentos quebra (já tratada em linhas 81-86) | `_strip_accents` já aplicado em build do `_CITY_TO_UF` — safe |
| Expansão causa memory bloat | Desprezível — ~140 strings ≈ <10KB |

---

## Priority Rationale (por que é P0)

1. **Mesmo vetor de impacto do CRIT-SEO-011** — risco de deindex para capitais de 11 UFs
2. **Baixa complexidade** — único arquivo modificado (`blog_stats.py`), delta é edição de literal dict
3. **Alta cobertura** — uma única mudança corrige 12+ capitais simultaneamente
4. **Oportunidade revenue**: capitais são high-intent search queries ("licitações em Maceió") — traffic organic imediatamente monetizável
5. **Consistência com produto** — SmartLic vende "cobertura nacional" mas 11 UFs são literalmente invisíveis para queries por cidade

---

## Definition of Done

- 27 capitais brasileiras retornam HTTP 200 em `/v1/blog/stats/cidade/{slug-capital}`
- Testes unitários parametrizados cobrem todas as 27 UFs
- Sitemap SEO regenerado (se aplicável)
- Smoke test produção pós-deploy: 12 capitais antes-404 agora retornam dados
- Zero regressão em cidades já funcionais

---

## Notes

- Curadoria de cidades secundárias deve usar IBGE como fonte canônica — evita discussão sobre qual cidade incluir. Critério: população + PIB municipal (cut-off top 5-10 por UF).
- Se esse padrão de allowlist virar gargalo (novas cidades batendo 404 no futuro), epic follow-up pode migrar para lookup dinâmico contra tabela `municipios` no DB.

---

## Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-04-24 | @sm (snappy-treehouse) | Story criada Draft |
| 2026-04-24 | @po (frolicking-glacier) | Validação 10-pt: GO (8/10 hard + 2 minor). Status `Draft → Ready`. AC4 atualizada (cache é InMemory, não Redis; 404 não cacheado → SKIP flush). Complexity field adicionado: S. |
| 2026-04-24 | @dev (frolicking-glacier) | Implementado: UF_CITIES expandido 16→27 UFs (~140 cidades). Frontend mirror `frontend/lib/cities.ts` sincronizado. 41 unit tests adicionados em test_blog_stats.py (TestStorySEO012CapitalsExpansion). 104 regression tests passing. Status `Ready → InReview`. AC1-AC5 done; AC6 (smoke prod) pendente devops merge. |

---

## Dev Agent Record

### Implementation summary

| Item | Status |
|------|--------|
| Backend `UF_CITIES` expansion | ✅ 27 UFs, ~140 cidades curadas (capital + top 5-10 por UF, IBGE-based) |
| Frontend `cities.ts` mirror | ✅ Sincronizado (mesmo conteúdo) |
| Tests parametrizados | ✅ 41 tests novos: structural (1) + 27 capitais (parametrize) + 12 previously-404 (parametrize) + sanity (1) |
| Full-file regression | ✅ 104 tests passing (test_blog_stats.py + test_blog_stats_cidade_setor.py) |
| AC1 — 27 UFs cobertas | ✅ |
| AC2 — 12 capitais 200 (unit) | ✅ |
| AC3 — 3 tests parametrizados | ✅ |
| AC4 — Cache flush | ⏭️ SKIP (justificado: `_blog_cache` in-memory, 404 raise antes do cache_set linha 679; cache nunca armazena erros) |
| AC5 — Sitemap regen | ✅ Sitemap usa `CITIES` derivado de `UF_CITIES_RAW` (frontend/lib/cities.ts) — recompila automaticamente no próximo build Next.js após merge. Não requer ação manual. |
| AC6 — Smoke prod 12 capitais | ⏸️ Pendente — devops fará após merge + Railway deploy |

### File List

| File | Change |
|------|--------|
| `backend/routes/blog_stats.py` | UF_CITIES dict expandido 16→27 UFs |
| `frontend/lib/cities.ts` | UF_CITIES_RAW mirror sincronizado |
| `backend/tests/test_blog_stats.py` | TestStorySEO012CapitalsExpansion class adicionada (41 tests) |

### Notes

- **AC4 rationale:** `routes/blog_stats.py` linhas 287-298 (`_cache_get` / `_cache_set`) opera só sobre dict in-memory `_blog_cache` (linha 33). Linha 630 raise HTTPException 404 ANTES de qualquer cache_set. Logo, cidades antes-404 nunca tiveram entrada no cache. Cache flush não é necessário.
- **AC5 rationale:** `frontend/app/sitemap.ts:683` usa `CITIES` array vindo de `frontend/lib/cities.ts`, que deriva de `UF_CITIES_RAW`. Atualizar este dict automaticamente atualiza CITIES → sitemap regenera no próximo build/ISR. Verificado: sitemap.ts não tem hardcode separado de cidades.
- Paste de TESTING: `pytest tests/test_blog_stats.py::TestStorySEO012CapitalsExpansion -v` → 41/41 PASSED em 8.32s.
- **NÃO commitado por @dev** — `@devops` cuida do commit + merge no fim da sessão.
