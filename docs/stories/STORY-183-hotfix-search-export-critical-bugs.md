# STORY-183: HOTFIX - Correção de Bugs Críticos em Busca e Exportação

**Status:** 🚨 Em Execução (P0 - Critical)
**Prioridade:** P0 - Crítico (bloqueando usuários)
**Estimativa:** 8 story points (1 sprint de hotfix - 1.5h)
**Tipo:** Bugfix (Hotfix)
**Épico:** Estabilidade e Confiabilidade
**Dependências:** Nenhuma
**Aprovado por:** @pm (Morgan) + Admin (Tiago Sasaki)
**Squad Executora:** search-export-bugfix-squad

---

## 🚨 Contexto de Emergência

### Situação Crítica Relatada

**Data do Incidente:** 2026-02-10
**Reportado por:** Usuário Admin (Tiago Sasaki)
**Severidade:** P0 (Critical) - 2 funcionalidades core bloqueadas

### Bug #1: Busca Retornando Apenas 2 Resultados

**Comportamento Esperado:**
- Usuário seleciona: todos os 27 estados + todas esferas + todas modalidades (Lei 14.133)
- Período: 01/jan/2026 - 10/fev/2026 (41 dias)
- Setor: Engenharia e Construção
- **Resultado Esperado:** Centenas ou milhares de licitações

**Comportamento Atual:**
- **Resultado:** Apenas 2 licitações retornadas

**Impacto:**
- ❌ Usuários não conseguem realizar buscas amplas
- ❌ Dados estão incompletos e não confiáveis
- ❌ Usuários podem cancelar assinaturas por perda de confiança
- ❌ Funcionalidade core do produto comprometida

---

### Bug #2: Exportação Google Sheets - HTTP 404

**Comportamento Esperado:**
- Usuário clica em "Exportar para Google Sheets"
- Fluxo OAuth completa (se necessário)
- Planilha é criada e aberta em nova aba

**Comportamento Atual:**
- **Erro:** "Falha ao exportar para Google Sheets - Erro HTTP 404"

**Impacto:**
- ❌ Feature premium (STORY-180) completamente quebrada
- ❌ Usuários pagantes não conseguem usar funcionalidade vendida
- ❌ Possível violação de SLA/expectativas de produto
- ❌ Perda de produtividade para usuários que dependem de Google Sheets

---

## 🎯 Objetivos

### Objetivo Principal

Restaurar funcionalidade completa de busca e exportação Google Sheets, garantindo que:
1. Buscas amplas retornem todos os resultados disponíveis (sem limite artificial)
2. Exportação para Google Sheets funcione sem erros 404

### Objetivos Secundários

1. Adicionar logging detalhado para detectar futuros problemas de paginação
2. Implementar warnings quando limites de paginação forem atingidos
3. Validar que correções não introduzem regressões
4. Documentar causa raiz para prevenir recorrência

---

## 🔍 Root Cause Analysis (RCA)

### Bug #1: Search Pagination Limit - CAUSA RAIZ IDENTIFICADA ✅

**Arquivo Afetado:** `backend/pncp_client.py:461`

**Código Problemático:**
```python
def _fetch_by_uf(
    self,
    data_inicial: str,
    data_final: str,
    modalidade: int,
    uf: str | None,
    on_progress: Callable[[int, int, int], None] | None,
    max_pages: int = 50,  # ← LIMITE MUITO BAIXO!
) -> Generator[Dict[str, Any], None, None]:
```

**Análise Técnica:**

1. **Limite Atual:**
   - `max_pages = 50` páginas
   - API PNCP retorna 20 itens por página
   - **Total máximo:** 50 × 20 = **1.000 registros** por combinação UF+modalidade

2. **Combinações Possíveis:**
   - 27 UFs × 8 modalidades (Lei 14.133) = **216 combinações**
   - Busca ampla deveria processar TODAS as 216 combinações

