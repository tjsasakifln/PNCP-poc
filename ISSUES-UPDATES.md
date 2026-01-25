# 📝 Issues Updates - 100% PRD Coverage

**Data:** 2026-01-24
**Objetivo:** Garantir 100% de cobertura do PRD nas issues

---

## 🆕 NOVAS ISSUES A CRIAR

### Issue #32: Setup Test Frameworks (pytest + jest)

**EPIC:** #2 (Setup e Infraestrutura Base)
**Labels:** `infrastructure`, `testing`, `setup`
**Prioridade:** P1 (Alta)
**Estimativa:** 2 horas

**Descrição:**
Configurar frameworks de teste para backend (pytest) e frontend (jest) conforme especificado em CLAUDE.md e PRD Seção 9.

**Referência PRD:**
- Seção 9 (Dependências)
- CLAUDE.md linhas 39-43, 649

**Acceptance Criteria:**
- [ ] pytest configurado com pytest.ini ou pyproject.toml
- [ ] pytest-cov instalado e configurado para coverage reports
- [ ] pytest-asyncio para testes assíncronos
- [ ] Script `pytest` e `pytest --cov` funcionando
- [ ] jest configurado para frontend (quando Next.js for configurado)
- [ ] Scripts npm test e npm run test:coverage
- [ ] Documentação em CLAUDE.md atualizada com comandos de teste
- [ ] Exemplo de teste básico para cada framework
- [ ] Coverage threshold configurado (70% backend, 60% frontend)

**Tarefas:**
1. Adicionar pytest, pytest-cov, pytest-asyncio em requirements.txt (se ainda não existem)
2. Criar pytest.ini com configurações:
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
   ```
3. Adicionar jest em frontend/package.json
4. Criar jest.config.js para Next.js
5. Atualizar CLAUDE.md com comandos de teste

**Bloqueado Por:** Nenhum

**Bloqueia:** Nenhum (mas fundamental para qualidade)

---

### Issue #33: Frontend Error Boundaries

**EPIC:** #20 (Frontend - Next.js)
**Labels:** `frontend`, `feature`, `error-handling`
**Prioridade:** P1 (Alta)
**Estimativa:** 2 horas

**Descrição:**
Implementar error boundary React conforme estrutura definida no PRD Seção 7.2.

**Referência PRD:**
- Seção 7.2 linha 1187 (`error.tsx` na estrutura de arquivos)

**Acceptance Criteria:**
- [ ] Arquivo `app/error.tsx` criado
- [ ] Error boundary component implementado
- [ ] Fallback UI amigável para erros
- [ ] Botão "Tentar novamente" funcional
- [ ] Erros logados no console (development)
- [ ] Erros reportados para serviço de monitoramento (produção - opcional)
- [ ] Testes para error boundary
- [ ] Documentação no código

**Tarefas:**
1. Criar `frontend/app/error.tsx`:
   ```tsx
   'use client'

   export default function Error({
     error,
     reset,
   }: {
     error: Error & { digest?: string }
     reset: () => void
   }) {
     return (
       <div className="flex flex-col items-center justify-center min-h-screen">
         <h2 className="text-2xl font-bold text-red-600 mb-4">
           Ops! Algo deu errado
         </h2>
         <p className="text-gray-600 mb-4">{error.message}</p>
         <button
           onClick={reset}
           className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
         >
           Tentar novamente
         </button>
       </div>
     )
   }
   ```
2. Adicionar error.tsx à estrutura de pastas
3. Testar com erro simulado
4. Documentar comportamento em CLAUDE.md

**Bloqueado Por:** #21 (Setup Next.js)

**Bloqueia:** Nenhum

---

### Issue #34: Frontend Form Validations

**EPIC:** #20 (Frontend - Next.js)
**Labels:** `frontend`, `feature`, `validation`
**Prioridade:** P1 (Alta)
**Estimativa:** 1 hora

**Descrição:**
Implementar validações client-side para formulário de busca conforme PRD Seção 7.3 linhas 1259-1262.

**Referência PRD:**
- Seção 7.3 linhas 1258-1292 (função `buscar`)
- Validação de UFs: linha 1259-1262
- Validação de datas: implícito no fluxo

**Acceptance Criteria:**
- [ ] Validação: mínimo 1 UF selecionada
- [ ] Validação: data_inicial não pode ser vazia
- [ ] Validação: data_final não pode ser vazia
- [ ] Validação: data_final >= data_inicial
- [ ] Validação: range de datas <= 30 dias (PRD Seção 1.2)
- [ ] Mensagens de erro inline e claras
- [ ] Botão "Buscar" desabilitado se validação falhar
- [ ] Estados de erro limpos ao corrigir
- [ ] Feedback visual nos campos inválidos

**Tarefas:**
1. Adicionar estado de validação em `page.tsx`
2. Implementar validações:
   ```tsx
   const validar = (): string | null => {
     if (ufsSelecionadas.size === 0) {
       return "Selecione pelo menos um estado";
     }

     const inicio = new Date(dataInicial);
     const fim = new Date(dataFinal);

     if (fim < inicio) {
       return "Data final deve ser maior ou igual à data inicial";
     }

     const diffDias = (fim - inicio) / (1000 * 60 * 60 * 24);
     if (diffDias > 30) {
       return "Período máximo de busca é 30 dias";
     }

     return null;
   };
   ```
3. Adicionar componente de erro inline
4. Estilizar campos inválidos com Tailwind
5. Desabilitar botão se validação falhar
6. Testes unitários para validações

**Bloqueado Por:** #22 (Interface seleção UFs) - pode ser implementado junto

**Bloqueia:** Nenhum

---

## ✏️ EDIÇÕES EM ISSUES EXISTENTES

### Issue #8: Implementar paginação automática PNCP

**Mudanças:**

**ADICIONAR à Descrição:**
```markdown
Implementar generator pattern `fetch_all()` conforme PRD Seção 3.2 linhas 351-423.

