# /radar-b2g — Monitoramento Contínuo de Editais B2G

## Purpose

Varredura diária automatizada de TODOS os editais novos relevantes para um cliente ou carteira de clientes. Baixa os PDFs, analisa os documentos, e entrega um briefing acionável com os editais que merecem atenção HOJE. O consultor acorda e já sabe o que fazer.

**Output primário:** `docs/radar/radar-{YYYY-MM-DD}.md` (briefing diário consolidado)
**Output por cliente:** `docs/radar/radar-{CNPJ}-{YYYY-MM-DD}.md` (briefing individual)
**Output alertas:** `docs/radar/alertas-{YYYY-MM-DD}.md` (apenas urgências)

---

## Usage

```
/radar-b2g                                           # varredura para TODA a carteira
/radar-b2g 12345678000190                            # varredura para 1 CNPJ
/radar-b2g --carteira docs/carteira-clientes.json    # usa arquivo de carteira
/radar-b2g --setor medicamentos                      # varredura por setor (sem cliente específico)
/radar-b2g --dias 3                                  # editais dos últimos 3 dias (padrão: 1)
/radar-b2g --urgente                                 # só editais com encerramento em <7 dias
```

## Arquivo de Carteira (opcional)

Se `--carteira` fornecido, usar JSON com perfil de cada cliente:

```json
{
  "clientes": [
    {
      "cnpj": "12345678000190",
      "nome_fantasia": "Empresa Alpha",
      "setor": "medicamentos",
      "keywords_extras": ["farmaceutico", "hospitalar"],
      "ufs_interesse": ["SP", "RJ", "MG", "PR"],
      "valor_min": 50000,
      "valor_max": 5000000,
      "modalidades": [4, 5, 6, 8],
      "pacote": "premium",
      "decisor": "João Silva",
      "whatsapp": "5511999998888",
      "email": "joao@alpha.com.br"
    }
  ]
}
```

Se carteira não fornecida, buscar CNPJs de reports anteriores em `docs/reports/` e `docs/propostas/` para inferir a carteira.

## What It Does

### Phase 1: Preparação da Varredura (@data-engineer)

1. **Carregar carteira** — De arquivo JSON, ou inferir de outputs anteriores
2. **Para cada cliente**, resolver:
   - Setor (do perfil ou via CNAE do OpenCNPJ)
   - Keywords (de `backend/sectors_data.yaml` + `keywords_extras`)
   - UFs de interesse (do perfil ou todas)
   - Faixa de valor (do perfil ou default do setor)
3. **Consolidar keywords** — Se múltiplos clientes no mesmo setor, deduplicar varreduras para economizar requests

### Phase 2: Varredura de Novos Editais (@data-engineer)

**2a. PNCP — editais publicados nas últimas 24h (ou --dias)**

```bash
# Para cada modalidade relevante (4, 5, 6, 8)
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={ontem_YYYYMMDD}\
  &dataFinal={hoje_YYYYMMDD}\
  &codigoModalidadeContratacao={modalidade}\
  &pagina=1&tamanhoPagina=50"
```

- Paginar até esgotar (max 5 páginas por modalidade — editais de 1 dia raramente excedem isso)
- Filtrar por keywords do setor de cada cliente
- Filtrar por UF se cliente tem UFs de interesse definidas
- Filtrar por faixa de valor se definida
- Extrair: objeto, órgão, UF, município, valor, modalidade, datas, cnpjOrgao, anoCompra, sequencialCompra

**2b. PCP v2 — editais novos**

```bash
curl -s "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos?page=1"
```
- Paginar (max 3 páginas)
- Filtrar client-side por keywords + data de publicação
- Dedup com PNCP

**2c. Prazos vencendo** — Além de novos editais, checar editais já conhecidos (de reports anteriores) cujo `dataEncerramentoProposta` está em <7 dias.

### Phase 3: Análise Documental Rápida (Claude direto)

Para cada edital novo encontrado, executar análise documental SIMPLIFICADA (versão fast do report-b2g Phase 2b):

**3a. Buscar documentos do edital**
```bash
curl -s "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{anoCompra}/{sequencialCompra}/arquivos"
```

**3b. Download do PDF principal** (apenas tipoDocumentoId: 2 = Edital)
```bash
curl -s -o /tmp/radar_{cnpj}_{ano}_{seq}.pdf \
  "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/1"
```

- Apenas 1 documento por edital (o edital principal — sem TR ou anexos)
- Max 20 páginas lidas
- Se PDF >5MB ou download falhar, usar apenas metadados da API

**3c. Análise rápida pelo Claude**

Extrair apenas os campos CRÍTICOS para decisão imediata:

| Campo | Prioridade |
|-------|-----------|
| Critério de julgamento (menor preço / técnica+preço) | CRÍTICA |
| Data e hora de encerramento | CRÍTICA |
| Valor estimado (se divulgado) | ALTA |
| Requisitos de habilitação mais restritivos | ALTA |
| Visita técnica obrigatória? (data limite) | ALTA |
| Amostra exigida? | MÉDIA |
| Exclusivo ME/EPP? | MÉDIA |
| Red flags (1-2 mais relevantes) | MÉDIA |
| Resumo do escopo (1 frase) | ALTA |

**Tempo-alvo:** <2 minutos por edital (análise rápida, não profunda como o report-b2g).