3. **Problema Identificado:**
   - Se QUALQUER combinação UF+modalidade tem > 1000 registros, resultados são truncados
   - Com timeout de 4 min, apenas algumas UFs são processadas antes de interrupção
   - Resultado: Apenas 2 licitações (possivelmente de 1-2 UFs antes de timeout)

4. **Por Que Só 2 Resultados?**
   - **Hipótese 1:** Busca paralela (`buscar_todas_ufs_paralelo`) falha silenciosamente
   - **Hipótese 2:** Timeout de 4 min atinge antes de completar todas UFs
   - **Hipótese 3:** Primeiras UFs atingem `max_pages=50` e param prematuramente

**Evidências:**
- Código fonte mostra `max_pages=50` em `pncp_client.py:461`
- Comentário no código diz "Increased from 10 to 50" (já foi aumentado antes!)
- Logs (se disponíveis) devem mostrar "MAX_PAGES ATINGIDO" para múltiplas UFs

---

### Bug #2: Export HTTP 404 - DIAGNÓSTICO PENDENTE ⏳

**Arquivo Afetado:** `backend/routes/export_sheets.py`, `backend/main.py`

**Análise Inicial:**

1. **Código Parece Correto:**
   - ✅ Rota definida: `@router.post("/google-sheets")`
   - ✅ Router registrado: `app.include_router(export_sheets_router)` (linha 99)
   - ✅ Prefixo correto: `router = APIRouter(prefix="/api/export")`
   - ✅ URL esperada: `/api/export/google-sheets`
   - ✅ Frontend chama: `fetch('/api/export/google-sheets')` (linha 76)

2. **Possíveis Causas:**
   - **Hipótese A:** Backend não iniciado completamente quando frontend faz request
   - **Hipótese B:** CORS bloqueando OPTIONS preflight, aparecendo como 404
   - **Hipótese C:** Prefixo duplicado (`/api/api/export`) devido a configuração FastAPI
   - **Hipótese D:** Proxy/nginx configurado incorretamente
   - **Hipótese E:** Rota não carregada em runtime apesar de código correto

**Próximo Passo:**
- Executar `squads/search-export-bugfix-squad/tools/quick-diagnostic.sh`
- Confirmar causa raiz exata antes de implementar correção

---

## ✅ Acceptance Criteria (Critérios de Aceitação)

### AC1: Busca Ampla Funciona Corretamente

**Given:** Usuário está autenticado e na página de busca
**When:** Usuário seleciona:
- UFs: Todos os 27 estados
- Esferas: Estadual, Municipal, Federal
- Modalidades: Todas (1-8, Lei 14.133)
- Data: 01/01/2026 - 10/02/2026
- Setor: Engenharia e Construção

**Then:**
- [ ] Busca retorna **> 100 resultados** (não apenas 2)
- [ ] Busca completa em **< 4 minutos**
- [ ] Logs mostram **todas as 27 UFs** foram processadas
- [ ] Logs mostram **todas as 8 modalidades** foram processadas
- [ ] Se `max_pages` for atingido, **warning é logado** indicando possível incompletude
- [ ] Sem erros ou timeouts

---

### AC2: Exportação Google Sheets Funciona

**Given:** Usuário está autenticado e possui resultados de busca
**When:** Usuário clica em "Exportar para Google Sheets"

**Then:**
- [ ] **NÃO retorna HTTP 404**
- [ ] Se usuário não tem OAuth: Redireciona para fluxo OAuth (esperado)
- [ ] Se usuário tem OAuth válido: Retorna **HTTP 200**
- [ ] Response contém `spreadsheet_url` válida
- [ ] Planilha abre corretamente no Google Sheets
- [ ] Todas as linhas são exportadas (não truncadas)
- [ ] Latência **< 10 segundos** para 1000 linhas

---

### AC3: Logging e Observabilidade

**Given:** Sistema está rodando em produção
**When:** Qualquer busca ou exportação é executada

**Then:**
- [ ] Logs mostram número de UFs processadas vs esperado
- [ ] Logs mostram número de modalidades processadas por UF
- [ ] Logs mostram tempo total de busca
- [ ] Logs mostram contagem de registros por UF+modalidade
- [ ] **Warning** é logado se `max_pages` for atingido
- [ ] Erros de busca paralela são logados (não silenciosos)
- [ ] Erros de exportação incluem stack trace completo

