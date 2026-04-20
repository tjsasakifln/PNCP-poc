# Task: Analisar Precedente

**Task ID:** analisar-precedente
**Versao:** 1.0
**Agente:** fachin-precedent
**Squad:** legal-analyst

## Proposito
Analisar precedente individual: ratio decidendi, obiter dictum, forca vinculante, votos vencidos, vulnerabilidades.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| acordao | string | Sim | Numero do processo ou texto do acordao |

## Etapas
1. Identificar dados (numero, Relator, orgao, data, resultado)
2. Extrair fatos juridicamente relevantes
3. Identificar questao juridica central (holding)
4. Separar ratio decidendi de obiter dictum
5. Analisar fundamentos determinantes do voto vencedor
6. Analisar votos vencidos
7. Avaliar forca vinculante
8. Mapear relacao com outros precedentes

## Output
- **Localizacao:** `minds/{tema}/fichas-precedentes/{numero}.md`

## Criterios de Conclusao
- [ ] Ratio decidendi identificada
- [ ] Obiter dicta separados
- [ ] Forca vinculante avaliada
- [ ] Ficha preenchida
