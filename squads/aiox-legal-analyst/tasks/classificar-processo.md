# Task: Classificar Processo

**Task ID:** classificar-processo
**Versao:** 1.0
**Agente:** barbosa-classifier
**Squad:** legal-analyst

## Proposito
Classificar processo judicial conforme TPU/SGT do CNJ. Definir classe processual, assuntos, competencia e gerar codigo DATAJUD.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| descricao | string | Sim | Descricao do caso ou dados extraidos |
| partes | lista | Nao | Lista de partes envolvidas |
| valor_causa | string | Nao | Valor da causa |

## Etapas
1. Analisar descricao/dados do caso
2. Identificar ramo do Direito predominante
3. Classificar classe processual (TPU nivel 1, 2, 3)
4. Identificar assuntos (arvore de assuntos CNJ)
5. Determinar competencia (material + territorial + funcional)
6. Identificar tribunal competente
7. Gerar codigo DATAJUD
8. Registrar observacoes relevantes

## Output
- **Localizacao:** `minds/{tema}/classificacao-processual.md`
- **Formato:** Tabela + observacoes

## Criterios de Conclusao
- [ ] Classe processual com codigo TPU
- [ ] Assuntos classificados
- [ ] Competencia definida
- [ ] Tribunal identificado
- [ ] Codigo DATAJUD gerado