Este método deve:
- Aceitar lista de UFs e fazer busca por UF (mais eficiente)
- Usar generator pattern para streaming de resultados
- Suportar callback `on_progress(current_page, total_pages, items_so_far)`
- Implementar helper `_fetch_by_uf()` para lógica de paginação
- Respeitar flag `temProximaPagina` da API PNCP
- Logar estatísticas ao final (items fetched, páginas processadas)
```

**ADICIONAR Acceptance Criteria:**
```markdown
**Implementação PRD-Compliant:**
- [ ] Método `fetch_all()` com signature do PRD (linhas 351-369)
- [ ] Parâmetro `ufs: list[str] | None` para filtro opcional
- [ ] Parâmetro `on_progress: callable` para callback de progresso
- [ ] Yield de cada licitação individualmente (generator pattern)
- [ ] Helper `_fetch_by_uf()` para lógica de paginação (linhas 381-423)
- [ ] Loop while True com break em `temProximaPagina == False`
- [ ] Log ao final com `items_fetched` e `pagina`
- [ ] Callback on_progress chamado a cada página processada

**Comportamento:**
- [ ] Se `ufs` fornecida: iterar por cada UF e chamar `_fetch_by_uf()`
- [ ] Se `ufs` é None: chamar `_fetch_by_uf()` uma vez com uf=None
- [ ] Incrementar `pagina` após cada fetch
- [ ] Parar quando `temProximaPagina == False` OU `pagina >= totalPaginas`

