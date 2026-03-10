# /intel-b2g — Mapeamento Inteligente de Leads B2G

## Purpose

Varredura multi-fonte para mapear TODOS os players ativos de um setor em licitacoes publicas. Cruza PNCP contratos + OpenCNPJ + Portal da Transparencia para consolidar dados cadastrais, operacionais e de contato.

**Squad:** `squad-intel-b2g.yaml` (v2.0)
**Task:** `intel-b2g-leads.md`
**Output primario:** `docs/intel-b2g/leads-{setor}-{data}.xlsx` (planilha com mensagens WhatsApp)
**Output secundario:** `docs/intel-b2g/leads-{setor}-{data}.md` (relatorio markdown)

---

## Usage

```
/intel-b2g leads de {setor}
/intel-b2g leads de medicamentos
/intel-b2g leads de engenharia --meses 12 --ufs SP,RJ,MG
/intel-b2g leads de limpeza --min-contratos 3
```

## What It Does

1. **Coleta** — Busca contratos PNCP do setor (6-12 meses), extrai CNPJs vencedores
2. **Enriquecimento** — OpenCNPJ (cadastro, QSA, contato) + Portal Transparencia (sancoes, contratos federais)
3. **Decisor** — Identifica socio-administrador do QSA como ponto de contato
4. **Contato** — Valida telefones (flag WhatsApp), busca website e email
5. **Consolidacao** — Gera relatorio ordenado por faturamento gov mensal
6. **WhatsApp Outreach** — Gera aba Excel com mensagem personalizada por lead, link wa.me clicavel, e colunas de tracking

**Oferta padrao:** Consultoria de consolidacao de licitacoes R$1.500/mes + 3% comissao (MAYDAY Track A1)

## Output Schema (por lead)

| Campo | Fonte |
|-------|-------|
| Empresa + Nome Fantasia | OpenCNPJ |
| CNPJ | PNCP |
| Cidade Sede | OpenCNPJ |
| Setor (CNAE) | OpenCNPJ |
| UFs/Cidades de Atuacao | PNCP (agregado) |
| Faturamento Gov Mensal | PNCP + PT (calculado) |
| Capital Social + Porte | OpenCNPJ |
| Website | OpenCNPJ / Web Search |
| Telefone (WhatsApp flag) | OpenCNPJ |
| Email | OpenCNPJ |
| Decisor (Nome + Cargo) | OpenCNPJ QSA |
| Sancoes | Portal da Transparencia |

## Execution

When this command is invoked:

1. Load squad config from `.aios-core/development/agent-teams/squad-intel-b2g.yaml`
2. Load task workflow from `.aios-core/development/tasks/intel-b2g-leads.md`
3. Map user's sector name to `backend/sectors_data.yaml` keywords
4. Execute the 5-step pipeline (coleta → enriquecimento → decisor → contato → consolidacao)
5. Save output to `docs/intel-b2g/`

## Output Excel

A planilha `.xlsx` gerada tem 5 abas:

| Aba | Conteudo |
|-----|----------|
| **Resumo** | Totais, cobertura UF, valor agregado |
| **Leads** | Todos os leads (41+ colunas: dados + tracking + mensagem WhatsApp) |
| **WhatsApp Outreach** | Apenas leads com celular — mensagem pronta, link wa.me, tracking |
| **Ref_CRM** | Legenda dos campos de tracking |
| **Metodologia** | Fontes, periodo, filtros aplicados |

**Aba "WhatsApp Outreach"** e a principal para prospeccao:
- Link wa.me clicavel (abre conversa direto)
- Mensagem personalizada por lead (copiar e colar)
- Colunas de tracking: Enviada?, Resposta, Follow-up, Status, Notas

## Downstream

Leads gerados aqui alimentam o `/ataque-turbo` (squad de prospeccao ativa com cold outreach).

```
/intel-b2g leads de medicamentos    → mapeia 50-200 leads com planilha WhatsApp
/ataque-turbo medicamentos          → pega top 15 e gera cadencia de emails
```

## Params

$ARGUMENTS
