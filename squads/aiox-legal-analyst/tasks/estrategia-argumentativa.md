# Task: Estrategia Argumentativa

**Task ID:** estrategia-argumentativa
**Versao:** 1.0
**Agente:** barroso-strategist
**Squad:** legal-analyst

## Proposito
Construir estrategia argumentativa completa: tese principal, subsidiaria, contra-argumentos antecipados, ponderacao se necessario.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| caso | string | Sim | Descricao do caso com fatos e pretensao |
| precedentes | lista | Sim | Precedentes relevantes |
| direitos | lista | Nao | Direitos fundamentais envolvidos |

## Etapas
1. Analisar fatos juridicamente relevantes
2. Identificar tese principal
3. Mapear fundamentos (lei + jurisprudencia + doutrina)
4. Ordenar argumentos do mais forte ao mais fraco
5. Construir tese subsidiaria
6. Antecipar contra-argumentos
7. Se colisao de principios: ponderar (Alexy)
8. Estruturar conforme CPC Art. 489 par. 1o

## Output
- **Localizacao:** `minds/{tema}/estrategia-argumentativa.md`

## Criterios de Conclusao
- [ ] Tese principal com fundamentos hierarquizados
- [ ] Tese subsidiaria definida
- [ ] Contra-argumentos antecipados
- [ ] Fundamentacao CPC Art. 489 compliant
