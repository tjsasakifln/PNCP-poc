# Task: Perfil de Relator

**Task ID:** perfil-relator
**Versao:** 1.0
**Agente:** carmem-relator
**Squad:** legal-analyst

## Proposito
Construir perfil completo de um Relator: tendencia de voto, linhas argumentativas, divergencias, evolucao.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| ministro | string | Sim | Nome do Ministro/Desembargador |
| tema | string | Nao | Tema juridico especifico |

## Etapas
1. Identificar Relator e orgao
2. Levantar votos no tema (ultimos 5 anos)
3. Calcular tendencia (% favoravel/desfavoravel)
4. Identificar votos vencidos e divergencias
5. Mapear linhas argumentativas preferidas
6. Identificar doutrinadores citados
7. Analisar evolucao temporal
8. Comparar com tendencia da turma/tribunal
9. Gerar perfil estruturado

## Output
- **Localizacao:** `minds/{tema}/perfil-relatores/{nome}.md`

## Criterios de Conclusao
- [ ] Tendencia calculada
- [ ] Votos-chave identificados
- [ ] Divergencias mapeadas
- [ ] Perfil gerado
