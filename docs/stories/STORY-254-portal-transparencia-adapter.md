# STORY-254: Portal da Transparência — Nova Fonte Federal com Sanções

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-254 |
| **Priority** | P2 |
| **Sprint** | Sprint 3 |
| **Estimate** | 8h |
| **Depends on** | STORY-252 (multi-source ativo) |
| **Blocks** | STORY-256 (sanctions usa endpoints desta API) |

## Contexto

O Portal da Transparência do Governo Federal (`api.portaldatransparencia.gov.br`) é mantido pela CGU e oferece **106 endpoints REST** com dados de licitações, contratos, despesas e — crucialmente — **cadastros de sanções** (CEIS, CNEP, CEAF, CEPIM). A API é **gratuita** com chave obtida via cadastro Gov.br.

### Por Que Integrar

1. **Redução de dependência do PNCP** — mais uma fonte federal livre quando PNCP está indisponível
2. **Dados únicos que PNCP não tem:**
   - Execução de despesas (empenho → liquidação → pagamento)
   - Cadastros de sanções (empresas impedidas/punidas)
   - Histórico de pagamentos por fornecedor (CNPJ)
   - Acordos de leniência
3. **Enriquecimento de resultados** — para cada licitação encontrada no PNCP, verificar se o fornecedor está sancionado
4. **Alta confiabilidade** — API mantida pela CGU com rate limits documentados

### Dados da API

| Item | Valor |
|------|-------|
| **Base URL** | `https://api.portaldatransparencia.gov.br/api-de-dados` |
| **Auth** | Header `chave-api-dados` com token gratuito |
| **Cadastro** | `portaldatransparencia.gov.br/api-de-dados/cadastrar-email` (requer Gov.br nível Verificado) |
| **Rate Limit** | 90 req/min (06h-24h) · 300 req/min (00h-06h) |
| **Cobertura** | Poder Executivo Federal apenas |
| **Formato datas** | DD/MM/AAAA (diferente do PNCP que usa YYYYMMDD) |
| **Paginação** | `pagina` (1-indexed), sem `totalPaginas` — iterar até array vazio |

### Limitações Conhecidas

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| **Federal apenas** | Não cobre estados/municípios | Complementar ao PNCP, não substitui |
| **Requer `codigoOrgao`** para listar licitações | Não dá para buscar "uniformes" em todos os órgãos de uma vez | Pré-carregar lista de órgãos via `/orgaos-siafi`, buscar em paralelo |
| **Período máx 1 mês** por consulta de licitações | Mais requests para cobrir períodos maiores | Chunking mensal |
| **Sem filtro direto por UF** em licitações | UF vem no `municipio` do response | Filtrar client-side |

---

## Acceptance Criteria

### Track 1: Client Adapter (4h)

- [ ] **AC1:** Novo arquivo `backend/clients/portal_transparencia_client.py` implementando `SourceAdapter` (interface de `clients/base.py`).
- [ ] **AC2:** Método `fetch()` consulta `/api-de-dados/licitacoes` com paginação, respeitando rate limit de 90 req/min (667ms entre requests).
- [ ] **AC3:** Normalização de response para `UnifiedProcurement` format (mesma interface que PNCP/ComprasGov adapters).
- [ ] **AC4:** Conversão de datas: input YYYY-MM-DD → DD/MM/AAAA para a API, response dates → ISO 8601 para output.
- [ ] **AC5:** Handling de `codigoOrgao` obrigatório: pré-carregar top 50 órgãos federais (por volume de licitações) via `/orgaos-siafi` e consultar em paralelo.
- [ ] **AC6:** API key carregada de env var `PORTAL_TRANSPARENCIA_API_KEY` — erro claro se ausente e fonte habilitada.
- [ ] **AC7:** Retry com backoff em 429 (rate limit) e 5xx. Skip em 4xx (exceto 429).

### Track 2: Sanctions Endpoints (2h)

Estes endpoints são a base para STORY-256 mas a integração inicial já fica nesta story.

