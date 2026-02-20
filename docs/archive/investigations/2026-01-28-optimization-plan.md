# Plano de Otimizacao: POC Demo-Ready

**Data:** 2026-01-28
**Objetivo:** Corrigir busca e melhorar UX para demonstracao do POC
**Meta:** "Sem batom na cueca" - demonstracao profissional e funcional

---

## Workflow de Otimizacao

```
FASE 1: Fix Critico (Backend)     FASE 2: UX Upgrade (Frontend)
        @dev + @qa                       @ux + @dev + @qa
            |                                   |
            v                                   v
+-------------------+               +-------------------+
| 1. Remover filtro |               | 4. Progress Steps |
|    de prazo       |               |    com etapas     |
+-------------------+               +-------------------+
            |                                   |
            v                                   v
+-------------------+               +-------------------+
| 2. Ajustar faixa  |               | 5. Empty State    |
|    de valor       |               |    amigavel       |
+-------------------+               +-------------------+
            |                                   |
            v                                   v
+-------------------+               +-------------------+
| 3. Adicionar logs |               | 6. Loading com    |
|    de estatisticas|               |    tempo estimado |
+-------------------+               +-------------------+
            |                                   |
            +-----------> MERGE <--------------+
                           |
                           v
                 +-------------------+
                 | 7. Testes E2E     |
                 |    @qa            |
                 +-------------------+
                           |
                           v
                 +-------------------+
                 | 8. Demo Ready!    |
                 +-------------------+
```

---

## FASE 1: Correcoes Backend

### Task 1.1: Remover Filtro de Prazo

**Arquivo:** `backend/filter.py`
**Linha:** 240-253
**Agente:** @dev

**Antes:**
```python
# 4. Deadline Filter (check if bid is still open)
data_abertura_str = licitacao.get("dataAberturaProposta")
if data_abertura_str:
    try:
        data_abertura = datetime.fromisoformat(
            data_abertura_str.replace("Z", "+00:00")
        )
        if data_abertura < datetime.now(data_abertura.tzinfo):
            return False, "Prazo encerrado"
    except (ValueError, TypeError):
        pass
```

**Depois:**
```python
# 4. Deadline Filter - REMOVIDO
# O campo dataAberturaProposta representa a data de ABERTURA, nao o prazo final.
# Licitacoes historicas sao validas para analise e planejamento.
# Para filtrar por prazo, seria necessario usar dataFimReceberPropostas.

# TODO: Implementar filtro opcional por dataFimReceberPropostas quando disponivel
# if include_closed is False:
#     data_fim = licitacao.get("dataFimReceberPropostas")
#     if data_fim and parse_date(data_fim) < now:
#         return False, "Prazo encerrado"
```

**Testes:** `backend/tests/test_filter.py`
```python
def test_filter_accepts_historical_bids():
    """Licitacoes com data passada devem ser aceitas."""
    yesterday = (datetime.now() - timedelta(days=1)).isoformat() + "Z"
    bid = {
        "uf": "SP",
        "valorTotalEstimado": 100000.0,
        "objetoCompra": "Aquisição de uniformes escolares",
        "dataAberturaProposta": yesterday
    }
    aprovada, motivo = filter_licitacao(bid, {"SP"})
    assert aprovada is True
```

---

### Task 1.2: Ajustar Faixa de Valor

**Arquivo:** `backend/main.py`
**Linhas:** 184-185
**Agente:** @dev

**Antes:**
```python
valor_min=50_000.0,
valor_max=5_000_000.0,
```

**Depois:**
```python
valor_min=10_000.0,    # Incluir licitacoes menores (municipios pequenos)
valor_max=10_000_000.0, # Incluir licitacoes maiores
```

**Alternativa (Configuravel):**
```python
# Via request ou env vars
valor_min = request.valor_min or float(os.getenv("FILTER_VALOR_MIN", 10_000))
valor_max = request.valor_max or float(os.getenv("FILTER_VALOR_MAX", 10_000_000))
```

---

### Task 1.3: Adicionar Logging de Estatisticas

**Arquivo:** `backend/main.py`
**Agente:** @dev

