# Referencia: Schema DATAJUD

> Resolucao CNJ 331/2020 — Base Nacional de Dados do Poder Judiciario

---

## Sobre o DATAJUD

O DATAJUD e a Base Nacional de Dados do Poder Judiciario brasileiro, instituida pela Resolucao CNJ 331/2020. Centraliza dados de todos os processos judiciais do pais, de todos os ramos e instancias.

**Objetivo:** Transparencia, estatisticas judiciais, gestao, e fundamentacao de politicas publicas.

---

## Campos Obrigatorios

### Identificacao do Processo
| Campo | Tipo | Formato | Descricao |
|-------|------|---------|-----------|
| `numero` | string | NNNNNNN-DD.AAAA.J.TR.OOOO | Numero unico CNJ |
| `classe` | objeto | {codigo, descricao} | Classe processual TPU |
| `assuntos` | lista | [{codigo, descricao, principal}] | Assuntos TPU |
| `orgao_julgador` | objeto | {codigo, nome, instancia} | Orgao julgador |

### Datas
| Campo | Tipo | Formato |
|-------|------|---------|
| `data_ajuizamento` | date | DD/MM/AAAA |
| `data_ultima_movimentacao` | date | DD/MM/AAAA |

### Partes
| Campo | Tipo | Descricao |
|-------|------|-----------|
| `partes` | lista | Nome, tipo (autor/reu/terceiro), advogados |

### Movimentacoes
| Campo | Tipo | Descricao |
|-------|------|-----------|
| `movimentacoes` | lista | Data, codigo TPU, descricao, complemento |

### Status
| Campo | Tipo | Valores |
|-------|------|---------|
| `situacao` | enum | em_tramitacao, baixado, arquivado, suspenso |

---

## Campos Opcionais

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `valor_causa` | decimal | Valor em reais |
| `prioridade` | boolean + tipo | Idoso, crianca, saude, preso |
| `segredo_justica` | boolean | Tramitacao sigilosa |
| `justica_gratuita` | boolean | Parte hipossuficiente |
| `tutela_urgencia` | boolean | Liminar concedida |

---

## API DATAJUD

**Endpoint base:** `https://datajud-wiki.cnj.jus.br/`

**Formato de resposta:** JSON

**Autenticacao:** Chave de API (solicitar ao CNJ)

**Endpoints principais:**
- `/api-publica/` — Dados publicos de processos
- `/documentacao/` — Documentacao da API

---

## Integracao com Pipeline

O `@datajud-formatter` utiliza este schema para:
1. Validar campos obrigatorios
2. Formatar dados de saida
3. Gerar YAML exportavel
4. Garantir compatibilidade com a base DATAJUD
