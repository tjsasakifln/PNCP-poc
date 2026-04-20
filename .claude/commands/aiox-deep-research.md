# /aiox-deep-research — Activate Deep Research Squad

**Squad:** aiox-deep-research (vendored from SynkraAI/aiox-squads + SmartLic overlay)

**File:** `squads/aiox-deep-research/config.yaml` + `squads/aiox-deep-research/config/smartlic-overlay.yaml`

Squad de pesquisa profunda com pipeline 3-tier (Diagnostic → Execution → Quality Assurance), 11 agentes especializados baseados em elite minds reais (Sackett, Booth, Creswell, Forsgren, Cochrane, Higgins, Klein, Gilad, Ioannidis, Kahneman). Customizado para pesquisa de mercado B2G usando DataLake (supplier_contracts + pncp_raw_bids).

## Como invocar

```
/aiox-deep-research
```

## Leitura obrigatória antes de agir

Você é o orchestrator de `aiox-deep-research`. Antes de iniciar qualquer pesquisa:

1. **`squads/_shared/domain-glossary.md`** — terminologia B2G canônica
2. **`squads/_shared/supabase-schema.md`** — fonte de dados primária (supplier_contracts, pncp_raw_bids)
3. **`squads/aiox-deep-research/config.yaml`** — pipeline original do squad
4. **`squads/aiox-deep-research/config/smartlic-overlay.yaml`** — fontes autorizadas, vieses B2G
5. **`squads/aiox-deep-research/agents/researcher-b2g.smartlic.md`** — patterns de pesquisa B2G
6. **`squads/aiox-deep-research/tasks/query-datalake.smartlic.md`** — como consultar DataLake
7. **`squads/aiox-deep-research/data/sources-catalog.md`** — hierarquia de confiança de fontes

## Fases do pipeline

- **Tier 0 (Diagnostic)**: Sackett, Booth, Creswell — formular questão PICO adaptada B2G
- **Tier 1 (Execution)**: Forsgren, Cochrane, Higgins, Klein, Gilad — coleta de evidência
- **QA**: Ioannidis (reliability, PPV, bias) + Kahneman (cognitive biases) — mandatory

## Quando este squad é apropriado

- Análise de mercado por setor/UF/esfera
- Perfil competitivo de CNPJ (quem ganha?)
- Viabilidade estratégica de entrada em novo segmento
- Síntese de evidências para decisão de alto impacto
- Benchmarking regional/setorial

## Quando NÃO usar este squad

- Consulta pontual ("qual o último edital de X?") → use `/aiox-dispatch` + query direta
- Verificação jurídica → use `/aiox-legal-analyst`
- Operacional (qualificar um lead específico) → use `/qualify-b2g`

## Output esperado

Sempre entregar em `docs/research/YYYY-MM-DD-<topic>.md` com sections: Question, Method, Findings, Evidence, Biases audited, Recommendations, Limitations.

## Delegação

- Pesquisa precisa paralelizar (múltiplas UFs × setores) → `/aiox-dispatch`
- Questão jurídica no caminho → `/aiox-legal-analyst`
- Visualização de dados complexa → `/aiox-apex` (após pesquisa)