**Adicionar no endpoint /buscar:**
```python
@app.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(request: BuscaRequest):
    start_time = time.time()

    # 1. Fetch
    logger.info(f"Iniciando busca: UFs={request.ufs}, periodo={request.data_inicial} a {request.data_final}")

    licitacoes_raw = list(client.fetch_all(...))
    fetch_time = time.time() - start_time
    logger.info(f"PNCP retornou {len(licitacoes_raw)} registros em {fetch_time:.1f}s")

    # 2. Filter
    filter_start = time.time()
    licitacoes_filtradas, stats = filter_batch(...)
    filter_time = time.time() - filter_start

    # Log detalhado de estatisticas
    logger.info(f"Filtragem em {filter_time:.1f}s:")
    logger.info(f"  - Total processadas: {stats['total']}")
    logger.info(f"  - Aprovadas: {stats['aprovadas']}")
    logger.info(f"  - Rejeitadas UF: {stats['rejeitadas_uf']}")
    logger.info(f"  - Rejeitadas Valor: {stats['rejeitadas_valor']}")
    logger.info(f"  - Rejeitadas Keyword: {stats['rejeitadas_keyword']}")
    logger.info(f"  - Rejeitadas Prazo: {stats['rejeitadas_prazo']}")

    # Incluir stats na response para frontend
    # ...
```

---

## FASE 2: Melhorias Frontend

### Task 2.1: Progress Steps Component

**Arquivo:** `frontend/app/page.tsx`
**Agente:** @ux + @dev

**Novo componente:**
```tsx
interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed';
}

function ProgressSteps({ steps }: { steps: ProgressStep[] }) {
  return (
    <div className="space-y-3">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center gap-3">
          {/* Status indicator */}
          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold
            ${step.status === 'completed' ? 'bg-green-600 text-white' : ''}
            ${step.status === 'active' ? 'bg-green-600 text-white animate-pulse' : ''}
            ${step.status === 'pending' ? 'bg-gray-300 dark:bg-gray-600 text-gray-500' : ''}
          `}>
            {step.status === 'completed' ? '✓' : index + 1}
          </div>

          {/* Label */}
          <span className={`text-base
            ${step.status === 'active' ? 'font-semibold text-green-700 dark:text-green-400' : ''}
            ${step.status === 'completed' ? 'text-gray-600 dark:text-gray-400' : ''}
            ${step.status === 'pending' ? 'text-gray-400 dark:text-gray-500' : ''}
          `}>
            {step.label}
          </span>
        </div>
      ))}
    </div>
  );
}
```

**Uso no loading state:**
```tsx
{loading && (
  <div className="mt-8 p-6 bg-gray-100 dark:bg-gray-800 rounded-lg" aria-live="polite">
    <ProgressSteps steps={[
      { id: 'fetch', label: 'Consultando PNCP...', status: loadingStep >= 1 ? (loadingStep > 1 ? 'completed' : 'active') : 'pending' },
      { id: 'filter', label: 'Filtrando resultados', status: loadingStep >= 2 ? (loadingStep > 2 ? 'completed' : 'active') : 'pending' },
      { id: 'llm', label: 'Gerando resumo com IA', status: loadingStep >= 3 ? (loadingStep > 3 ? 'completed' : 'active') : 'pending' },
      { id: 'excel', label: 'Preparando Excel', status: loadingStep >= 4 ? 'completed' : 'pending' },
    ]} />

    <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
      Tempo estimado: ~30-60 segundos
    </div>
  </div>
)}
```

---

### Task 2.2: Empty State Component

**Arquivo:** `frontend/app/page.tsx`
**Agente:** @ux + @dev

```tsx
function EmptyState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mt-8 p-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl text-center">
      {/* Icon */}
      <svg className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>

      <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
        Nenhuma licitacao encontrada
      </h3>

      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        Nao encontramos licitacoes de uniformes com os criterios selecionados.
      </p>

      <div className="text-left max-w-sm mx-auto mb-6">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sugestoes:</p>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>• Amplie o periodo de busca (maximo 30 dias)</li>
          <li>• Selecione mais estados</li>
          <li>• Tente datas mais recentes</li>
        </ul>
      </div>

      <button
        onClick={onRetry}
        className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
      >
        Ajustar busca
      </button>
    </div>
  );
}
```

**Uso:**
```tsx
{result && result.resumo.total_oportunidades === 0 && (
  <EmptyState onRetry={() => window.scrollTo({ top: 0, behavior: 'smooth' })} />
)}
```

---

### Task 2.3: Loading com Tempo Estimado

**Backend support (streaming/SSE):**

Para feedback em tempo real, implementar Server-Sent Events:

```python
# backend/main.py
@app.get("/buscar-stream")
async def buscar_licitacoes_stream(
    ufs: str,  # comma-separated
    data_inicial: str,
    data_final: str
):
    async def event_generator():
        # Step 1: Fetch
        yield f"data: {json.dumps({'step': 1, 'message': 'Consultando PNCP...'})}\n\n"

        licitacoes = list(client.fetch_all(...))
        yield f"data: {json.dumps({'step': 2, 'message': 'Filtrando resultados...', 'raw_count': len(licitacoes)})}\n\n"

        # Step 2: Filter
        filtradas, stats = filter_batch(...)
        yield f"data: {json.dumps({'step': 3, 'message': 'Gerando resumo IA...', 'filtered_count': len(filtradas)})}\n\n"

        # Step 3: LLM
        resumo = generate_summary(filtradas)
        yield f"data: {json.dumps({'step': 4, 'message': 'Preparando Excel...', 'summary': resumo})}\n\n"

        # Step 4: Excel
        excel = generate_excel(filtradas)
        yield f"data: {json.dumps({'step': 5, 'message': 'Concluido!', 'download_id': excel.id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Frontend consumption:**