- [ ] **AC8:** Método `check_ceis(cnpj: str) -> list[SanctionRecord]` — consulta `/api-de-dados/ceis?codigoSancionado={cnpj}`. Retorna lista de sanções ativas.
- [ ] **AC9:** Método `check_cnep(cnpj: str) -> list[SanctionRecord]` — consulta `/api-de-dados/cnep?codigoSancionado={cnpj}`. Retorna sanções + valor da multa.
- [ ] **AC10:** Método `check_sanctions(cnpj: str) -> SanctionsResult` — agrega CEIS + CNEP em um resultado unificado com `is_sanctioned: bool`, `sanctions: list`, `checked_at: datetime`.
- [ ] **AC11:** Caching de resultados de sanções por CNPJ (in-memory, TTL 24h) — CNPJ limpo raramente muda de status em menos de 1 dia.

### Track 3: Source Registration & Tests (2h)

- [ ] **AC12:** Registrar `PORTAL_TRANSPARENCIA` como nova fonte em `source_config/sources.py` com prioridade 3 (entre ComprasGov e Licitar).
- [ ] **AC13:** Env var `ENABLE_SOURCE_PORTAL_TRANSPARENCIA=true/false` controla ativação.
- [ ] **AC14:** Testes unitários para o adapter: fetch com mock, normalização de campos, conversão de datas, handling de rate limit.
- [ ] **AC15:** Testes unitários para sanctions: CEIS check, CNEP check, cache hit, CNPJ limpo vs sancionado.
- [ ] **AC16:** Integration test (marcado `@pytest.mark.integration`): consulta real à API com chave de teste.

---

## Schema: `SanctionRecord`

```python
@dataclass
class SanctionRecord:
    source: str              # "CEIS" | "CNEP"
    cnpj: str
    company_name: str
    sanction_type: str       # "Impedimento", "Inidoneidade", "Suspensão", etc.
    start_date: date
    end_date: Optional[date]
    sanctioning_body: str    # "Ministério da Defesa", etc.
    legal_basis: str         # "Lei 8.666/1993, Art. 87, IV"
    fine_amount: Optional[Decimal]  # Só CNEP
    is_active: bool          # end_date is None ou end_date > hoje

@dataclass
class SanctionsResult:
    cnpj: str
    is_sanctioned: bool
    sanctions: list[SanctionRecord]
    checked_at: datetime
    ceis_count: int
    cnep_count: int
```

## Endpoints Utilizados

| Endpoint | Uso | Params Chave |
|----------|-----|-------------|
| `GET /api-de-dados/licitacoes` | Busca de licitações federais | `codigoOrgao`, `dataInicial`, `dataFinal`, `pagina` |
| `GET /api-de-dados/contratos/cpf-cnpj` | Contratos por fornecedor | `cpfCnpj`, `pagina` |
| `GET /api-de-dados/ceis` | Empresas impedidas/suspensas | `codigoSancionado`, `pagina` |
| `GET /api-de-dados/cnep` | Empresas punidas (Lei Anticorrupção) | `codigoSancionado`, `pagina` |
| `GET /api-de-dados/orgaos-siafi` | Lista de órgãos federais | `pagina` |

## Arquivos

| Arquivo | Tipo | Mudança |
|---------|------|---------|
| `backend/clients/portal_transparencia_client.py` | **NOVO** | Adapter completo |
| `backend/clients/sanctions.py` | **NOVO** | CEIS/CNEP checker com cache |
| `backend/source_config/sources.py` | Editar | Registrar PORTAL_TRANSPARENCIA |
| `backend/schemas.py` | Editar | SanctionRecord, SanctionsResult |
| `backend/tests/test_portal_transparencia.py` | **NOVO** | Unit + integration tests |
| `.env.example` | Editar | `PORTAL_TRANSPARENCIA_API_KEY=` |

## Definition of Done

- [ ] Adapter funcional consultando licitações federais
- [ ] `check_sanctions(cnpj)` retorna status unificado CEIS+CNEP
- [ ] Integrado no multi-source consolidation (STORY-252)
- [ ] Testes passando (unit + integration)
- [ ] Rate limit respeitado (90 req/min)
- [ ] Zero regressão

## Referências

- [Swagger UI](https://api.portaldatransparencia.gov.br/swagger-ui/index.html)
- [Cadastro de API Key](https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email)
- [Exemplos de Uso](https://portaldatransparencia.gov.br/pagina-interna/603579-api-de-dados-exemplos-de-uso)
- [Python wrapper (comunidade)](https://github.com/guizsantos/portaldatransparencia)
- [MCP Portal Transparência](https://github.com/dutradotdev/mcp-portal-transparencia)
