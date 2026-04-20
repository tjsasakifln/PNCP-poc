# Task: Consolidar Precedentes

**Task ID:** consolidar-precedentes
**Versao:** 1.0
**Agente:** toffoli-aggregator
**Squad:** legal-analyst

## Proposito
Consolidar precedentes dispersos em mapa coerente. Identificar correntes, IRDR, IAC, temas repetitivos e sumulas.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| tema | string | Sim | Tema juridico |
| acordaos | lista | Sim | Acordaos da pesquisa |

## Etapas
1. Agrupar acordaos por tese/entendimento
2. Identificar correntes (majoritaria, minoritaria)
3. Mapear IRDR/IAC sobre o tema
4. Mapear temas repetitivos STF/STJ
5. Mapear sumulas aplicaveis
6. Identificar divergencias entre tribunais
7. Criar matriz de consolidacao

## Output
- **Localizacao:** `minds/{tema}/precedentes-consolidados.md`

## Criterios de Conclusao
- [ ] Correntes identificadas e quantificadas
- [ ] Mecanismos de uniformizacao mapeados
- [ ] Divergencias documentadas
- [ ] Matriz de consolidacao gerada