```tsx
const eventSource = new EventSource(`/api/buscar-stream?ufs=${ufs.join(',')}&...`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setLoadingStep(data.step);
  setLoadingMessage(data.message);

  if (data.step === 5) {
    eventSource.close();
    setResult(data);
    setLoading(false);
  }
};
```

---

## FASE 3: Testes E2E

### Cenarios para Demo

| # | Cenario | Esperado | Agente |
|---|---------|----------|--------|
| 1 | Busca SP, ultimos 7 dias | > 0 resultados | @qa |
| 2 | Busca todos UFs, 7 dias | > 10 resultados | @qa |
| 3 | Busca sem resultados (UF sem licitacoes) | Empty state amigavel | @qa |
| 4 | Loading longo | Progress steps visiveis | @qa |
| 5 | Download Excel | Arquivo gerado corretamente | @qa |

---

## Cronograma de Implementacao

### Sprint 1: Fix Critico (2-4 horas)

| Task | Responsavel | Tempo | Dependencia |
|------|-------------|-------|-------------|
| 1.1 Remover filtro prazo | @dev | 30min | - |
| 1.2 Ajustar faixa valor | @dev | 15min | - |
| 1.3 Adicionar logs | @dev | 30min | - |
| Testes unitarios | @qa | 1h | 1.1, 1.2 |
| Teste integracao PNCP | @qa | 30min | 1.1-1.3 |

### Sprint 2: UX Upgrade (4-6 horas)

| Task | Responsavel | Tempo | Dependencia |
|------|-------------|-------|-------------|
| 2.1 Progress Steps | @ux + @dev | 2h | - |
| 2.2 Empty State | @ux + @dev | 1h | - |
| 2.3 SSE (opcional) | @dev | 2h | 2.1 |
| Testes E2E | @qa | 1h | 2.1, 2.2 |

### Sprint 3: Polish (1-2 horas)

| Task | Responsavel | Tempo | Dependencia |
|------|-------------|-------|-------------|
| Revisao geral | @architect | 30min | Tudo |
| Demo dry-run | Todos | 30min | Tudo |
| Documentacao | @dev | 30min | Tudo |

---

## Checklist Demo-Ready

### Backend
- [ ] Filtro de prazo removido
- [ ] Faixa de valor ajustada (R$ 10k - R$ 10M)
- [ ] Logs de estatisticas implementados
- [ ] Testes passando (70%+ coverage)
- [ ] API retornando resultados para busca Brasil

### Frontend
- [ ] Progress Steps implementado
- [ ] Empty State implementado
- [ ] Loading com tempo estimado
- [ ] Responsivo (mobile-friendly)
- [ ] Dark mode funcionando

### Qualidade
- [ ] Testes E2E passando
- [ ] Tempo de resposta < 60s
- [ ] Sem erros no console
- [ ] Download Excel funcionando

### Demo
- [ ] Dados de exemplo preparados
- [ ] Script de demonstracao pronto
- [ ] Fallback manual documentado

---

## Comandos para Execucao

```bash
# Backend
cd backend
pytest --cov  # Verificar testes
uvicorn main:app --reload  # Rodar servidor

# Frontend
cd frontend
npm test  # Testes
npm run dev  # Servidor dev

# Demo
# 1. Abrir http://localhost:3000
# 2. Selecionar SP, RJ, MG
# 3. Ultimos 7 dias
# 4. Clicar "Buscar"
# 5. Observar progress steps
# 6. Ver resultados
# 7. Download Excel
```

---

## Contato

| Agente | Responsabilidade |
|--------|------------------|
| @dev (James) | Implementacao backend e frontend |
| @qa (Quinn) | Testes e validacao |
| @ux (Uma) | Design de componentes |
| @architect (Aria) | Revisao tecnica |
| @pm (Morgan) | Acompanhamento geral |

