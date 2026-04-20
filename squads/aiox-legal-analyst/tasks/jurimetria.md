# Task: Jurimetria

**Task ID:** jurimetria
**Versao:** 1.0
**Agente:** nunes-quantitative
**Squad:** legal-analyst

## Proposito
Analise quantitativa/estatistica de julgados: taxa de procedencia, valores medios, tendencias, distribuicao por Relator.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| tema | string | Sim | Tema juridico |
| tribunal | string | Nao | Tribunal especifico |
| periodo | string | Nao | Periodo de analise |

## Etapas
1. Definir universo de analise
2. Coletar dados quantitativos
3. Calcular taxa de procedencia/improcedencia
4. Calcular valores medios, medianos, min/max
5. Analisar distribuicao por Relator
6. Analisar tendencia temporal
7. Calcular tempo medio de tramitacao
8. Identificar padroes e outliers
9. Gerar relatorio com tabelas

## Output
- **Localizacao:** `minds/{tema}/jurimetria-report.md`

## Criterios de Conclusao
- [ ] Taxas calculadas
- [ ] Distribuicao por Relator
- [ ] Tendencia temporal
- [ ] Relatorio gerado
