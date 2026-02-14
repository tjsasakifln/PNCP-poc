# STORY-256: Verificação de Sanções — CEIS/CNEP no Pipeline de Leads e Busca

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-256 |
| **Priority** | P3 |
| **Sprint** | Sprint 3-4 |
| **Estimate** | 8h |
| **Depends on** | STORY-254 (client Portal da Transparência com endpoints CEIS/CNEP) |
| **Blocks** | Nenhuma |

## Contexto

O SmartLic já possui um pipeline de prospecção de leads completo (STORY-184) com 11 etapas:

```
Contratos homologados → Agrupamento → Dedup → Receita Federal → Scoring →
Contato → Inteligência → Mensagem → Qualificação → Histórico → Report
```

**O que falta:** Nenhuma verificação de sanções. O sistema recomenda leads que podem estar **impedidas, suspensas ou punidas** pelo governo. Isso é um risco reputacional grave e uma oportunidade de diferenciação competitiva.

### Cadastros de Sanções Disponíveis

| Cadastro | Fonte | O Que Contém | Endpoint |
|----------|-------|-------------|----------|
| **CEIS** | CGU/Portal da Transparência | Empresas impedidas de licitar e contratar | `/api-de-dados/ceis` |
| **CNEP** | CGU/Portal da Transparência | Empresas punidas (Lei Anticorrupção 12.846/2013), inclui valor de multa | `/api-de-dados/cnep` |
| **CEAF** | CGU/Portal da Transparência | Servidores federais expulsos | `/api-de-dados/ceaf` |
| **CEPIM** | CGU/Portal da Transparência | Entidades sem fins lucrativos impedidas | `/api-de-dados/cepim` |
| **TCU Inabilitados** | TCU | Pessoas inabilitadas pelo Tribunal de Contas | `contas.tcu.gov.br/ords/condenacao/consulta/inabilitados` |
| **TCU Certidões** | TCU | Certidão negativa de irregularidades | `certidoes-apf.apps.tcu.gov.br/api/rest/publico/certidoes/{cnpj}` |

### Valor de Negócio

1. **Due diligence automatizada** — verificar se fornecedores/concorrentes estão limpos antes de abordar
2. **Diferencial competitivo** — flag "empresa sancionada" nos resultados de busca (nenhum concorrente faz isso)
3. **Redução de risco** — evitar recomendar leads que não podem participar de licitações
4. **Inteligência de mercado** — empresas sancionadas = oportunidade para concorrentes

---

## Acceptance Criteria

### Track 1: Sanctions Service (3h)

Construir sobre o client do Portal da Transparência (STORY-254 AC8-AC11).

- [ ] **AC1:** Novo arquivo `backend/services/sanctions_service.py` com classe `SanctionsService` que agrega verificações CEIS + CNEP + TCU.
- [ ] **AC2:** Método `check_company(cnpj: str) -> CompanySanctionsReport` que consulta CEIS, CNEP e opcionalmente TCU certidões em paralelo.
- [ ] **AC3:** Cache in-memory por CNPJ com TTL de 24h (sanções mudam raramente). Usar `cachetools.TTLCache`.
- [ ] **AC4:** Batch check: `check_companies(cnpjs: list[str]) -> dict[str, CompanySanctionsReport]` com rate limiting respeitando 90 req/min do Portal da Transparência.
- [ ] **AC5:** Graceful degradation: se Portal da Transparência está indisponível, retornar `status="unavailable"` (não bloquear o pipeline).

### Track 2: Lead Pipeline Integration (2h)

Inserir verificação de sanções como Step 5.5 no pipeline existente.

- [ ] **AC6:** `lead_prospecting.py` chama `SanctionsService.check_company()` após enriquecimento Receita Federal (Step 4) e antes do scoring (Step 5).
- [ ] **AC7:** `LeadProfile` schema atualizado com campos:
  ```python
  sanctions_check: Optional[CompanySanctionsReport]
  is_sanctioned: bool  # True se qualquer sanção ativa encontrada
  ```
- [ ] **AC8:** Scoring penaliza empresas sancionadas: `qualification_score` multiplicado por 0 se `is_sanctioned=True` (lead desqualificado automaticamente).
- [ ] **AC9:** Report de leads inclui seção "Empresas Sancionadas Encontradas" listando as que foram desqualificadas e motivo.
- [ ] **AC10:** Flag `--skip-sanctions` no CLI (`cli_acha_leads.py`) para pular verificação (útil em dev/debug).

### Track 3: Search Results Enrichment (2h)

Além do pipeline de leads, oferecer verificação de sanções nos resultados de busca regular.

- [ ] **AC11:** Novo campo em `BidItem` (resultado de busca): `supplier_sanctions: Optional[SanctionsSummary]` com `is_clean: bool`, `active_sanctions_count: int`.
- [ ] **AC12:** Verificação opt-in via parâmetro `check_sanctions=true` no request de busca (default false — impacto em performance).
- [ ] **AC13:** Quando `check_sanctions=true`, extrair CNPJs dos resultados (campo `cnpj` ou similar) e verificar em batch.
- [ ] **AC14:** Frontend mostra badge nos resultados: shield verde "Empresa Limpa" ou shield vermelho "Sancionada (CEIS)" ao lado do nome do fornecedor.
- [ ] **AC15:** Tooltip no badge vermelho mostra: tipo de sanção, órgão sancionador, data de início, base legal.

