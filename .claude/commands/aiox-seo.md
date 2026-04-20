# /aiox-seo — Activate SEO Optimization Squad

**Squad:** aiox-seo (vendored from SynkraAI/aiox-squads + SmartLic overlay)

**File:** `squads/aiox-seo/config.yaml` + `squads/aiox-seo/config/smartlic-overlay.yaml`

Squad SEO completo (AUDIT → OPTIMIZE → REPORT) com 8 agentes especializados cobrindo on-page, técnico, dados estruturados, E-E-A-T, Core Web Vitals, visibilidade IA, arquitetura. Customizado para SmartLic — inbound orgânico baseado em supplier_contracts (~2M contratos históricos, potencial 15-20k long-tail pages).

## Como invocar

```
/aiox-seo
```

## Leitura obrigatória antes de agir

1. **`squads/_shared/domain-glossary.md`** — terminologia B2G
2. **`squads/aiox-seo/config.yaml`** — pipeline upstream (3 fases)
3. **`squads/aiox-seo/config/smartlic-overlay.yaml`** — estratégia long-tail + technical SEO B2G
4. **`squads/aiox-seo/agents/seo-specialist.smartlic.md`** — patterns de priorização
5. **`squads/aiox-seo/data/supplier-contracts-schema.md`** — estrutura do dataset primário
6. **`squads/aiox-seo/tasks/generate-blog-from-contracts.smartlic.md`** — pipeline de geração de conteúdo

## Pipeline (3 fases)

1. **AUDIT** — score 0-100 + gap list
2. **OPTIMIZE** — correções em 7 categorias (on-page, technical, structured data, E-E-A-T, CWV, AI visibility, architecture)
3. **REPORT** — antes/depois + métricas

## Tipos de páginas SmartLic

- `/fornecedores/[cnpj]` — ~10k top CNPJs por volume
- `/orgaos/[cnpj]` — ~5k top órgãos
- `/observatorio/[setor]` e `/observatorio/[setor]/[uf]` — hub setorial
- `/contratos-*` — posts manuais existentes (preservar)

## Quando este squad é apropriado

- Gerar páginas programmatic SEO
- Audit técnico de sitemap/robots/canonicals
- Otimização de Core Web Vitals
- Structured data JSON-LD
- Estratégia de hub-and-spoke

## Quando NÃO usar

- Copywriting pontual → `/copymasters`
- Bug em página existente → `@dev` direto
- Estratégia de mídia paga → não escopo (produto é orgânico-first)

## Data constraints B2G

- **NUNCA** inventar fato sobre CNPJ/órgão (fact-check via supplier_contracts)
- **LGPD-aware**: CNPJ é público; CPF nunca expor
- **Staleness**: dataset 3x/sem; pages mostram "atualizado em"

## Delegação

- Refactor de arquitetura frontend → `/aiox-apex`
- Validar claim quantitativa → `/aiox-deep-research`
- Mudança em robots/sitemap infra → `@devops`