---

### AC4: Testes de Regressão Passam

**Given:** Correções foram implementadas
**When:** Suite de testes é executada

**Then:**
- [ ] Testes unitários de `pncp_client.py` passam
- [ ] Testes de integração de `/api/buscar` passam
- [ ] Testes E2E de busca passam (Playwright)
- [ ] Testes de exportação Google Sheets passam
- [ ] Nenhum teste existente quebrou (zero regressões)

---

### AC5: Performance Não Degradou

**Given:** Correções foram implementadas
**When:** Busca ampla é executada (27 UFs, 8 modalidades)

**Then:**
- [ ] Tempo de execução **< 4 minutos** (mesmo limite atual)
- [ ] Uso de memória não aumentou significativamente
- [ ] Número de requests à API PNCP não aumentou (mesma lógica de paginação)
- [ ] Frontend permanece responsivo durante busca

---

## 📋 Technical Implementation Plan

### Fase 1: Diagnóstico e Confirmação (15 min)

**Task 1.1: Executar Script de Diagnóstico Automático**
- [ ] Rodar `bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh`
- [ ] Confirmar valor de `max_pages` (deve ser 50)
- [ ] Confirmar se rota `/api/export/google-sheets` retorna 404
- [ ] Verificar logs do backend para erros silenciosos

**Task 1.2: Reproduzir Bugs Localmente**
- [ ] Reproduzir busca ampla (todos UFs + todas modalidades)
- [ ] Confirmar apenas 2 resultados retornados
- [ ] Tentar exportação e confirmar HTTP 404
- [ ] Capturar screenshots e logs como evidência

**Deliverables:**
- ✅ Root cause confirmada para ambos bugs
- ✅ Evidências documentadas (logs, screenshots)
- ✅ Plano de correção técnica finalizado

---

### Fase 2: Implementação das Correções (45 min)

#### **Correção 2.1: Bug de Busca (Pagination Limit)**

**Arquivo:** `backend/pncp_client.py`

**Mudanças:**

1. **Aumentar `max_pages` (Linha 461)**
   ```python
   # ANTES:
   max_pages: int = 50,  # 1000 registros por UF+modalidade

   # DEPOIS:
   max_pages: int = 500,  # 10.000 registros por UF+modalidade
   ```

2. **Adicionar Warning de Limite Atingido (Linha ~485)**
   ```python
   while pagina <= max_pages:
       # ... código existente de fetch ...

       if not data.get("temProximaPagina"):
           break

       # NOVO: Warning se max_pages for atingido
       if pagina >= max_pages and data.get("temProximaPagina"):
           logger.warning(
               f"⚠️ MAX_PAGES ({max_pages}) ATINGIDO! "
               f"UF={uf or 'ALL'}, modalidade={modalidade}. "
               f"Resultados podem estar incompletos. "
               f"Considere aumentar max_pages ou otimizar filtros."
           )

       pagina += 1
   ```

3. **Adicionar Logging Detalhado de Progresso (Linha ~495)**
   ```python
   # Após loop de paginação
   logger.info(
       f"✅ Fetch completo para UF={uf or 'ALL'}, modalidade={modalidade}: "
       f"{items_fetched} itens em {pagina-1} páginas"
   )
   ```

4. **Melhorar Error Handling em `buscar_todas_ufs_paralelo`**
   ```python
   # Em backend/main.py ou pncp_client.py (onde está definida)

   try:
       return await buscar_todas_ufs_paralelo(...)
   except Exception as e:
       logger.error(
           f"❌ Busca paralela falhou: {type(e).__name__}: {str(e)}",
           exc_info=True
       )
       # Fallback para busca sequencial
       client = PNCPClient()
       return list(client.fetch_all(...))
   ```

