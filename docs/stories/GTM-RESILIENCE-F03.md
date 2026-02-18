# GTM-RESILIENCE-F03 --- Realinhar Timeout PerModality < PerUF (Hierarquia Estrita)

| Campo | Valor |
|-------|-------|
| **Track** | F: Infra para Escala |
| **Prioridade** | P2 |
| **Sprint** | 3 |
| **Estimativa** | 2-3 horas (2 tracks paralelizaveis) |
| **Gaps** | I-07 |
| **Dependencias** | Nenhuma |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

A cadeia de timeouts do pipeline foi recalibrada no GTM-FIX-029 (commit `e6e2ec9`) para acomodar o `tamanhoPagina=50` da PNCP. A cadeia resultante e:

```
FE Proxy(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s) > PerUF(90s) < PerModality(120s) > HTTP(30s)
```

O GTM-FIX-029 documentou explicitamente a **near-inversion** entre PerModality(120s) e PerUF(90s) como "intencional" porque as 4 modalidades rodam em paralelo dentro do UF. O argumento e que o tempo real do UF e `max(mod1, mod2, mod3, mod4)`, nao a soma, entao 90s basta.

### Situacao Atual

- **PerModality**: 120s (`PNCP_TIMEOUT_PER_MODALITY` em `pncp_client.py` L53-54)
- **PerUF**: 90s normal, 120s degradado (`PNCP_TIMEOUT_PER_UF` em `pncp_client.py` L64-69)
- **Relacao**: PerModality(120s) > PerUF(90s) --- **inversao em modo normal**
- **Near-inversion warning**: `consolidation.py` loga warning quando `per_source > 80% * global`, mas **nao ha warning para PerModality > PerUF**
- **Teste existente**: `test_timeout_chain.py::TestTimeoutChainInvariant::test_per_modality_fits_within_per_uf` valida `PerUF >= PerModality * 0.5` (50%) --- condicao fraca, permite inversao
- **Env vars**: Ambos configuraveis via `PNCP_TIMEOUT_PER_MODALITY` e `PNCP_TIMEOUT_PER_UF`

### Impacto

O cenario problematico ocorre quando **uma unica modalidade demora mais que o PerUF timeout**:

1. UF=SP inicia 4 modalidades em paralelo via `asyncio.gather()`
2. Mod 6 (saude) tem 50+ paginas --- levaria ~80s
3. Mods 1,4,5 completam em 5-15s cada
4. `asyncio.wait_for(gather(...), timeout=PER_UF_TIMEOUT=90s)` cancela tudo aos 90s
5. Mod 6 tinha 70 paginas processadas de 80 --- **dados parciais descartados**
6. Se PerModality fosse 60s, Mod 6 teria sido cortada e as outras preservadas

Com PerModality > PerUF, o timeout por modalidade nunca efetivamente atua em modo normal --- e o PerUF que corta, perdendo potencialmente dados parciais de todas as modalidades.

---

## Problema

`PNCP_TIMEOUT_PER_MODALITY=120s` excede `PNCP_TIMEOUT_PER_UF=90s`, criando uma inversao na hierarquia de timeouts. Isso significa que:

1. O timeout por modalidade e **inefetivo** em modo normal (o UF sempre estoura antes)
2. Uma modalidade lenta pode consumir todo o budget do UF sem ser cortada
3. Dados parciais de modalidades rapidas podem ser descartados junto com a lenta
4. O `near-inversion warning` existente no `consolidation.py` nao cobre esta relacao
5. Nao ha validacao no startup que rejeite configuracoes onde PerModality >= PerUF

---

## Solucao

Enforce hierarquia estrita onde **PerModality < PerUF** com margem minima de 30s, e adicionar validacao no startup que previna misconfiguracoes:

1. **Reduzir PerModality** de 120s para 60s (default) --- margem de 30s abaixo do PerUF(90s)
2. **Adicionar validacao no startup** que rejeita `PerModality >= PerUF` com log critico e fallback para valores seguros
3. **Atualizar testes** para enforce a hierarquia estrita (nao 50% como hoje)
4. **Documentar** a cadeia completa com invariantes nos comentarios de config

---

## Acceptance Criteria

### Track 1 --- Recalibracao de Timeouts (P0)

- [ ] **AC1**: `PNCP_TIMEOUT_PER_MODALITY` default alterado de `"120"` para `"60"` em `pncp_client.py` L54
- [ ] **AC2**: Hierarquia resultante e estritamente decrescente em todos os niveis:
  ```
  FE(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s) > PerUF(90s) > PerModality(60s) > HTTP(30s)
  ```
