---
name: Setup Test Frameworks (pytest + jest)
about: Configurar frameworks de teste para backend e frontend
title: 'Setup Test Frameworks (pytest + jest)'
labels: 'infrastructure, testing, setup'
assignees: ''

---

## 📋 Descrição

Configurar frameworks de teste para backend (pytest) e frontend (jest) conforme especificado em CLAUDE.md e PRD Seção 9.

**EPIC:** #2 (Setup e Infraestrutura Base)
**Prioridade:** P1 (Alta)
**Estimativa:** 2 horas

## 🎯 Objetivo

Estabelecer infraestrutura de testes com coverage reporting para garantir qualidade do código.

## 📚 Referência PRD

- **PRD Seção 9:** Dependências (pytest, jest mencionados)
- **CLAUDE.md linhas 39-43:** Comandos pytest
- **CLAUDE.md linha 649:** Testing strategy (70% backend, 60% frontend)

## ✅ Acceptance Criteria

### Backend (pytest)
- [ ] `pytest` instalado em requirements.txt (se não existir)
- [ ] `pytest-cov` instalado para coverage reports
- [ ] `pytest-asyncio` instalado para testes assíncronos
- [ ] Arquivo `pytest.ini` ou configuração em `pyproject.toml` criado
- [ ] Coverage threshold configurado para 70%
- [ ] Script `pytest` funciona sem erros
- [ ] Script `pytest --cov` gera relatório de coverage
- [ ] Relatório HTML gerado em `htmlcov/`

### Frontend (jest)
- [ ] `jest` adicionado em `frontend/package.json` devDependencies
- [ ] `@testing-library/react` e `@testing-library/jest-dom` instalados
- [ ] Arquivo `jest.config.js` criado
- [ ] Scripts `npm test` e `npm run test:coverage` funcionando
- [ ] Coverage threshold configurado para 60%

### Documentação
- [ ] CLAUDE.md atualizado com comandos de teste
- [ ] Exemplo de teste básico criado para backend
- [ ] Exemplo de teste básico criado para frontend (quando Next.js configurado)

## 🛠️ Tarefas de Implementação

### 1. Backend (pytest)

Criar `backend/pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=70
asyncio_mode = auto
```

Verificar `requirements.txt` contém:
```
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-asyncio>=0.23.0
```

### 2. Frontend (jest)

Adicionar em `frontend/package.json`:
```json
{
  "devDependencies": {
    "jest": "^29.7.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "jest-environment-jsdom": "^29.7.0"
  },
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

Criar `frontend/jest.config.js`:
```js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60,
    },
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
```

### 3. Exemplo de teste

Criar `backend/tests/test_example.py`:
```python
"""Example test to verify pytest setup."""

def test_example():
    """Basic test to verify pytest is working."""
    assert 1 + 1 == 2
```

### 4. Atualizar CLAUDE.md

Adicionar seção sobre execução de testes na linha apropriada.

## 🔗 Dependências

**Bloqueado por:** Nenhum
**Bloqueia:** Nenhum (mas fundamental para qualidade)

## 📝 Notas

- Esta issue foi identificada durante auditoria PRD
- CLAUDE.md menciona pytest/jest mas não havia issue para setup inicial
- Coverage thresholds são requisitos do PRD
- Testes existentes em `backend/tests/` devem continuar funcionando

## ✨ Definição de Pronto

- [ ] Todos os acceptance criteria cumpridos
- [ ] Testes existentes passando com nova configuração
- [ ] Coverage reports gerando corretamente
- [ ] Documentação atualizada
- [ ] PR criado e merged