### Phase 4: Matching Cliente × Edital (@analyst)

Para cada par (cliente, edital), calcular:

**Relevance Score (0-100):**

| Dimensão | Peso | Critério |
|----------|------|----------|
| Aderência de keywords | 30% | Quantas keywords do setor aparecem no objeto |
| Faixa de valor | 20% | Valor estimado dentro do range do cliente |
| Geografia | 20% | Edital na UF de interesse do cliente |
| Prazo | 15% | Dias até encerramento (mais tempo = melhor) |
| Habilitação | 15% | Cliente provável apto vs não apto (baseado em porte/capital) |

**Classificação:**

| Score | Tag | Ação |
|-------|-----|------|
| 80-100 | **QUENTE** | Alertar imediatamente — alta aderência |
| 60-79 | **MORNO** | Incluir no briefing diário |
| 40-59 | **FRIO** | Mencionar brevemente |
| <40 | Descartado | Não incluir no briefing |

### Phase 5: Geração do Briefing (@dev)

#### Briefing Diário Consolidado (`radar-{YYYY-MM-DD}.md`)

```markdown
# Radar B2G — {data}

## Resumo
- **Editais novos encontrados:** {N}
- **Relevantes para a carteira:** {N}
- **Alertas QUENTES:** {N}
- **Prazos vencendo esta semana:** {N}
- **Clientes impactados:** {N} de {total}

---

## 🔴 ALERTAS QUENTES (ação em 48h)

### 1. {Objeto resumido} — R${valor}
- **Órgão:** {nome} ({UF})
- **Encerra:** {data} ({N} dias)
- **Modalidade:** {tipo}
- **Critério:** {menor preço / T+P}
- **Relevante para:** {Cliente A} (score {X}), {Cliente B} (score {Y})
- **Do edital:** {1-2 fatos críticos extraídos do PDF}
- **Red flags:** {se houver}
- **Link:** {URL PNCP}

### 2. ...

---

## 🟡 EDITAIS MORNOS (avaliar esta semana)

| # | Objeto | Órgão | UF | Valor | Encerra | Cliente | Score |
|---|--------|-------|----|-------|---------|---------|-------|
| 1 | {resumo} | {orgao} | {UF} | R${val} | {data} | {nome} | {score} |
| ... |

---

## ⏰ PRAZOS VENCENDO (próximos 7 dias)

| Edital | Órgão | Encerra | Cliente | Status |
|--------|-------|---------|---------|--------|
| {num} | {orgao} | {data} ({N}d) | {nome} | Alerta enviado / Pendente |

---

## 📊 Estatísticas do Dia
- Editais varridos: {N} (PNCP: {N}, PCP: {N})
- PDFs analisados: {N}
- Taxa de relevância: {N}% (relevantes / total)
- Setores com mais editais: {setor1} ({N}), {setor2} ({N})
- UFs mais ativas: {UF1} ({N}), {UF2} ({N})
```

#### Briefing Individual por Cliente (`radar-{CNPJ}-{YYYY-MM-DD}.md`)

Versão filtrada apenas com editais relevantes para aquele CNPJ. Formato pronto para copiar e enviar ao cliente via WhatsApp/Email.

```markdown
# Radar de Oportunidades — {Nome Fantasia}
**Data:** {data} | **Setor:** {setor} | **UFs:** {ufs}

## Novos Editais Relevantes ({N})

### ⭐ {Objeto}
- **Órgão:** {nome} — {município}/{UF}
- **Valor:** R${valor}
- **Encerra:** {data} ({N} dias)
- **Critério:** {tipo}
- **O que você precisa:** {resumo de habilitação em 1 linha}
- **Nossa avaliação:** {PARTICIPAR / AVALIAR / MONITORAR}

### ...

## Prazos desta Semana
[editais já conhecidos com prazo vencendo]

---
Tiago Sasaki - Consultor de Licitações
(48)9 8834-4559
```

#### Output de Alertas (`alertas-{YYYY-MM-DD}.md`)

Apenas editais QUENTES (score >80) + prazos <3 dias. Formato ultra-compacto para ação imediata.

## Automação (recomendação de uso)

Este command é projetado para execução diária. Workflow recomendado:

```
06:00  /radar-b2g                           → gera briefing do dia
06:05  Consultor revisa alertas QUENTES     → 5 minutos
06:10  Encaminha briefings individuais       → WhatsApp/Email por cliente
       aos clientes relevantes
```

Para automatizar a execução diária, usar o command `/loop`:
```
/loop 24h /radar-b2g
```

Ou executar manualmente toda manhã como primeira tarefa.

## Downstream

```
/radar-b2g                               → identifica edital quente
/report-b2g {CNPJ}                       → análise profunda para o cliente
/war-room-b2g {edital}                   → prepara participação
/pricing-b2g {objeto} --setor {setor}    → inteligência de preço para ofertar
```

## APIs Reference

| API | Endpoint | Uso no Radar |
|-----|----------|-------------|
| PNCP Consulta | `/api/consulta/v1/contratacoes/publicacao` | Editais novos |
| PNCP Arquivos | `/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos` | Lista documentos |
| PNCP Download | `/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}` | PDF do edital |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Editais complementares |

## Params

$ARGUMENTS
