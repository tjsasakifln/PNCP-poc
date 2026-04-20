# Task: Verificar Admissibilidade

**Task ID:** verificar-admissibilidade
**Versao:** 1.0
**Agente:** fux-procedural
**Squad:** legal-analyst

## Proposito
Verificar pressupostos processuais, condicoes da acao e requisitos de admissibilidade recursal.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| processo | string | Sim | Descricao do processo ou recurso |
| classe | string | Sim | Classe processual (da classificacao) |
| tribunal | string | Sim | Tribunal competente |

## Etapas
1. Identificar tipo de acao/recurso
2. Verificar pressupostos processuais subjetivos (capacidade, legitimidade ad processum)
3. Verificar pressupostos processuais objetivos (peticao inepta, litispendencia, coisa julgada)
4. Analisar condicoes da acao (legitimidade ad causam, interesse de agir)
5. Se recurso: verificar tempestividade, preparo, regularidade formal
6. Se RE/REsp: verificar prequestionamento e repercussao geral
7. Emitir parecer: ADMISSIVEL / INADMISSIVEL / COM RESSALVAS

## Output
- **Localizacao:** `minds/{tema}/admissibilidade-report.md`

## Criterios de Conclusao
- [ ] Pressupostos processuais verificados
- [ ] Condicoes da acao analisadas
- [ ] Requisitos recursais verificados (se aplicavel)
- [ ] Parecer emitido com fundamentacao
