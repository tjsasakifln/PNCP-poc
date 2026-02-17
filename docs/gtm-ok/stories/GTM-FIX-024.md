# GTM-FIX-024: Fix Multi-Source Search Pipeline — PNCP+PCP Consolidation Completamente Inoperante

## Classificação
- **Priority:** P0 BLOCKER
- **Effort:** M (4-6h, 6 tracks parallelizáveis)
- **Severidade:** Crítica — zero buscas completam em produção

## Dimension Impact
- D01 (Core Functionality): 6/10 → **9/10**
- D02 (Revenue Reliability): 6/10 → **8/10**
- D03 (Data Quality): 6/10 → **8/10**

## Problema

O sistema é **completamente inútil na funcionalidade essencial**: buscar, consolidar, apresentar e analisar dados de licitações. Nenhuma busca completa com sucesso. A investigação revelou **6 bugs encadeados** que, combinados, tornam o pipeline de consolidação multi-source 100% inoperante.

### Erro em Produção (2026-02-17T17:39:29)

```
AttributeError: 'PNCPLegacyAdapter' object has no attribute 'code'
  consolidation.py:503 → _deduplicate()
  consolidation.py:336 → fetch_all()
  search_pipeline.py:658 → _execute_multi_source()
```

---

## Análise de Causa-Raiz: 6 Bugs Encadeados

### BUG 1 — `PNCPLegacyAdapter` sem property `code` (CRASH)
**Arquivo:** `pncp_client.py:1519`
**Causa:** Classe standalone que NÃO herda de `SourceAdapter` (clients/base.py:296). A base class define `code` como property (base.py:316-318) que delega para `self.metadata.code`. Todos os outros adapters herdam e ganham `code` de graça. PNCPLegacyAdapter não.
**Impacto:** `AttributeError` em `consolidation.py:503` — 100% das buscas falham.

### BUG 2 — PCP silenciosamente desabilitado por API key gate
**Arquivo:** `source_config/sources.py:240` + `search_pipeline.py:631`
**Causa:** O método `is_available()` lista apenas `PNCP, COMPRAS_GOV, QUERIDO_DIARIO` como open-data (linha 240). **PORTAL (PCP) ficou de fora**, mesmo que v2 API seja pública e não requeira autenticação. O `search_pipeline.py:631` faz `source_config.portal.credentials.has_api_key()` — como nenhuma API key é setada (v2 não precisa), `has_api_key()` retorna `False` e o adapter **nunca é instanciado**.
**Impacto:** PCP nunca contribui resultados. Consolidação opera apenas com PNCP (single-source disfarçada de multi-source).

### BUG 3 — Dedup key incompatível entre PNCP e PCP
**Arquivo:** `clients/base.py:209-221`
**Causa:** `_generate_dedup_key()` usa `cnpj:numero_edital:ano` quando disponível. PNCP popula `numero_edital` e `ano` corretamente. PCP frequentemente NÃO tem `numero_edital` (depende do campo `numero` da API v2, que pode ser vazio). Sem `numero_edital`, o fallback é `cnpj:objeto_hash:valor_estimado`. Mas PCP v2 retorna `valor_estimado=0.0` (hardcoded em portal_compras_client.py:426). Resultado: PNCP gera key `12345:EDITAL-01:2026`, PCP gera key `12345:abc123:0` — **nunca colidem, nunca deduplicam**.
**Impacto:** Mesma licitação aparece duplicada (uma do PNCP, outra do PCP). Inflação de resultados.

### BUG 4 — Colisão falsa de dedup keys do PCP (valor=0)
**Arquivo:** `clients/base.py:221`
**Causa:** Quando PCP usa fallback dedup (`cnpj:hash:valor`), TODOS os records PCP têm `valor=0`. Se duas licitações do mesmo órgão tiverem `objeto` similar (mesmo hash MD5), geram dedup_key idêntico → uma é descartada erroneamente.
**Impacto:** Licitações PCP diferentes do mesmo órgão com texto similar são falsamente deduplicadas. Perda silenciosa de resultados.

### BUG 5 — `modalidadeId` ausente no legacy format
**Arquivo:** `clients/base.py:255-290`
**Causa:** `to_legacy_format()` produz `modalidadeNome` mas NÃO `modalidadeId` nem `codigoModalidadeContratacao`. O `filter.py:1968` faz `lic.get("modalidadeId") or lic.get("codigoModalidadeContratacao")` — ambos retornam `None`. Filtro por modalidade silenciosamente não aplica.
**Impacto:** Filtro de modalidade bypassed — resultados incluem modalidades não solicitadas.

