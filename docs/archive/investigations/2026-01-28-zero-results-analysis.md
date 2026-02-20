# Investigacao: Busca Retornando Zero Resultados

**Data:** 2026-01-28
**Reportado por:** Usuario
**Severidade:** CRITICA
**Status:** Em Analise

## Sintoma

Ao buscar por licitacoes de uniformes em todo o Brasil (27 UFs), o sistema retorna zero resultados. Isso e improvavel considerando o volume de contratacoes publicas no pais.

---

## Analise Multi-Agente

### @architect (Aria) - Analise de Arquitetura

#### Fluxo de Dados Atual

```
Frontend (Next.js)
    |
    v
POST /api/buscar
    |
    v
Backend (FastAPI)
    |
    +---> PNCP Client (fetch_all)
    |         |
    |         +---> Loop: 5 modalidades x N UFs x M paginas
    |         |
    |         v
    |     API PNCP (pncp.gov.br)
    |
    +---> filter_batch()
    |         |
    |         +---> Filtro UF
    |         +---> Filtro Valor (R$ 50k - R$ 5M)
    |         +---> Filtro Keywords (65 termos)
    |         +---> Filtro Prazo <-- BUG CRITICO AQUI
    |
    +---> LLM Summary (GPT-4.1-nano)
    |
    +---> Excel Generator
    |
    v
Response com resumo + download_id
```

#### Pontos de Falha Identificados

| Camada | Componente | Risco | Status |
|--------|------------|-------|--------|
| API | Formato de data | Baixo | CORRIGIDO (yyyyMMdd) |
| API | Page size | Baixo | CORRIGIDO (20 items) |
| API | HTTP 204 handling | Baixo | CORRIGIDO |
| API | Modalidades | Medio | 5 de 15 modalidades |
| Filter | Filtro de prazo | **CRITICO** | **BUG ATIVO** |
| Filter | Faixa de valor | Medio | Muito restritivo |
| Filter | Keywords | Baixo | 65 termos cobertos |

---

### @dev (James) - Analise de Codigo

#### BUG CRITICO: Filtro de Prazo (filter.py:249)

```python
# LINHA 240-250 de filter.py
data_abertura_str = licitacao.get("dataAberturaProposta")
if data_abertura_str:
    try:
        data_abertura = datetime.fromisoformat(
            data_abertura_str.replace("Z", "+00:00")
        )
        # BUG: Compara se a data de abertura ja passou
        if data_abertura < datetime.now(data_abertura.tzinfo):
            return False, "Prazo encerrado"  # <-- REJEITA TUDO!
    except (ValueError, TypeError):
        pass
```

**Problema:** O campo `dataAberturaProposta` representa a data de ABERTURA das propostas, nao o prazo final. Quando buscamos licitacoes dos ultimos 7 dias:

1. Busca: 21/01/2026 a 28/01/2026
2. Licitacoes retornadas tem `dataAberturaProposta` nesse periodo
3. Hoje e 28/01/2026
4. Qualquer data anterior a hoje (21-27/01) e considerada "prazo encerrado"
5. **RESULTADO: 100% das licitacoes sao rejeitadas!**

#### Correcao Proposta

```python
# OPCAO 1: Remover filtro de prazo (mais seguro)
# Deixar usuario decidir se quer ver licitacoes com prazo encerrado

# OPCAO 2: Usar dataFimReceberPropostas se disponivel
data_fim_str = licitacao.get("dataFimReceberPropostas") or licitacao.get("dataAberturaProposta")

# OPCAO 3: Adicionar margem de tolerancia
if data_abertura < datetime.now(data_abertura.tzinfo) - timedelta(days=1):
    return False, "Prazo encerrado"
```

#### Outros Problemas de Codigo

**1. Faixa de Valor Hardcoded (main.py)**
```python
# Linhas 184-185
valor_min=50_000.0,   # Exclui licitacoes pequenas
valor_max=5_000_000.0 # Exclui licitacoes grandes
```

**2. Modalidades Limitadas (config.py)**
```python
DEFAULT_MODALIDADES = [4, 5, 6, 7, 8]  # Apenas 5 de 15 modalidades
```

---

### @data-engineer (Dara) - Analise de Dados

#### Mapeamento de Campos PNCP

| Campo PNCP | Uso Atual | Interpretacao Correta |
|------------|-----------|----------------------|
| `dataAberturaProposta` | Filtro de prazo | Data de ABERTURA (inicio), nao fim |
| `dataFimReceberPropostas` | Nao usado | Data LIMITE para propostas |
| `dataEncerramentoProposta` | Nao usado | Data de encerramento |
| `valorTotalEstimado` | Filtro R$ 50k-5M | Pode excluir oportunidades validas |

#### Estatisticas Esperadas

Com base em dados publicos do PNCP:
- ~500-1000 publicacoes/dia em todo Brasil
- ~5-10% relacionadas a uniformes/vestuario
- **Esperado: 25-100 resultados em 7 dias para 27 UFs**

#### Recomendacoes