**Checklist de Implementação:**
- [ ] Aumentar `max_pages` de 50 para 500
- [ ] Adicionar warning quando `max_pages` for atingido
- [ ] Adicionar logging de progresso por UF+modalidade
- [ ] Melhorar error handling em busca paralela
- [ ] Testar com busca ampla (27 UFs)
- [ ] Verificar logs mostram todas UFs processadas
- [ ] Confirmar > 100 resultados retornados

---

#### **Correção 2.2: Bug de Exportação (HTTP 404)**

**IMPORTANTE:** Correção depende do diagnóstico (Fase 1)

**Cenário A: Backend Não Iniciado / Timing Issue**

**Solução:** Adicionar health check no frontend antes de renderizar botão

```typescript
// frontend/components/GoogleSheetsExportButton.tsx

const [backendReady, setBackendReady] = useState(false);

useEffect(() => {
  // Check backend health on mount
  fetch('/api/health')
    .then(res => res.ok && setBackendReady(true))
    .catch(() => setBackendReady(false));
}, []);

// Disable button if backend not ready
disabled={disabled || exporting || !backendReady || licitacoes.length === 0}
```

---

**Cenário B: Prefixo Duplicado (/api/api/export)**

**Solução:** Verificar e corrigir prefixo em `main.py`

```python
# backend/main.py

# VERIFICAR SE TEM:
app = FastAPI(
    title="SmartLic API",
    prefix="/api"  # ← Se tiver isso, REMOVER!
)

# DEVE SER:
app = FastAPI(
    title="SmartLic API",
    # Sem prefix global
)
```

---

**Cenário C: CORS Bloqueando OPTIONS**

**Solução:** Garantir CORS permite `/api/export/*`

```python
# backend/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://smartlic.com.br"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

---

**Cenário D: Rota Não Carregada em Runtime**

**Solução:** Verificar ordem de imports e includes

```python
# backend/main.py

# IMPORTANTE: Imports devem estar ANTES de app.include_router
from routes.export_sheets import router as export_sheets_router

# ...

# Include deve estar DEPOIS de CORS middleware
app.add_middleware(CORSMiddleware, ...)
app.include_router(export_sheets_router)  # ← Verificar está aqui
```

---

### Fase 3: Testes e Validação (30 min)

#### **Teste 3.1: Busca Ampla (Crítico)**

```bash
# Terminal 1: Iniciar backend com logging
cd backend
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --port 8000

# Terminal 2: Executar busca via curl
curl -X POST http://localhost:8000/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "ufs": ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"],
    "esferas": ["estadual", "municipal", "federal"],
    "modalidades": [1,2,3,4,5,6,7,8],
    "data_inicial": "2026-01-01",
    "data_final": "2026-02-10",
    "setor_id": "engenharia_construcao"
  }'

# Validações:
# ✅ Resposta tem total_filtrado > 100
# ✅ Busca completa em < 4 min
# ✅ Logs mostram todas 27 UFs processadas
# ✅ Logs mostram progresso de cada UF+modalidade
```

**Checklist:**
- [ ] Busca retorna > 100 resultados
- [ ] Tempo < 4 minutos
- [ ] Logs mostram todas UFs processadas
- [ ] Nenhum erro no console

---

#### **Teste 3.2: Exportação Google Sheets**

```bash
# Testar endpoint diretamente
curl -i -X POST http://localhost:8000/api/export/google-sheets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "licitacoes": [],
    "title": "Test Export",
    "mode": "create"
  }'

# Esperado:
# - HTTP 200 (ou 401 se sem OAuth, mas NÃO 404!)
# - Response JSON com spreadsheet_url
```

**Checklist:**
- [ ] Endpoint retorna 200 (não 404)
- [ ] Spreadsheet URL é retornada
- [ ] Planilha abre no Google Sheets
- [ ] Dados estão completos

---

#### **Teste 3.3: Testes Automatizados**

```bash
# Backend tests
cd backend
pytest tests/test_api_buscar.py -v
pytest tests/test_routes_export_sheets.py -v
pytest tests/test_pncp_client.py -v