### BUG 6 — Sem validação de contrato no ConsolidationService
**Arquivo:** `consolidation.py:95-99`
**Causa:** `__init__()` aceita qualquer dict de adapters sem verificar se implementam a interface `SourceAdapter`. O erro só estoura em `_deduplicate()` **após minutos de fetch** de APIs externas. Dados coletados são descartados.
**Impacto:** Waste de tempo e recursos. Erro poderia ser detectado em <1ms na construção.

---

## Solução: 6 Tracks

### Track 1 — Fix PNCPLegacyAdapter interface (P0)
Adicionar properties `code` e `name` ao `PNCPLegacyAdapter`, ou idealmente fazer herdar de `SourceAdapter`.

**Opção A (minimal, 2 linhas):**
```python
# pncp_client.py após linha 1555:
@property
def code(self) -> str:
    return self.metadata.code

@property
def name(self) -> str:
    return self.metadata.name
```

**Opção B (estrutural, recomendada):**
```python
# pncp_client.py linha 1519:
from clients.base import SourceAdapter  # lazy-loaded, já ocorre dentro dos métodos
class PNCPLegacyAdapter(SourceAdapter):
```

### Track 2 — Desbloquear PCP como open-data source (P0)
Adicionar `SourceCode.PORTAL` à lista de open-data em `source_config/sources.py:240` e remover check de API key no `search_pipeline.py:631`.

```python
# source_config/sources.py:240 — ANTES:
if self.code in (SourceCode.PNCP, SourceCode.COMPRAS_GOV, SourceCode.QUERIDO_DIARIO):
# DEPOIS:
if self.code in (SourceCode.PNCP, SourceCode.COMPRAS_GOV, SourceCode.QUERIDO_DIARIO, SourceCode.PORTAL):

# search_pipeline.py:631 — ANTES:
if source_config.portal.enabled and source_config.portal.credentials.has_api_key():
# DEPOIS:
if source_config.portal.enabled:
```

### Track 3 — Fix dedup key cross-source (P0)
Melhorar `_generate_dedup_key()` para produzir keys compatíveis entre PNCP e PCP. Incluir `data_publicacao` como componente alternativo ao `valor_estimado` quando valor é zero.

```python
# base.py:218-221 — Fallback melhorado:
def _generate_dedup_key(self) -> str:
    cnpj_clean = re.sub(r"[^\d]", "", self.cnpj_orgao) if self.cnpj_orgao else ""
    if self.numero_edital and self.ano:
        return f"{cnpj_clean}:{self.numero_edital}:{self.ano}"
    # Fallback: usar hash do objeto + data (não valor, que PCP retorna como 0.0)
    objeto_normalized = " ".join(self.objeto.lower().split()) if self.objeto else ""
    objeto_hash = hashlib.md5(objeto_normalized.encode()).hexdigest()[:12]
    date_str = ""
    if self.data_publicacao:
        date_str = self.data_publicacao.strftime("%Y%m%d")
    elif self.data_abertura:
        date_str = self.data_abertura.strftime("%Y%m%d")
    return f"{cnpj_clean}:{objeto_hash}:{date_str}"
```

### Track 4 — Adicionar `modalidadeId` no legacy format (P1)
Incluir campo `modalidadeId` no dict de `to_legacy_format()`. Se o valor numérico não estiver disponível, mapear da string ou do `raw_data`.

```python
# base.py:276, após modalidadeNome:
"modalidadeId": self.raw_data.get("modalidadeId") or self.raw_data.get("codigoModalidadeContratacao") if self.raw_data else None,
```

### Track 5 — Validação de contrato no ConsolidationService (P1)
Fail-fast na construção se adapter não implementa interface.

```python
# consolidation.py, no __init__() após self._adapters = adapters:
for code, adapter in self._adapters.items():
    for attr in ('code', 'metadata', 'fetch', 'health_check'):
        if not hasattr(adapter, attr):
            raise TypeError(
                f"Adapter '{code}' ({type(adapter).__name__}) missing '{attr}'. "
                f"Must implement SourceAdapter interface."
            )
```

### Track 6 — Testes de integração end-to-end (P1)
Testes que exercitam o fluxo completo: criação de adapters → fetch → dedup → response, verificando:
- Contrato de interface de todos os adapters
- Dedup correto entre fontes PNCP e PCP
- Legacy format compatível com filter.py downstream