- [ ] **AC3**: Margem entre PerUF e PerModality e >= 30s em modo normal (90 - 60 = 30s)
- [ ] **AC4**: Em modo degradado: PerUF=120s, PerModality=60s --- margem de 60s (confortavel)
- [ ] **AC5**: Comentario atualizado em `pncp_client.py` explicando calculo:
  ```
  # PerModality=60s: max ~120 paginas (50 items/page) a ~0.5s/req.
  # Suficiente para 6000 items por modalidade. Raro exceder.
  # Hierarquia: PerModality(60s) < PerUF(90s) --- margem 30s.
  ```
- [ ] **AC6**: Env var `PNCP_TIMEOUT_PER_MODALITY` continua funcional para override manual

### Track 2 --- Validacao no Startup (P0)

- [ ] **AC7**: Funcao `validate_timeout_chain()` criada em `pncp_client.py` (ou `config.py`)
- [ ] **AC8**: `validate_timeout_chain()` chamada durante import do modulo `pncp_client` (module-level validation)
- [ ] **AC9**: Se `PNCP_TIMEOUT_PER_MODALITY >= PNCP_TIMEOUT_PER_UF`, logar `logger.critical()` com mensagem:
  ```
  "TIMEOUT MISCONFIGURATION: PerModality({X}s) >= PerUF({Y}s).
   Modality timeout must be strictly less than UF timeout.
   Falling back to safe defaults: PerModality=60s, PerUF=90s."
  ```
- [ ] **AC10**: Apos log critico, forcar valores seguros: PerModality=60s, PerUF=90s (nao crashar o server)
- [ ] **AC11**: Se `PNCP_TIMEOUT_PER_MODALITY > PNCP_TIMEOUT_PER_UF * 0.8` (near-inversion), logar `logger.warning()`:
  ```
  "TIMEOUT NEAR-INVERSION: PerModality({X}s) > 80% of PerUF({Y}s).
   Recommend PerModality <= {Y*0.67:.0f}s for safe margin."
  ```
- [ ] **AC12**: Validacao tambem verifica `PNCP_TIMEOUT_PER_UF > PNCP_TIMEOUT_PER_MODALITY * 0.5` (minimo 50% headroom) --- redundante com AC9 mas explicita a intencao

### Track 3 --- Atualizacao de Testes (P0)

- [ ] **AC13**: `test_timeout_chain.py::test_per_modality_fits_within_per_uf` atualizado:
  - **Antes**: `assert PNCP_TIMEOUT_PER_UF >= PNCP_TIMEOUT_PER_MODALITY * 0.5` (fraco)
  - **Depois**: `assert PNCP_TIMEOUT_PER_MODALITY < PNCP_TIMEOUT_PER_UF` (estrito)
- [ ] **AC14**: Novo teste: `test_per_modality_default_60s` --- valida que default mudou para 60s
- [ ] **AC15**: Novo teste: `test_per_modality_margin_30s` --- valida `PNCP_TIMEOUT_PER_UF - PNCP_TIMEOUT_PER_MODALITY >= 30`
- [ ] **AC16**: Novo teste: `test_startup_validation_rejects_inversion` --- simula `PerModality=100, PerUF=90`, verifica log critico e fallback
- [ ] **AC17**: Novo teste: `test_startup_validation_warns_near_inversion` --- simula `PerModality=80, PerUF=90`, verifica log warning
- [ ] **AC18**: Novo teste: `test_startup_validation_passes_healthy` --- simula `PerModality=60, PerUF=90`, verifica nenhum warning
- [ ] **AC19**: Testes existentes em `test_pncp_hardening.py` que patcheiam `PNCP_TIMEOUT_PER_MODALITY` atualizados para valores compativeis com nova validacao
- [ ] **AC20**: Zero near-inversion warnings nos logs quando rodando com defaults (confirmar via caplog nos testes)

### Track 4 --- Documentacao e Env Vars (P1)

- [ ] **AC21**: Cadeia completa documentada em comentario no topo de `pncp_client.py` (ou `config.py`):
  ```
  # TIMEOUT CHAIN (strict decreasing, validated at startup):
  # FE Proxy(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s)
  #   > PerUF(90s) > PerModality(60s) > HTTP(30s)
  # Invariants:
  #   - Each level must be strictly greater than the next
  #   - PerUF - PerModality >= 30s (margin for parallel modality completion)
  #   - PerSource > 2 * PerUF (margin for multi-UF batches)
  ```
