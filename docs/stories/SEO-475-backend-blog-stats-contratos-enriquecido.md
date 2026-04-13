# SEO-475 — Backend: enriquecer endpoints de contratos com n_unique_orgaos, n_unique_fornecedores e sample_contracts

**Status:** InReview  
**Type:** Feature  
**Prioridade:** Alta — pré-requisito de SEO-474 e de toda a cadeia de enriquecimento  
**Depende de:** —  
**Bloqueia:** SEO-474, SEO-470, SEO-472, SEO-473

## Problema

Os endpoints `/blog/stats/contratos/{setor}/uf/{uf}`, `/blog/stats/contratos/cidade/{cidade}` e `/blog/stats/contratos/{setor}` retornam dados suficientes para KPIs básicos, mas carecem de campos que o `ContractsPanoramaBlock` (SEO-474) precisa para demonstrar autoridade de mercado:

1. **`n_unique_orgaos`** — quantos órgãos distintos compraram neste setor/UF. Diferente de `len(top_orgaos)` (que é top 10), este número revela a dimensão do mercado comprador
2. **`n_unique_fornecedores`** — quantos fornecedores distintos foram contratados. Mostra competitividade do mercado
3. **`sample_contracts`** — 3 a 5 contratos recentes com objeto, órgão, fornecedor, valor e data. Conteúdo editorial real que prova que o mercado existe e gera autoridade de conteúdo para o Google

Nota: `monthly_trend` já cobre 12 meses (verificado em `_compute_contratos_stats` linha 891). Nenhuma mudança necessária neste campo.

## Solução

Adicionar os três campos a `_compute_contratos_stats` (função compartilhada) e aos modelos Pydantic de response. Os dados já estão disponíveis no loop de agregação existente — é apenas questão de capturar e expor.

## Acceptance Criteria

- [x] AC1: `ContratosSetorUfStats` inclui campo `n_unique_orgaos: int`
- [x] AC2: `ContratosSetorUfStats` inclui campo `n_unique_fornecedores: int`
- [x] AC3: `ContratosSetorUfStats` inclui campo `sample_contracts: list[SampleContract]`
- [x] AC4: Mesmo para `ContratosCidadeStats` (AC1–AC3 aplicáveis)
- [x] AC5: Mesmo para `ContratosSetorStats` (nacional — AC1–AC3 aplicáveis)
- [x] AC6: `SampleContract` tem campos: `objeto: str`, `orgao: str`, `fornecedor: str`, `valor: float | None`, `data_assinatura: str`
- [x] AC7: `sample_contracts` retorna até 5 contratos — os mais recentes com `objeto_contrato` não nulo e `valor_global > 0`
- [x] AC8: `n_unique_orgaos` = `len(set(orgao_cnpj para todos os rows matched))`
- [x] AC9: `n_unique_fornecedores` = `len(set(ni_fornecedor para todos os rows matched))`
- [x] AC10: Cache 6h mantido — nenhuma mudança na estratégia de cache
- [x] AC11: Backward compatibility: campos adicionados como opcionais com default (`n_unique_orgaos: int = 0`) para não quebrar clientes existentes
- [x] AC12: Testes existentes de `blog_stats.py` passam sem regressão
- [x] AC13: Mypy/ruff passam sem novos erros

## Escopo

**IN:**
- `backend/routes/blog_stats.py` — função `_compute_contratos_stats`, modelos Pydantic, endpoint responses

**OUT:**
- Mudanças no banco de dados ou migrations — não necessário (dados já existem, agregação em Python)
- Mudanças no frontend — SEO-474
- Endpoint de bids (`/blog/stats/setor/{setor_id}/uf/{uf}`) — fora do escopo

## Implementação

```python
# Em _compute_contratos_stats, dentro do loop de matched rows:
sample_contracts_raw = []  # captura os 5 mais recentes com objeto e valor

# ... loop existente ...
for row in matched:
    # ... código existente de aggregation ...
    
    # Capturar amostra (já ordenado desc por data_assinatura no query)
    if len(sample_contracts_raw) < 5:
        obj = (row.get("objeto_contrato") or "").strip()
        val = _safe_float_blog(row.get("valor_global"))
        if obj and val > 0:
            sample_contracts_raw.append({
                "objeto": obj[:200],  # truncar para evitar payloads gigantes
                "orgao": row.get("orgao_nome") or row.get("orgao_cnpj") or "",
                "fornecedor": row.get("nome_fornecedor") or row.get("ni_fornecedor") or "",
                "valor": val,
                "data_assinatura": (row.get("data_assinatura") or "")[:10],
            })

# n_unique calculados de orgao_agg e forn_agg já existentes:
n_unique_orgaos = len(orgao_agg)
n_unique_fornecedores = len(forn_agg)
```

## Riscos

- **Truncamento de objeto:** `objeto_contrato` pode ter texto muito longo. Mitigação: truncar a 200 chars (AC7)
- **Payload size:** 5 contratos × 200 chars não representa risco de payload
- **Backward compatibility:** Campos adicionais com default não quebram clientes — verificar que `ContratosSetorUfStats` é consumido apenas pelo frontend Next.js (não por outros serviços internos)

## Complexidade

**S** (1 dia) — adição de campos em função e modelos existentes

## Critério de Done

- `curl https://api-backend/v1/blog/stats/contratos/saude/uf/SP` retorna `n_unique_orgaos`, `n_unique_fornecedores` e `sample_contracts` no JSON
- `sample_contracts` tem ao menos 1 item para setores com dados
- Nenhum teste existente quebrado
- Ruff e mypy sem novos erros

## File List

- [x] `docs/stories/SEO-475-backend-blog-stats-contratos-enriquecido.md` (esta story)
- [x] `backend/routes/blog_stats.py`
- [x] `backend/tests/test_blog_stats.py` (classe TestContratosEnrichment adicionada)