---

## Acceptance Criteria

### Track 1 — PNCPLegacyAdapter Interface Fix (P0)
- [ ] AC1: `PNCPLegacyAdapter().code` retorna `"PNCP"` sem `AttributeError`
- [ ] AC2: `PNCPLegacyAdapter().name` retorna `"PNCP"` sem `AttributeError`
- [ ] AC3: `consolidation._deduplicate()` completa sem erro com `PNCPLegacyAdapter` no dict
- [ ] AC4: Busca com `ENABLE_MULTI_SOURCE=true` retorna resultados (não 500)
- [ ] AC5: Teste unitário `test_pncp_legacy_adapter_code_property`
- [ ] AC6: Teste unitário `test_pncp_legacy_adapter_metadata_priority`

### Track 2 — PCP Open-Data Desbloqueio (P0)
- [ ] AC7: `SourceCode.PORTAL` está na lista open-data de `is_available()` (sources.py:240)
- [ ] AC8: `search_pipeline.py` instancia `PortalComprasAdapter` sem exigir API key
- [ ] AC9: Com `PCP_ENABLED=true` (default), adapter "PORTAL_COMPRAS" presente no dict de adapters
- [ ] AC10: Log de INFO quando PCP adapter é instanciado com sucesso
- [ ] AC11: Teste unitário verifica que `PortalComprasAdapter` é criado sem API key

### Track 3 — Dedup Key Cross-Source Fix (P0)
- [ ] AC12: Dedup key não usa `valor_estimado` quando valor é 0.0
- [ ] AC13: Dedup key usa `data_publicacao` como componente alternativo
- [ ] AC14: Duas licitações PCP diferentes do mesmo órgão geram keys distintas
- [ ] AC15: Mesma licitação em PNCP e PCP com `numero_edital+ano` gera key idêntica → dedup correto
- [ ] AC16: Teste com records mock: PNCP(priority=1) + PCP(priority=2) com mesma key → PNCP vence

### Track 4 — modalidadeId no Legacy Format (P1)
- [ ] AC17: `to_legacy_format()` inclui campo `modalidadeId` quando disponível em `raw_data`
- [ ] AC18: `filter.py` encontra `modalidadeId` no dict consolidado e aplica filtro corretamente
- [ ] AC19: Teste unitário verifica presença de `modalidadeId` no output de `to_legacy_format()`

### Track 5 — Contract Validation (P1)
- [ ] AC20: `ConsolidationService.__init__()` raises `TypeError` se adapter sem `code`
- [ ] AC21: `ConsolidationService.__init__()` raises `TypeError` se adapter sem `metadata`
- [ ] AC22: Mensagem de erro inclui nome da classe e atributo faltante
- [ ] AC23: Teste unitário com adapter mock incompleto

### Track 6 — Integration Tests (P1)
- [ ] AC24: Teste parametrizado verifica `hasattr(adapter, attr)` para todos os 5 adapters × 4 atributos
- [ ] AC25: Teste de integração: cria ConsolidationService com PNCPLegacyAdapter + PortalComprasAdapter, chama `_deduplicate()` com records mistos, verifica PNCP vence por prioridade
- [ ] AC26: Teste de integração: verifica `to_legacy_format()` produz dict compatível com `filter.py` (campos `objetoCompra`, `valorTotalEstimado`, `modalidadeId`, etc.)
- [ ] AC27: Todos os testes pre-existentes passam sem regressão

---

## Arquivos Afetados

| Track | Arquivo | Linhas | Mudança |
|-------|---------|--------|---------|
| T1 | `backend/pncp_client.py` | 1519, 1547-1555 | Adicionar `code`/`name` properties ou herdar `SourceAdapter` |
| T2 | `backend/source_config/sources.py` | 240 | Adicionar `SourceCode.PORTAL` à lista open-data |
| T2 | `backend/search_pipeline.py` | 631 | Remover `has_api_key()` check para PCP |
| T3 | `backend/clients/base.py` | 209-221 | Melhorar `_generate_dedup_key()` fallback |
| T4 | `backend/clients/base.py` | 276 | Adicionar `modalidadeId` em `to_legacy_format()` |
| T5 | `backend/consolidation.py` | ~95-99 | Adicionar validação de contrato em `__init__()` |
| T6 | `backend/tests/test_adapter_contract.py` | novo | Testes parametrizados de conformidade |
| T6 | `backend/tests/test_consolidation_integration.py` | novo | Testes de integração end-to-end |