1. **Remover filtro de prazo** - Campo incorreto para esse proposito
2. **Expandir faixa de valor** - R$ 10k a R$ 10M
3. **Adicionar logging detalhado** - Quantos rejeitados por cada filtro
4. **Mostrar estatisticas ao usuario** - "X encontradas, Y filtradas"

---

### @qa (Quinn) - Analise de Qualidade

#### Casos de Teste Faltantes

| Cenario | Testado? | Prioridade |
|---------|----------|------------|
| Busca retorna 0 items da API | Parcial | Alta |
| Busca retorna items mas todos filtrados | **NAO** | **CRITICA** |
| Filtro de prazo com datas passadas | **NAO** | **CRITICA** |
| Filtro de valor nos limites | Sim | Media |
| Filtro de keywords edge cases | Sim | Media |

#### Testes de Regressao Necessarios

```python
def test_filter_does_not_reject_valid_historical_bids():
    """Licitacoes com data de abertura no passado NAO devem ser rejeitadas."""
    bid = {
        "uf": "SP",
        "valorTotalEstimado": 100000.0,
        "objetoCompra": "Aquisição de uniformes",
        "dataAberturaProposta": "2026-01-20T10:00:00Z"  # Passado
    }
    aprovada, motivo = filter_licitacao(bid, {"SP"})
    assert aprovada == True, f"Licitacao valida rejeitada: {motivo}"
```

#### Metricas de Qualidade

- **Cobertura atual:** 96.69% (82 testes)
- **Gap:** Cenarios de filtro de prazo nao cobertos
- **Acao:** Adicionar 5-10 testes para filtro de prazo

---

### @ux-design-expert (Uma) - Analise de UX

#### Problemas de Experiencia Identificados

**1. Loading State Insuficiente**
```
Atual:
+----------------------------------+
| [skeleton]                       |
| [skeleton]                       |
| Buscando licitacoes...           |
+----------------------------------+

Problema: Usuario nao sabe em qual etapa esta
```

**2. Ausencia de Empty State**
```
Quando retorna 0 resultados:
- Nenhum feedback especifico
- Usuario nao sabe se e erro ou resultado vazio
- Nao ha sugestoes de acao
```

**3. Tempo de Espera Angustiante**

| Operacao | Tempo Estimado | Feedback Atual |
|----------|----------------|----------------|
| Fetch PNCP (5 modalidades x 27 UFs) | 30-60s | Nenhum |
| Filtrar resultados | <1s | Nenhum |
| Gerar resumo LLM | 5-15s | Nenhum |
| Gerar Excel | 1-3s | Nenhum |

**Total: 40-80 segundos sem feedback de progresso!**

#### Solucoes Propostas

**1. Progress Steps (Stepper)**
```
Buscando licitacoes...
[====>               ] 25%
Etapa 2 de 4: Filtrando resultados

1. Consultando PNCP     ✓
2. Filtrando resultados ●
3. Gerando resumo IA    ○
4. Preparando Excel     ○
```

**2. Empty State Amigavel**
```
+----------------------------------+
|        (icone de pasta vazia)    |
|                                  |
|   Nenhuma licitacao encontrada   |
|                                  |
|   Sugestoes:                     |
|   • Amplie o periodo de busca    |
|   • Selecione mais estados       |
|   • Verifique os filtros         |
|                                  |
|   [Tentar novamente]             |
+----------------------------------+
```

**3. Loading com Estimativa**
```
Buscando licitacoes...
Tempo estimado: ~45 segundos
Buscando em 27 estados, 5 modalidades
```

---

### @analyst (Atlas) - Analise de Negocio

#### Impacto no Negocio

| Aspecto | Impacto | Severidade |
|---------|---------|------------|
| Demonstracao POC | Falha total | CRITICA |
| Confianca do usuario | Perda de credibilidade | Alta |
| Valor do produto | Inutilizavel | CRITICA |

#### Requisitos Funcionais Nao Atendidos

1. **RF-001:** Buscar licitacoes de uniformes no PNCP
   - Status: **FALHA** - Retorna 0 resultados

2. **RF-002:** Filtrar por UF, valor e keywords
   - Status: **PARCIAL** - Filtro de prazo incorreto

3. **RF-003:** Gerar resumo executivo
   - Status: **N/A** - Depende de resultados

4. **RF-004:** Exportar para Excel
   - Status: **N/A** - Depende de resultados

#### Criterios de Aceite para Demo

1. Busca em todos os estados retorna > 0 resultados
2. Loading mostra progresso em tempo real
3. Empty state informa usuario adequadamente
4. Tempo de resposta < 60 segundos para demo

---

## Resumo: Root Causes

| # | Causa | Tipo | Impacto | Esforco |
|---|-------|------|---------|---------|
| 1 | Filtro de prazo rejeitando licitacoes validas | Bug | CRITICO | Baixo |
| 2 | Loading sem progresso (angustiante) | UX | Alto | Medio |
| 3 | Faixa de valor muito restritiva | Config | Medio | Baixo |
| 4 | Ausencia de empty state | UX | Medio | Baixo |
| 5 | Modalidades limitadas (5 de 15) | Config | Baixo | Baixo |

---

## Proximos Passos

Ver documento: `docs/investigations/2026-01-28-optimization-plan.md`