# Frontend tests
cd frontend
npm test -- GoogleSheetsExportButton.test.tsx
```

**Checklist:**
- [ ] Todos os testes unitários passam
- [ ] Todos os testes de integração passam
- [ ] Nenhuma regressão detectada

---

#### **Teste 3.4: E2E Testing (Manual)**

```bash
# Iniciar ambiente completo
cd backend && uvicorn main:app --reload &
cd frontend && npm run dev &
```

**Cenário 1: Busca Ampla**
1. Abrir http://localhost:3000/buscar
2. Selecionar todos os estados (27)
3. Selecionar todas as modalidades
4. Data: 01/01/2026 - 10/02/2026
5. Setor: Engenharia e Construção
6. Clicar "Buscar"
7. **Validar:** > 100 resultados retornados

**Cenário 2: Exportação**
1. Com resultados na tela, clicar "Exportar para Google Sheets"
2. Se pedido, completar OAuth
3. **Validar:** Planilha abre em nova aba
4. **Validar:** Dados estão completos

**Checklist:**
- [ ] Busca ampla funciona (> 100 resultados)
- [ ] Exportação funciona (sem 404)
- [ ] Planilha criada corretamente
- [ ] UX é fluida (sem erros visíveis)

---

### Fase 4: Deploy e Monitoring (15 min)

#### **Passo 4.1: Code Review e Merge**

```bash
# Criar hotfix branch
git checkout -b hotfix/STORY-183-search-export-bugs

# Adicionar mudanças
git add backend/pncp_client.py backend/main.py

# Commit com mensagem detalhada
git commit -m "fix(P0): resolve search pagination and export 404 bugs [STORY-183]

Bug #1: Search Pagination Limit
- Increase max_pages from 50 to 500 (10,000 records per UF+modality)
- Add warning when max_pages is reached
- Add detailed logging for UF+modality progress
- Improve error handling in parallel fetch

Bug #2: Google Sheets Export HTTP 404
- [Based on diagnostic: add specific fix here]
- Fix route registration/CORS/timing issue

Acceptance Criteria:
✅ AC1: Search returns > 100 results for wide params
✅ AC2: Export returns HTTP 200 (not 404)
✅ AC3: Detailed logging implemented
✅ AC4: All regression tests pass
✅ AC5: Performance < 4 min maintained

Testing:
- Manual E2E testing: PASS
- Unit tests: PASS
- Integration tests: PASS

Fixes: [Link to bug report]
Squad: search-export-bugfix-squad

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push para revisão
git push origin hotfix/STORY-183-search-export-bugs
```

**Checklist:**
- [ ] PR criado com descrição detalhada
- [ ] Todos os checks CI/CD passam
- [ ] Code review aprovado por senior engineer
- [ ] Testes de staging validados

---

#### **Passo 4.2: Deploy em Produção**

```bash
# Merge para main
git checkout main
git merge hotfix/STORY-183-search-export-bugs
git push origin main

# Tag da versão hotfix
git tag -a v1.8.1-hotfix -m "Hotfix: Search pagination and export bugs"
git push origin v1.8.1-hotfix