---

## Mapa de Dependências dos Bugs

```
BUG 1 (adapter.code)     ──── CRASH ──── Nenhuma busca funciona
  │
  └──▶ Se resolvido sozinho: PNCP funciona, mas...
         │
BUG 2 (PCP silenciado)   ──── PCP nunca instanciado ──── Single-source disfarçada
  │
  └──▶ Se resolvido + BUG 1: PNCP+PCP chegam ao dedup, mas...
         │
BUG 3 (dedup keys)       ──── Keys incompatíveis ──── Nunca deduplicam
BUG 4 (valor=0 colisão)  ──── False dedup ──── Perda de resultados PCP
  │
  └──▶ Se tudo resolvido: Dados chegam ao filter, mas...
         │
BUG 5 (modalidadeId)     ──── Filtro bypassed ──── Resultados inflados
```

**Conclusão:** Resolver apenas BUG 1 faz as buscas pararem de crashar, mas o sistema opera em single-source (apenas PNCP) sem dedup funcional. Os 6 bugs devem ser resolvidos juntos para que o sistema entregue o output esperado: **consolidação multi-source com deduplicação correta e filtragem funcional**.

---

## Tabela de Prioridade dos Adapters (Referência)

| Adapter | Classe | Code | Priority | Herda SourceAdapter? | Open-Data? |
|---------|--------|------|----------|---------------------|------------|
| PNCP | `PNCPLegacyAdapter` | `PNCP` | 1 | **NÃO (BUG 1)** | Sim |
| Portal de Compras | `PortalComprasAdapter` | `PORTAL_COMPRAS` | 2 | Sim | **Sim, mas não listado (BUG 2)** |
| Portal Transparência | `PortalTransparenciaAdapter` | `PORTAL_TRANSPARENCIA` | 3 | Sim | Não (requer API key) |
| ComprasGov | `ComprasGovAdapter` | `COMPRAS_GOV` | 4 | Sim | Sim |
| Querido Diário | `QueridoDiarioClient` | `QUERIDO_DIARIO` | 5 | Sim | Sim |

---

## Práticas Consagradas Aplicadas

1. **[PEP 544 — Structural Subtyping](https://peps.python.org/pep-0544/)** — Se não herda ABC, use `Protocol` para type safety
2. **[ABC vs Protocol](https://jellis18.github.io/post/2022-01-11-abc-vs-protocol/)** — Use ABCs quando há implementação compartilhada (como property `code`)
3. **[Adapter Pattern — Refactoring Guru](https://refactoring.guru/design-patterns/adapter/python/example)** — Nunca confiar em conformidade implícita sem verificação
4. **[ETL Dedup Best Practices — Airbyte](https://airbyte.com/data-engineering-resources/the-best-way-to-handle-data-deduplication-in-etl)** — Validar contratos nas fronteiras do pipeline
5. **[Fail-Fast Principle — Softkraft](https://www.softkraft.co/python-data-pipelines/)** — Detectar violações de interface na construção, não na execução
6. **[Data Consolidation Guide](https://datasights.co/data-consolidation/)** — Dedup com unique identifiers consistentes entre fontes

---

## Rollback Plan

Se o fix causar problemas inesperados:
- `ENABLE_MULTI_SOURCE=false` → fallback para modo PNCP-only (bypass completo da consolidação)
- `PCP_ENABLED=false` → desabilita apenas PCP, mantém PNCP via consolidação
- Ambos já são paths existentes em `search_pipeline.py:528-539`

## Definition of Done

Após implementação completa dos 6 tracks:
1. Busca por UF(SP) retorna resultados de **ambas as fontes** (PNCP + PCP)
2. Resultados duplicados entre fontes são corretamente deduplicados (PNCP vence)
3. Filtros de modalidade funcionam no output consolidado
4. Zero `AttributeError` em produção
5. Todos os testes passam sem regressão vs baseline

## Post-Fix Verification

```bash
# Testes unitários
cd backend && python -m pytest tests/test_gtm_fix_017.py tests/test_adapter_contract.py tests/test_consolidation_integration.py -v

# Smoke test local
curl -X POST http://localhost:8000/buscar \
  -H "Content-Type: application/json" \
  -d '{"ufs":["SP"],"data_inicial":"2026-02-10","data_final":"2026-02-17","setor_id":1}'
# Esperado: 200 OK com resultados de PNCP e PCP (verificar campo _source)
```