**Testes:**
- [ ] Teste: busca com 1 página retorna todos items
- [ ] Teste: busca com múltiplas páginas retorna todos items
- [ ] Teste: callback on_progress é chamado corretamente
- [ ] Teste: múltiplas UFs resulta em chamadas separadas
- [ ] Teste: flag temProximaPagina=False para paginação
```

**ADICIONAR Referência:**
```markdown
**Código de Referência:** PRD.md linhas 351-423 (implementação completa fornecida)
```

---

### Issue #22: Interface seleção UFs e período

**Mudanças:**

**ADICIONAR Acceptance Criteria (Validações):**
```markdown
**Validações Client-Side (PRD 7.3 linhas 1259-1262):**
- [ ] Validar mínimo 1 UF selecionada antes de buscar
- [ ] Validar data_inicial não vazia
- [ ] Validar data_final não vazia
- [ ] Validar data_final >= data_inicial
- [ ] Validar range <= 30 dias (PRD Seção 1.2)
- [ ] Mostrar mensagens de erro inline e claras
- [ ] Desabilitar botão "Buscar" se validação falhar
- [ ] Limpar erros ao corrigir campos
- [ ] Feedback visual em campos inválidos (borda vermelha)
```

**ADICIONAR à Descrição:**
```markdown
**Validações:**
Implementar validações client-side conforme PRD Seção 7.3:
- UFs: mínimo 1 selecionada
- Datas: formato válido, final >= inicial, range <= 30 dias
- Mensagens de erro inline
```

---

## 📊 IMPACTO NAS ESTATÍSTICAS

### Antes (31 issues):
- Total: 31 issues
- Backend: 17 issues
- Frontend: 4 issues
- Infraestrutura: 5 issues
- Integração/Deploy: 5 issues

### Depois (34 issues):
- **Total: 34 issues** (+3)
- **Backend: 17 issues** (sem mudança)
- **Frontend: 6 issues** (+2: #33, #34)
- **Infraestrutura: 6 issues** (+1: #32)
- **Integração/Deploy: 5 issues** (sem mudança)

### Novo Progresso:
- **Issues Completas:** 4/34 (11.8%) - ajustado de 12.9%
- **PRD Coverage:** 100% (era 93%)

---

## 🎯 ORDEM DE EXECUÇÃO ATUALIZADA

### M1: Fundação e Backend Core
**Adicionado:** Issue #32 (Setup Test Frameworks) - 2h

**Nova sequência M1:**
1. ✅ #3, #4, #5 (Setup base)
2. ✅ #7 (Cliente HTTP resiliente)
3. **#32 (Setup Test Frameworks)** ← NOVO, deve ser feito cedo
4. #8 (Paginação) ← ENRIQUECIDO
5. #28 (Rate limiting)
6. #10, #11, #30 (Filtragem)
7. #13, #14, #15 (Saídas)

### M2: Full-Stack Funcional
**Adicionado:** Issues #33, #34 (Error boundaries e validations)

**Nova sequência M2:**
1. #17, #18, #19, #29 (Backend API)
2. #21 (Setup Next.js)
3. **#33 (Error Boundaries)** ← NOVO, deve ser feito logo após #21
4. #22 (Seleção UFs) ← ENRIQUECIDO com validações
5. **#34 (Form Validations)** ← NOVO, pode ser junto com #22
6. #23 (Resultados)
7. #24 (API Routes)

---

## ✅ CHECKLIST DE APLICAÇÃO

- [ ] Criar Issue #32 no GitHub
- [ ] Criar Issue #33 no GitHub
- [ ] Criar Issue #34 no GitHub
- [ ] Editar Issue #8 com detalhes do generator pattern
- [ ] Editar Issue #22 com validações client-side
- [ ] Atualizar ISSUES-ROADMAP.md com novas issues
- [ ] Atualizar ROADMAP.md com novas estatísticas
- [ ] Atualizar estatísticas: 34 issues total, 11.8% completo
- [ ] Commit changes: "feat(roadmap): add 3 issues for 100% PRD coverage"

---

## 📋 RESUMO EXECUTIVO

**Gaps Identificados pela Auditoria:**
1. ✅ Testing frameworks (pytest/jest) - Issue #32
2. ✅ Frontend error boundaries - Issue #33
3. ✅ Frontend form validations - Issue #34

**Issues Enriquecidas:**
1. ✅ Issue #8 - Detalhes do generator pattern do PRD
2. ✅ Issue #22 - Validações client-side explícitas

**Resultado:**
- **PRD Coverage: 93% → 100%**
- **Total Issues: 31 → 34**
- **Progresso: 12.9% → 11.8%** (denominador aumentou)
- **Completude do Plano:** Total

---

**Próximo Passo:** Aplicar mudanças aos arquivos ROADMAP.md e ISSUES-ROADMAP.md, e criar issues no GitHub.
