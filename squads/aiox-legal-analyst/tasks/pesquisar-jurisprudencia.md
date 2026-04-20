# Task: Pesquisar Jurisprudencia

**Task ID:** pesquisar-jurisprudencia
**Versao:** 1.0
**Agente:** mendes-researcher
**Squad:** legal-analyst

## Proposito
Pesquisa jurisprudencial completa sobre um tema juridico, mapeando precedentes do STF, STJ, TJs e TRFs com estrutura DATAJUD.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| tema | string | Sim | Tema juridico para pesquisa |
| tribunal | string | Nao | Tribunal especifico (STF, STJ, TJ-XX, TRF-X) |
| periodo | string | Nao | Periodo de pesquisa (ex: "2020-2025") |

## Etapas
1. Definir termos de busca e palavras-chave
2. Pesquisar no STF (controle concentrado + repercussao geral)
3. Pesquisar no STJ (temas repetitivos + sumulas)
4. Pesquisar nos TRFs/TJs (se aplicavel)
5. Para cada acordao: extrair numero, Relator, orgao, data, ementa, tese
6. Classificar por relevancia (vinculante > repetitivo > persuasivo)
7. Identificar evolucao jurisprudencial
8. Gerar mapa de jurisprudencia

## Output
- **Localizacao:** `minds/{tema}/mapa-jurisprudencia.md`
- **Formato:** Tabelas de sumulas + precedentes + jurisprudencia dominante

## Condicoes de Veto
- Menos de 5 acordaos -> ALERTA
- Menos de 3 acordaos -> BLOQUEAR, solicitar input humano

## Criterios de Conclusao
- [ ] Minimo 5 acordaos relevantes
- [ ] Sumulas aplicaveis identificadas
- [ ] Precedentes classificados por hierarquia
- [ ] Evolucao jurisprudencial mapeada
- [ ] Relatores identificados