- [ ] **AC22**: Env var `PNCP_TIMEOUT_PER_MODALITY` documentada em `.env.example` com default 60 e nota sobre hierarquia
- [ ] **AC23**: Se Railway env vars existirem para `PNCP_TIMEOUT_PER_MODALITY`, atualizar para 60 (ou remover para usar default)

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/pncp_client.py` L53-54 | Default `PNCP_TIMEOUT_PER_MODALITY`: `"120"` -> `"60"` |
| `backend/pncp_client.py` (novo) | Funcao `validate_timeout_chain()` + chamada module-level |
| `backend/tests/test_timeout_chain.py` | Atualizar `test_per_modality_fits_within_per_uf` de 50% para estrito |
| `backend/tests/test_timeout_chain.py` | 6 novos testes (AC14-AC18, AC20) |
| `backend/tests/test_pncp_hardening.py` | Atualizar patches de `PNCP_TIMEOUT_PER_MODALITY` onde necessario |
| `.env.example` | Documentar `PNCP_TIMEOUT_PER_MODALITY=60` |

---

## Dependencias

| Dependencia | Tipo | Status |
|-------------|------|--------|
| GTM-FIX-029 (timeout chain) | Completada | Commit `e6e2ec9` --- base para esta correcao |
| Nenhuma nova dependencia de pacote | --- | --- |

---

## Definition of Done

- [ ] `PNCP_TIMEOUT_PER_MODALITY` default e 60s
- [ ] Hierarquia estrita: PerModality(60s) < PerUF(90s) confirmada por testes
- [ ] Startup validation previne inversao e loga critico + fallback
- [ ] Startup validation detecta near-inversion e loga warning
- [ ] Zero warnings nos logs com configuracao default
- [ ] 6 novos testes passando
- [ ] Todos os testes existentes passam sem regressao (baseline: ~3400 pass)
- [ ] Cadeia documentada em comentarios do codigo
- [ ] Env var documentada em .env.example

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| 60s insuficiente para modalidades com 100+ paginas (5000+ items) | Baixa | Medio | Cenario raro (SP Saude pico); busca retorna parcial + retry automatico de UFs falhas |
| Testes existentes hardcoded com `PNCP_TIMEOUT_PER_MODALITY=120` falham | Media | Baixo | Atualizar patches em test_pncp_hardening.py (AC19) |
| Railway env var override mantendo 120s | Baixa | Baixo | AC23: verificar e remover/atualizar env vars |
| Module-level validation crashar import | Baixa | Alto | Validacao faz fallback seguro (AC10), nunca raise |

---

## Notas Tecnicas

### Calculo de Capacidade com PerModality=60s

```
Items por pagina: 50 (PNCP max)
Tempo por pagina: ~0.5-1.0s (com rate limiting 100ms + jitter)
Paginas em 60s: ~60-120 paginas
Items em 60s: 3000-6000 items por modalidade
```

Dados de producao (2026-02-17) mostram que a modalidade com mais items (SP/Saude/mod6) tinha ~750 items = 15 paginas = ~15s. O teto de 60s cobre cenarios 4x maiores que o pior caso observado.

### Por que nao PerModality=45s (50% do PerUF)?

45s cobre 2250-4500 items por modalidade, suficiente para 99.9% dos casos. Porem, 60s da margem adicional sem custo (as modalidades rodam em paralelo, entao o UF nao "gasta" mais por ter PerModality=60s). O custo real e zero --- o ganho e resiliencia contra picos sazonais.

### Validacao Module-Level vs Startup Hook

A validacao ocorre no import de `pncp_client.py` (module-level) e nao no `lifespan()` de `main.py`. Justificativa:

1. **Qualquer modulo que importar pncp_client** tera a validacao
2. **Testes** que importam pncp_client tambem sao validados
3. **Falha precoce**: misconfiguracao detectada antes de qualquer request
4. **Sem side effects**: validacao so le env vars e ajusta module-level globals

### Cadeia Final Apos Fix

```
CAMADA 0: Frontend Proxy               480s   (route.ts)
CAMADA 1: Pipeline FETCH_TIMEOUT        360s   (search_pipeline.py)
CAMADA 2: Consolidation Global          300s   (sources.py)
CAMADA 3: Consolidation Per-Source      180s   (sources.py)
CAMADA 4: Per-UF Timeout                 90s   (pncp_client.py)    [normal]
CAMADA 4d: Per-UF Timeout (degraded)    120s   (pncp_client.py)    [degraded]
CAMADA 5: Per-Modality Timeout           60s   (pncp_client.py)    <-- ALTERADO
CAMADA 6: Per-Page HTTP                  30s   (config.py)

Invariantes (validadas por testes + startup):
  480 > 360 > 300 > 180 > 90 > 60 > 30  (estritamente decrescente)
  90 - 60 >= 30                           (margem PerUF-PerModality)
```