# Deploy automático (se CI/CD configurado)
# Ou deploy manual:
# - Vercel: git push vercel main
# - Backend: Redeployar FastAPI app
```

**Checklist:**
- [ ] Deploy em produção completo
- [ ] Smoke tests em produção passam
- [ ] Monitoring dashboards não mostram erros
- [ ] Logs de produção confirmam correções ativas

---

#### **Passo 4.3: Validação Pós-Deploy**

**Validar em Produção:**

1. **Busca Ampla:**
   - Fazer busca com todos os estados
   - Confirmar > 100 resultados
   - Verificar tempo < 4 min

2. **Exportação:**
   - Clicar "Exportar para Google Sheets"
   - Confirmar planilha criada (sem 404)

3. **Logs:**
   - Verificar logs mostram todas UFs processadas
   - Confirmar warnings de max_pages (se aplicável)

**Checklist:**
- [ ] Busca ampla funciona em produção
- [ ] Exportação funciona em produção
- [ ] Logs confirmam correções ativas
- [ ] Nenhum erro novo introduzido

---

## 📊 Success Metrics (Métricas de Sucesso)

### Métricas Técnicas

| Métrica | Target | Medição |
|---------|--------|---------|
| **Search Success Rate** | > 99% | % de buscas retornando resultados completos |
| **Search Coverage** | 100% | % de UFs+modalidades processadas vs esperado |
| **Search Performance** | < 4 min | Tempo total para busca com 27 UFs |
| **Export Success Rate** | > 99% | % de exportações completando sem 404 |
| **Export Latency** | < 10s | Tempo de resposta da API de exportação |
| **Regression Rate** | 0% | Número de testes existentes quebrados |

### Métricas de Negócio

| Métrica | Target | Medição |
|---------|--------|---------|
| **User Satisfaction** | Nenhuma reclamação | Tickets de suporte sobre esses bugs |
| **Feature Usage** | Sem redução | Número de exportações/dia mantido |
| **Churn Prevention** | 0 cancelamentos | Cancelamentos atribuídos a esses bugs |

---

## 🔄 Rollback Plan (Plano de Reversão)

### Critérios para Rollback

Executar rollback SE qualquer um ocorrer:
- Busca fica **> 5 minutos** (piora significativa de performance)
- Taxa de erro de busca **> 5%**
- Exportação continua com 404
- Qualquer regressão crítica detectada

### Procedimento de Rollback

```bash
# Reverter commit
git revert <commit-hash-hotfix>
git push origin main

# Ou voltar para versão anterior
git checkout v1.8.0
# Redeploy
```

### Post-Rollback

Se rollback for necessário:
1. Investigar causa raiz da falha
2. Ajustar correção em ambiente de desenvolvimento
3. Re-testar extensivamente
4. Re-deploy quando validado

---

## 📁 File List (Arquivos Modificados)

### Backend

- [ ] `backend/pncp_client.py` - Aumentar max_pages, adicionar warnings/logging
- [ ] `backend/main.py` - Melhorar error handling de busca paralela (se necessário)
- [ ] `backend/routes/export_sheets.py` - Correção de 404 (se necessário)
- [ ] `backend/tests/test_pncp_client.py` - Adicionar testes de max_pages
- [ ] `backend/tests/test_api_buscar.py` - Validar busca ampla
- [ ] `backend/tests/test_routes_export_sheets.py` - Validar exportação

### Frontend

- [ ] `frontend/components/GoogleSheetsExportButton.tsx` - Correção de 404 (se necessário)
- [ ] `frontend/__tests__/GoogleSheetsExportButton.test.tsx` - Validar correção

### Documentation

- [ ] `docs/stories/STORY-183-hotfix-search-export-critical-bugs.md` - Esta story
- [ ] `HOTFIX-EXECUTION-REPORT-2026-02-10.md` - Relatório de execução
- [ ] `CHANGELOG.md` - Adicionar entry do hotfix

### Squad Assets

- [ ] `squads/search-export-bugfix-squad/squad.yaml` - Manifest
- [ ] `squads/search-export-bugfix-squad/README.md` - Documentação do squad
- [ ] `squads/search-export-bugfix-squad/tools/quick-diagnostic.sh` - Script de diagnóstico

---

## ⏱️ Timeline e Estimativa

| Fase | Duração | Responsável | Status |
|------|---------|-------------|--------|
| **Diagnóstico** | 15 min | search-specialist, export-specialist | ⏳ Pendente |
| **Implementação** | 45 min | search-specialist, export-specialist | ⏳ Pendente |
| **Testes** | 30 min | qa-validator | ⏳ Pendente |
| **Deploy** | 15 min | DevOps / Admin | ⏳ Pendente |
| **Validação Pós-Deploy** | 10 min | QA + PM | ⏳ Pendente |
| **TOTAL** | **1h55min** | Squad completo | ⏳ Pendente |

---

## 🚨 Risk Assessment (Análise de Riscos)

### Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Aumentar max_pages degrada performance | Baixa | Alto | Monitorar tempo de busca; rollback se > 5min |
| Correção de exportação quebra OAuth | Média | Alto | Testar fluxo OAuth completo antes de deploy |
| Busca paralela continua falhando | Média | Médio | Implementar fallback para busca sequencial |
| Novos bugs introduzidos | Baixa | Alto | Suite completa de testes de regressão |

### Riscos de Negócio

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Usuários já cancelaram assinatura | Alta | Alto | Comunicar correção proativamente |
| Confiança no produto abalada | Alta | Alto | Transparência sobre causa e correção |
| Hotfix não resolve completamente | Baixa | Crítico | Diagnóstico minucioso antes de implementar |

---

## 📞 Stakeholders e Comunicação

### Aprovadores

- ✅ **@pm (Morgan)** - Product Manager - Aprovado
- ✅ **Admin (Tiago Sasaki)** - Product Owner - Aprovado

### Comunicação Pós-Deploy

**Template de Comunicação aos Usuários:**

```
🚀 Correção Implementada - Sistema de Busca e Exportação

