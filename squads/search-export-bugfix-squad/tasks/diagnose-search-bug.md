# Task: Diagnosticar Bug de Busca Retornando 2 Resultados

**Assigned to:** search-specialist
**Priority:** P0
**Estimated Time:** 20 min
**Elicit:** false

## Objetivo

Identificar causa raiz exata do bug onde busca com filtros amplos (todos estados, todas esferas, todas modalidades, período 01/jan - 10/fev) retorna apenas 2 resultados quando deveria retornar centenas/milhares.

## Contexto

**Parâmetros da busca problemática:**
- UFs: Todos os 27 estados
- Esferas: Estadual, Municipal, Federal
- Modalidades: Todas (1-8, Lei 14.133)
- Data: 01/01/2026 - 10/02/2026 (41 dias)
- Setor: Engenharia e Construção

**Resultado:** Apenas 2 licitações retornadas

**Código suspeito identificado:**
- `backend/pncp_client.py:461` - `max_pages=50` (limita a 1000 registros/UF/modalidade)
- `backend/main.py:1309` - `buscar_todas_ufs_paralelo` (pode falhar silenciosamente)
- `backend/config.py` - `DEFAULT_MODALIDADES` (pode estar desatualizado)

## Steps

### 1. Adicionar Logging Detalhado

```python
# Editar backend/pncp_client.py - função buscar_todas_ufs_paralelo

import logging
logger = logging.getLogger(__name__)

async def buscar_todas_ufs_paralelo(...):
    logger.info(f"🔍 DIAGNÓSTICO: Iniciando busca paralela")
    logger.info(f"  - UFs solicitadas: {len(ufs)} → {ufs}")
    logger.info(f"  - Modalidades: {modalidades}")
    logger.info(f"  - Período: {data_inicial} a {data_final}")

    # ... código existente ...

    # Ao final, adicionar:
    logger.info(f"✅ DIAGNÓSTICO: Busca paralela completa")
    logger.info(f"  - UFs processadas com sucesso: {len(successful_ufs)}")
    logger.info(f"  - UFs com erro: {len(failed_ufs)}")
    logger.info(f"  - Total de registros: {len(all_results)}")
```

### 2. Reproduzir Bug Localmente

```bash
# Iniciar backend com logging detalhado
cd backend
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --port 8000

# Em outro terminal, fazer request via curl ou Postman
curl -X POST http://localhost:8000/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "ufs": ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"],
    "esferas": ["estadual", "municipal", "federal"],
    "modalidades": [1,2,3,4,5,6,7,8],
    "data_inicial": "2026-01-01",
    "data_final": "2026-02-10",
    "setor_id": "engenharia_construcao"
  }'
```

### 3. Analisar Logs

```bash
# Ver logs em tempo real
tail -f backend/logs/app.log | grep "DIAGNÓSTICO"

# Procurar por erros silenciosos
grep -i "error\|exception\|failed" backend/logs/app.log | tail -50

# Verificar quantos UFs foram processados vs esperado
grep "UFs processadas com sucesso" backend/logs/app.log
```

### 4. Verificar Limite de Paginação

```python
# Adicionar logging em _fetch_by_uf para detectar quando max_pages é atingido

def _fetch_by_uf(self, ..., max_pages: int = 50):
    # ... código existente ...

    while pagina <= max_pages:
        # ... fetch page ...

        if pagina == max_pages and tem_proxima_pagina:
            logger.warning(
                f"⚠️ MAX_PAGES ATINGIDO! UF={uf}, modalidade={modalidade}, "
                f"página {pagina}/{max_pages}. Resultados incompletos!"
            )
```

### 5. Testar com max_pages Aumentado

```python
# Editar temporariamente pncp_client.py linha 461
max_pages: int = 200,  # Aumentar de 50 para 200

# Re-executar busca e comparar resultados
```

### 6. Verificar buscar_todas_ufs_paralelo

```bash
# Procurar por exceptions em buscar_todas_ufs_paralelo
grep "buscar_todas_ufs_paralelo" backend/logs/app.log | grep -i "error"

# Verificar se está usando paralelização ou fallback
grep "Using parallel fetch\|falling back to sequential" backend/logs/app.log
```

## Acceptance Criteria

- [ ] Causa raiz exata identificada (ex: max_pages atingido em 15/27 UFs)
- [ ] Bug reproduzido localmente com mesmos parâmetros
- [ ] Evidências documentadas:
  - Screenshots dos logs
  - Contagem de UFs processadas vs esperado
  - Contagem de registros por UF/modalidade
  - Mensagens de warning de max_pages atingido (se aplicável)
- [ ] Solução técnica proposta com code snippet
- [ ] Relatório de diagnóstico preenchido (template: `bug-diagnosis-report.md`)

## Expected Findings (Hipóteses)

**Hipótese 1: max_pages atingido**
- Evidência: Logs mostram "MAX_PAGES ATINGIDO" para múltiplas UFs
- Impacto: Busca interrompida prematuramente
- Solução: Aumentar max_pages para 200-500

**Hipótese 2: buscar_todas_ufs_paralelo falhando**
- Evidência: Logs mostram "falling back to sequential" + apenas 1-2 UFs processadas
- Impacto: Paralelização falha, busca incompleta
- Solução: Corrigir error handling em async fetch

**Hipótese 3: Timeout global de 4 min atingido**
- Evidência: Logs mostram "fetch timed out after 240s"
- Impacto: Busca interrompida antes de completar todas UFs
- Solução: Aumentar timeout ou otimizar paralelização

## Deliverables

1. **Bug Diagnosis Report** (`docs/bug-reports/search-2-results-bug.md`)
   - Root cause
   - Reproduction steps
   - Evidence (logs, screenshots)
   - Proposed solution

2. **Code changes para diagnóstico** (commit separado, não vai para prod)
   - Logging adicional
   - Warnings de max_pages

3. **Métricas coletadas**
   - UFs processadas: X/27
   - Modalidades processadas: Y/8
   - Registros por UF/modalidade (top 5)
   - Tempo total de busca
   - Max_pages atingido: Z vezes

## Next Task

Após completar diagnóstico, executar: `fix-search-bug.md`
