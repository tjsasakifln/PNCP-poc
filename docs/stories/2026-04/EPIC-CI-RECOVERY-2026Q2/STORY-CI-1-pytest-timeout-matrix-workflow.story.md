# STORY-CI-1 — pytest-timeout ausente no matrix workflow (Python 3.11/3.12)

**Epic:** EPIC-CI-RECOVERY-2026Q2  
**Sprint:** 2026-Q2-S3  
**Status:** Ready  
**Priority:** P0 — Blocker  
**Effort:** XS (<1h)  
**Agents:** @dev, @devops  

---

## Contexto

O workflow `.github/workflows/tests.yml` ("Tests — Full Matrix + Integration + E2E") executa os testes de backend em matrix com Python 3.11 e 3.12. O step "Install dependencies" desse job instala apenas `requirements.txt` + alguns pacotes avulsos — omitindo `pytest-timeout`.

O `backend/pyproject.toml` declara `timeout = 30.0` em `[tool.pytest.ini_options]`, que requer o plugin `pytest-timeout`. Sem ele, o pytest falha na coleção com:

```
INTERNALERROR> pytest.PytestConfigWarning: Unknown config option: timeout
```

Isso bloqueia **toda** a suite no matrix job desde 2026-04-14. O workflow dedicado `backend-tests.yml` NÃO é afetado (instala `pytest-timeout` explicitamente), mas o matrix job é o gate de PR/main.

---

## Acceptance Criteria

- [x] AC1: `backend/requirements-dev.txt` contém `pytest-timeout==2.3.1` (já confirmado — não requer alteração)
- [x] AC2: O step "Install dependencies" do job `backend-tests` em `.github/workflows/tests.yml` usa `pip install -r requirements-dev.txt`
- [ ] AC3: O matrix job (Python 3.11 e 3.12) coleta testes sem `PytestConfigWarning: Unknown config option: timeout` (a verificar no CI)
- [ ] AC4: Zero novas falhas de teste introduzidas além da baseline de 292 pre-existing (a verificar no CI)

---

## Implementação

**Arquivo:** `.github/workflows/tests.yml`

Localizar o job `backend-tests` (ou nome equivalente que roda em matrix `python-version: [3.11, 3.12]`) e alterar o step:

```yaml
# ANTES:
- name: Install dependencies
  run: |
    cd backend
    if [ -f requirements.txt ]; then
      pip install -r requirements.txt
    fi
    pip install pytest pytest-cov pytest-asyncio httpx

# DEPOIS:
- name: Install dependencies
  run: |
    cd backend
    pip install -r requirements-dev.txt
```

`requirements-dev.txt` linha 1 é `-r requirements.txt` — inclui todas as dependências de produção. Não há regressão.

---

## Verificação Local

```bash
# Simular install como CI faz
pip install -r backend/requirements-dev.txt

# Confirmar pytest-timeout instalado
python -c "import pytest_timeout; print(pytest_timeout.__version__)"
# Esperado: 2.3.1

# Coleção sem warnings
cd backend && python -m pytest --collect-only -q 2>&1 | grep -i "warning\|error" | head -20
```

---

## File List

- `.github/workflows/tests.yml` — step "Install dependencies" do job backend-tests
