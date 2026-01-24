# Coding Standards - PNCP POC

## Princípios Gerais

1. **Simplicidade**: Código simples e direto, sem over-engineering
2. **Resiliência**: Tratamento de erros, retry logic, timeouts
3. **Observabilidade**: Logging estruturado, métricas claras
4. **Performance**: Caching, lazy loading, operações assíncronas

## Python (Backend)

### Type Hints
```python
# BOM
def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: set[str],
    valor_min: float = 50_000.0
) -> tuple[bool, str | None]:
    ...

# RUIM - sem type hints
def filter_licitacao(licitacao, ufs, valor_min=50000):
    ...
```

### Error Handling
```python
# BOM - específico e informativo
try:
    response = self.session.get(url, timeout=30)
except requests.exceptions.Timeout:
    logger.warning(f"Timeout após 30s: {url}")
    raise PNCPAPIError("Timeout na API PNCP")

# RUIM - genérico
try:
    response = self.session.get(url)
except Exception as e:
    print(e)
```

### Logging
```python
# BOM - estruturado
logger.info(
    "Licitações filtradas",
    extra={
        "total_raw": len(raw),
        "total_filtered": len(filtered),
        "ufs": list(ufs)
    }
)

# RUIM - string simples
print(f"Filtradas: {len(filtered)}")
```

### Pydantic Models
```python
# BOM - validação completa
class BuscaRequest(BaseModel):
    ufs: list[str] = Field(..., min_length=1)
    data_inicial: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_final: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")

# RUIM - sem validação
class BuscaRequest(BaseModel):
    ufs: list
    data_inicial: str
    data_final: str
```

## TypeScript (Frontend)

### Type Safety
```typescript
// BOM - interfaces bem definidas
interface Resumo {
  resumo_executivo: string;
  total_oportunidades: number;
  valor_total: number;
  destaques: string[];
}

// RUIM - any
const handleResult = (data: any) => {
  setResult(data);
};
```

### React Hooks
```typescript
// BOM - estado tipado
const [result, setResult] = useState<BuscaResult | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// RUIM - estado genérico
const [result, setResult] = useState(null);
```

### Error Handling
```typescript
// BOM - tratamento completo
try {
  const response = await fetch("/api/buscar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.message || "Erro ao buscar");
  }

  const data = await response.json();
  setResult(data);
} catch (e) {
  setError(e instanceof Error ? e.message : "Erro desconhecido");
} finally {
  setLoading(false);
}
```

## Git Workflow

### Commits
```bash
# BOM - descritivo
git commit -m "feat(backend): adicionar retry logic ao PNCP client"
git commit -m "fix(frontend): corrigir validação de datas"

# RUIM - genérico
git commit -m "updates"
git commit -m "fix bug"
```

### Branches
```
main            # Produção
develop         # Desenvolvimento
feature/*       # Novas features
fix/*           # Correções
hotfix/*        # Correções urgentes
```

## Testes

### Coverage Mínimo
- Backend: 70% de cobertura
- Frontend: 60% de cobertura
- Funções críticas: 100% (retry logic, filtros)

### Estrutura de Testes
```
backend/
  tests/
    test_pncp_client.py
    test_filter.py
    test_excel.py
    test_llm.py

frontend/
  __tests__/
    page.test.tsx
    api/
      buscar.test.ts
```

## Performance

### Backend
- Rate limiting: max 10 req/s para PNCP
- Timeout: 30s por request
- Max retries: 5 com exponential backoff
- Cache: 5 minutos para metadata

### Frontend
- Bundle size: < 200KB inicial
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s

## Segurança

### Backend
- CORS configurado corretamente
- Validação de inputs com Pydantic
- Rate limiting por IP
- Sanitização de logs (sem credenciais)

### Frontend
- Validação client-side
- Escape de HTML
- Headers de segurança (CSP, X-Frame-Options)

## Documentação

### Docstrings (Python)
```python
def fetch_page(
    self,
    data_inicial: str,
    data_final: str,
    uf: str | None = None
) -> dict:
    """
    Busca uma página de licitações do PNCP.

    Args:
        data_inicial: Data inicial no formato YYYY-MM-DD
        data_final: Data final no formato YYYY-MM-DD
        uf: Sigla do estado (opcional)

    Returns:
        dict: Resposta da API com dados paginados

    Raises:
        PNCPAPIError: Em caso de falha após retries
        PNCPRateLimitError: Se rate limited persistir
    """
```

### JSDoc (TypeScript)
```typescript
/**
 * Busca licitações de uniformes no PNCP
 *
 * @param ufs - Lista de UFs selecionadas
 * @param dataInicial - Data inicial (YYYY-MM-DD)
 * @param dataFinal - Data final (YYYY-MM-DD)
 * @returns Resumo e ID de download
 * @throws Error se a busca falhar
 */
async function buscarLicitacoes(
  ufs: string[],
  dataInicial: string,
  dataFinal: string
): Promise<BuscaResult>
```
