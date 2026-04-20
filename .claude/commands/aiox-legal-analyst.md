# /aiox-legal-analyst — Activate Legal Analyst Squad (Lei 14.133)

**Squad:** aiox-legal-analyst (vendored from SynkraAI/aiox-squads + SmartLic overlay)

**File:** `squads/aiox-legal-analyst/config.yaml` + `squads/aiox-legal-analyst/config/smartlic-overlay.yaml`

Squad de análise jurídica com 14 agentes especializados. Customizado para SmartLic — foco em **Lei 14.133**, jurisprudência TCU/TCE, habilitação, impugnação. **Complementa** (não substitui) o squad interno existente `lei-14133-modalidades-squad` (que é operacional/classificação).

## Como invocar

```
/aiox-legal-analyst
```

## Leitura obrigatória antes de agir

1. **`squads/_shared/domain-glossary.md`** §"Modalidades (Lei 14.133)"
2. **`squads/aiox-legal-analyst/config.yaml`** — pipeline upstream
3. **`squads/aiox-legal-analyst/config/smartlic-overlay.yaml`** — escopo B2G + fontes autorizadas
4. **`squads/aiox-legal-analyst/agents/legal-analyst.smartlic.md`** — estrutura de parecer + pitfalls
5. **`squads/aiox-legal-analyst/data/lei-14133-articles.md`** — artigos essenciais (referência rápida)
6. **`squads/aiox-legal-analyst/checklists/habilitacao-14133.md`** — checklist habilitação

## Escopo

**IN-SCOPE:**
- Interpretação da Lei 14.133
- Análise de editais (viabilidade, riscos habilitação)
- Preparação de impugnações (Art. 164)
- Parecer sobre modalidade adequada (valor × objeto)
- Jurisprudência TCU/TCE relevante
- Requisitos de habilitação (jurídica, técnica, econômica, fiscal, trabalhista)

**OUT-OF-SCOPE:**
- Processo judicial (cível, trabalhista, penal)
- Direito empresarial genérico
- Aconselhamento jurídico formal (produto é informativo)

## Hierarquia decisória

1. Texto legal (Lei 14.133 + decretos)
2. Jurisprudência TCU (vinculante controle externo)
3. Jurisprudência TCE (esfera estadual)
4. STJ/STF (raro sobre licitações)
5. Doutrina consolidada (3+ comentadores)
6. Parecer AGU/PGFN publicado

## Distinção com squad interno

- `squads/lei-14133-modalidades-squad/` — tactical: "este edital é modalidade X?"
- `/aiox-legal-analyst` — strategic: "devo impugnar?", "qual jurisprudência?", "risco habilitação?"

Handoff: interno classifica; este squad analisa.

## Quality gates (obrigatórios)

- QG-LEGAL-1: Fonte primária citada em toda afirmação de direito
- QG-LEGAL-2: Output marca "parecer técnico, não substitui aconselhamento"
- QG-LEGAL-4: LGPD — não expõe CPF, endereço, dado pessoal

## Quando este squad é apropriado

- Análise profunda de edital antes de participar
- Parecer sobre modalidade em caso ambíguo
- Draft de impugnação
- Verificação de jurisprudência aplicável
- Análise de decreto regulamentador novo

## Quando NÃO usar

- Classificação operacional rápida → `lei-14133-modalidades-squad` interno
- Processo judicial → este squad NÃO é especializado (escopo vetado)
- Estratégia comercial → use `/war-room-b2g` ou `/qualify-b2g`

## Delegação

- Quantificar jurisprudência → `/aiox-deep-research`
- Caso operacional simples → `lei-14133-modalidades-squad`
- Ajuste de prompt LLM backend (se detectar classificação errada) → `@sm` + `@dev`
