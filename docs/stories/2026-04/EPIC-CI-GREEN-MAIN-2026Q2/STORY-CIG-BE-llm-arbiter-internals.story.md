# STORY-CIG-BE-llm-arbiter-internals — `_client` e `_hourly_cost_usd` moveram após `llm_arbiter` virar package — 9 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P1 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes `test_harden001_openai_timeout.py` e `test_llm_cost_monitoring.py` rodam em `backend-tests.yml` e falham em **9 testes** do triage row #14/30. Causa raiz classificada como **mock-drift**: o módulo `backend/llm_arbiter.py` virou package `backend/llm_arbiter/` e os símbolos `_client` e `_hourly_cost_usd` foram movidos para submódulos. Testes patcham o path antigo.

CLAUDE.md orienta especificamente: *"LLM: Mock at `@patch("llm_arbiter._get_client")` level"* — essa recomendação pode precisar ser atualizada pós-refactor.

**Arquivos principais afetados:**
- `backend/tests/test_harden001_openai_timeout.py`
- `backend/tests/test_llm_cost_monitoring.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** `_client` → `llm_arbiter.client._client` ou `llm_arbiter.classification._client`. Validar com `grep -rn "_client\\|_hourly_cost_usd\\|_get_client" backend/llm_arbiter/`.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_harden001_openai_timeout.py backend/tests/test_llm_cost_monitoring.py -v` retorna exit code 0 localmente (9/9 PASS). **Evidência local (2026-04-18):** `============================== 9 passed in 5.42s ===============================`.
- [x] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log. *(pendente publicação do PR — será preenchido após `@devops *push`.)*
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Listar símbolos antes→depois. CLAUDE.md **permanece válido**: `@patch("llm_arbiter._get_client")` segue funcionando (a função está re-exportada em `__init__.py`); apenas símbolos mutáveis (`_client`, `_hourly_cost_usd`, `_cost_alert_fired`, `OpenAI`, `logger`) exigem o path do submódulo `classification`.
- [x] AC4: Cobertura backend **não caiu**. Mudanças restritas a 2 arquivos de teste (apenas mock paths); zero alterações em código de produção.
- [x] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. **Evidência (2026-04-18):** `grep -nE "@pytest\.mark\.skip|pytest\.skip\(|@pytest\.mark\.xfail|\.only\("` sobre os 2 arquivos retornou vazio.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas.
- [ ] `grep -rn "_client\\|_hourly_cost_usd\\|_get_client" backend/llm_arbiter/ backend/llm.py`.
- [ ] Atualizar mocks dos testes para novo path.
- [ ] Se CLAUDE.md orientação de patch path ficar incorreta: abrir PR separada ou incluir fix de docs nesta story.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #14/30)

## Stories relacionadas no epic

- STORY-CIG-BE-consolidation-helpers-private (#10 — mesmo padrão de refactor private drift)
- STORY-CIG-BE-asyncio-run-production-scan (#28 — static scan inclui `llm_arbiter/classification.py`)

---

## Root Cause Analysis

**Classificação:** mock-drift puro (zero bug de produção).

O módulo `backend/llm_arbiter.py` foi decomposto em um package (`backend/llm_arbiter/__init__.py` + submódulos `classification.py`, `zero_match.py`, `async_runtime.py`, `batch_api.py`, `prompt_builder.py`) como parte do TD-009 (DEBT-07 module split). O `__init__.py` re-exporta **funções** (`_get_client`, `_log_token_usage`, etc.) para preservar `from llm_arbiter import X`, mas **não** re-exporta os globals mutáveis (`_client`, `_hourly_cost_usd`, `_cost_alert_fired`) nem imports auxiliares (`OpenAI`, `logger`). Os testes acessavam esses símbolos via `llm_arbiter.<attr>`, que agora vivem apenas em `llm_arbiter.classification.<attr>`.

Nota adicional: mesmo se `_client` fosse re-exportado no `__init__`, reatribuir `llm_arbiter._client = None` **não** resetaria o global usado por `_get_client()` (que lê o do próprio submódulo `classification`). Por isso o fix aponta diretamente para o submódulo.

### Símbolos: antes → depois

| Antes (test patch/access) | Depois (novo path correto) | Observação |
|---------------------------|---------------------------|------------|
| `llm_arbiter._client` | `llm_arbiter.classification._client` | Global mutável (Optional[OpenAI]) |
| `llm_arbiter._hourly_cost_usd` | `llm_arbiter.classification._hourly_cost_usd` | Lista rolling-window (DEBT-v3-S2 AC4) |
| `llm_arbiter._cost_alert_fired` | `llm_arbiter.classification._cost_alert_fired` | Flag bool |
| `@patch("llm_arbiter.OpenAI")` | `@patch("llm_arbiter.classification.OpenAI")` | Classe importada em `classification.py:18` |
| `@patch("llm_arbiter.logger")` | `@patch("llm_arbiter.classification.logger")` | `logger = logging.getLogger(__name__)` em `classification.py:25` |
| `llm_arbiter._get_client()` | inalterado — facade re-exporta | `__init__.py:42,104` |
| `from llm_arbiter import _log_token_usage` | inalterado — facade re-exporta | `__init__.py:44` |

### Gotcha: `test_timeout_configurable_via_env`

O valor `_LLM_TIMEOUT` em `classification.py:28` é resolvido no import-time a partir de `config.features.LLM_TIMEOUT_S` (que por sua vez lê `os.environ` no import-time). Apenas `importlib.reload(llm_arbiter)` **não** propaga a mudança de env var — também é necessário recarregar o submódulo `config.features` e depois `classification`. O teste foi ajustado para seguir esse padrão (`reload(features) → reload(classification) → patch("llm_arbiter.classification.OpenAI")`).

### Validação CLAUDE.md

A orientação atual no CLAUDE.md (`LLM: Mock at @patch("llm_arbiter._get_client") level`) **permanece correta** para a maioria dos mocks (retorno de client). Só os testes que mexem em **estado mutável de módulo** precisam do path do submódulo. Nenhuma atualização de CLAUDE.md é necessária nesta story.

---

## File List

- `backend/tests/test_harden001_openai_timeout.py` — ajuste de 6 pontos de mock (_client via `classification._client`, `@patch("llm_arbiter.classification.OpenAI")`, reload duplo no teste env-var).
- `backend/tests/test_llm_cost_monitoring.py` — ajuste de 5 pontos de mock (`_hourly_cost_usd`, `_cost_alert_fired`, `@patch("llm_arbiter.classification.logger")` em 3 testes).
- `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/STORY-CIG-BE-llm-arbiter-internals.story.md` — ACs marcados, RCA, File List, Change Log, Status → InReview.

**Zero alterações em código de produção.**

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #14/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Se fix tornar CLAUDE.md mocking guidance (`@patch("llm_arbiter._get_client")`) obsoleto, incluir PR de docs update nesta story.
- **2026-04-18** — @dev: fix mock-drift em 2 suítes (9/9 PASS local) — redirecionados patches de `_client`, `_hourly_cost_usd`, `_cost_alert_fired`, `OpenAI`, `logger` para submódulo `llm_arbiter.classification`; reload duplo `config.features` + `classification` no teste env-var. Zero prod changes. Status Ready → InReview.