Olá!

Identificamos e corrigimos dois bugs críticos no SmartLic:

1. ✅ BUSCA: Buscas amplas agora retornam resultados completos
   - Antes: Apenas 2 resultados para buscas amplas
   - Agora: Todos os resultados disponíveis (sem limite artificial)

2. ✅ EXPORTAÇÃO: Google Sheets Export funcionando
   - Antes: Erro 404 ao exportar
   - Agora: Exportação funciona normalmente

Agradecemos sua paciência e feedback!

Equipe SmartLic
```

---

## 📚 References (Referências)

### Documentação Relacionada

- [HOTFIX Execution Report](../../HOTFIX-EXECUTION-REPORT-2026-02-10.md)
- [Squad Bugfix README](../../squads/search-export-bugfix-squad/README.md)
- [STORY-180: Google Sheets Export](./STORY-180-google-sheets-export.md)
- [Epic: Estabilidade e Confiabilidade](./epic-technical-debt.md)

### Technical References

- [PNCP API Documentation](https://pncp.gov.br/api/docs)
- [FastAPI Routing](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Google Sheets API](https://developers.google.com/sheets/api)

---

## ✅ Definition of Done (DoD)

Esta story está COMPLETA quando:

### Código
- [ ] Todas as mudanças implementadas e testadas
- [ ] Code review aprovado
- [ ] Nenhuma regressão detectada
- [ ] Commits seguem padrão de mensagens

### Testes
- [ ] Testes unitários passam (100%)
- [ ] Testes de integração passam (100%)
- [ ] Testes E2E manuais passam
- [ ] Performance validada (< 4 min)

### Deploy
- [ ] Deploy em produção completo
- [ ] Smoke tests em produção passam
- [ ] Monitoring configurado
- [ ] Rollback plan documentado

### Documentação
- [ ] Story atualizada com resultados
- [ ] CHANGELOG atualizado
- [ ] Squad README atualizado
- [ ] Comunicação aos usuários enviada (se aplicável)

### Validação
- [ ] PM valida correções funcionam
- [ ] Admin (Tiago) confirma bugs resolvidos
- [ ] Nenhum novo ticket de suporte sobre esses bugs

---

## 📝 Execution Log (Log de Execução)

### 2026-02-10 21:30 UTC - Story Criada
- **Ação:** Story STORY-183 criada por @pm (Morgan)
- **Status:** 🚨 Em Execução (P0)
- **Squad:** search-export-bugfix-squad ativado
- **Próximo Passo:** Executar diagnóstico automático

### [A COMPLETAR DURANTE EXECUÇÃO]

---

**Story criada por:** @pm (Morgan - Product Manager)
**Data de Criação:** 2026-02-10 21:45 UTC
**Última Atualização:** 2026-02-10 21:45 UTC
**Squad:** search-export-bugfix-squad
**Epic:** Estabilidade e Confiabilidade

---

— Morgan, planejando o futuro 📊
