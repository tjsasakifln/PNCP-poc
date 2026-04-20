# Task: Validar Fundamentacao

**Task ID:** validar-fundamentacao
**Versao:** 1.0
**Agente:** theodoro-validator
**Squad:** legal-analyst

## Proposito
Validar fundamentacao processual conforme CPC Art. 489 par. 1o, coerencia logica e completude.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| documento | string | Sim | Path ou texto da fundamentacao |

## Etapas
1. Verificar Art. 489, par. 1o, I (nao se limita a indicar norma)
2. Verificar Art. 489, par. 1o, II (explica conceitos indeterminados)
3. Verificar Art. 489, par. 1o, III (motivos nao genericos)
4. Verificar Art. 489, par. 1o, IV (enfrenta todos os argumentos)
5. Verificar Art. 489, par. 1o, V (precedentes com fundamentos determinantes)
6. Verificar Art. 489, par. 1o, VI (distinguishing fundamentado)
7. Verificar coerencia logica
8. Verificar completude
9. Emitir score e parecer

## Output
- **Localizacao:** `output/legal/{processo}/validacao-report.md`

## Criterios de Conclusao
- [ ] 6 incisos do Art. 489 verificados
- [ ] Coerencia logica avaliada
- [ ] Score emitido
- [ ] Parecer (APROVADO/REPROVADO/REVISAO)