### Track 4: Tests (1h)

- [ ] **AC16:** Testes unitários para `SanctionsService`: CNPJ limpo, CNPJ sancionado (CEIS), CNPJ sancionado (CNEP), cache hit, API indisponível.
- [ ] **AC17:** Testes unitários para pipeline integration: lead com sanção → score zerado, lead sem sanção → score normal.
- [ ] **AC18:** Testes unitários para search enrichment: badge rendering com dados mock.
- [ ] **AC19:** Integration test: verificar CNPJ conhecido como sancionado no CEIS (ex: consultar `/ceis?pagina=1` e usar primeiro resultado como fixture).

---

## Schemas

```python
@dataclass
class CompanySanctionsReport:
    cnpj: str
    company_name: Optional[str]
    checked_at: datetime
    status: str                         # "clean" | "sanctioned" | "unavailable"
    is_sanctioned: bool
    ceis_records: list[SanctionRecord]  # De STORY-254
    cnep_records: list[SanctionRecord]  # De STORY-254
    tcu_ineligible: bool               # TCU inabilitados check
    total_active_sanctions: int
    most_severe_sanction: Optional[str] # "Inidoneidade" > "Impedimento" > "Suspensão"
    earliest_end_date: Optional[date]   # Quando a sanção mais próxima termina

@dataclass
class SanctionsSummary:
    """Versão leve para resultados de busca (não o report completo)."""
    is_clean: bool
    active_sanctions_count: int
    sanction_types: list[str]          # ["CEIS: Impedimento", "CNEP: Multa"]
    checked_at: datetime
```

## Fluxo no Pipeline de Leads (Atualizado)

```
Step 1:  Query PNCP homologated contracts      → PNCPHomologadosClient
Step 2:  Group contracts by CNPJ               → Aggregation
Step 3:  Deduplication                         → LeadDeduplicator
Step 4:  Enrich with Receita Federal           → ReceitaFederalClient
Step 5:  ██ CHECK SANCTIONS (NEW) ██           → SanctionsService  ← STORY-256
Step 6:  Calculate dependency score            → LeadScorer
Step 7:  Find contact data                     → ContactSearcher
Step 8:  Gather strategic intelligence         → ContactSearcher
Step 9:  Generate personalized message         → MessageGenerator
Step 10: Calculate qualification score         → LeadScorer (× 0 se sancionado)
Step 11: Update history                        → LeadDeduplicator
Step 12: Generate report (com seção sanções)   → ReportGenerator
```

## Arquivos

| Arquivo | Tipo | Mudança |
|---------|------|---------|
| `backend/services/sanctions_service.py` | **NOVO** | Service unificado CEIS+CNEP+TCU |
| `backend/lead_prospecting.py` | Editar | Inserir Step 5 (sanctions check) |
| `backend/lead_scorer.py` | Editar | Penalizar score de empresa sancionada |
| `backend/schemas_lead_prospecting.py` | Editar | `sanctions_check` + `is_sanctioned` em LeadProfile |
| `backend/schemas.py` | Editar | `SanctionsSummary` para resultados de busca |
| `backend/report_generator.py` | Editar | Seção "Empresas Sancionadas" no report |
| `backend/cli_acha_leads.py` | Editar | Flag `--skip-sanctions` |
| `backend/search_pipeline.py` | Editar | Opt-in `check_sanctions` param |
| `frontend/app/buscar/page.tsx` | Editar | Badge de sanções nos resultados |
| `backend/tests/test_sanctions.py` | **NOVO** | Unit + integration tests |

## Definition of Done

- [ ] `SanctionsService.check_company(cnpj)` retorna report completo CEIS+CNEP
- [ ] Pipeline de leads desqualifica automaticamente empresas sancionadas
- [ ] Report de leads lista empresas sancionadas com motivo
- [ ] Busca com `check_sanctions=true` enriquece resultados com badges
- [ ] Cache 24h para evitar requests repetidos
- [ ] Graceful degradation se Portal da Transparência indisponível
- [ ] Testes passando
- [ ] Zero regressão

## Referências

- [CEIS — Empresas Impedidas](https://portaldatransparencia.gov.br/sancoes/consulta?cadastro=1)
- [CNEP — Empresas Punidas](https://portaldatransparencia.gov.br/sancoes/consulta?cadastro=2)
- [CEAF — Servidores Expulsos](https://portaldatransparencia.gov.br/sancoes/consulta?cadastro=3)
- [API Swagger — Sanctions](https://api.portaldatransparencia.gov.br/swagger-ui/index.html)
- [TCU Certidões](https://certidoes-apf.apps.tcu.gov.br/)
- [TCU Dados Abertos](https://sites.tcu.gov.br/dados-abertos/)
- [Lei Anticorrupção 12.846/2013](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12846.htm)
