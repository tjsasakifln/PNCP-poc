# Task: Intake de Processo Judicial via PDF

**Task ID:** intake-processo-pdf
**Versao:** 1.0
**Agente:** legal-chief
**Squad:** legal-analyst

## Proposito
Receber um PDF de processo judicial, extrair dados estruturados (partes, pedidos, causa de pedir, fundamentos, decisoes) e iniciar o pipeline de analise processual completa.

## Inputs
| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| pdf_path | string | Sim | Caminho para o PDF do processo |
| objetivo | string | Nao | Objetivo especifico da analise (ex: "elaborar contrarrazoes") |
| foco | string | Nao | Foco da analise (ex: "dano moral", "prescricao") |

## Precondições
- [ ] PDF legivel (nao escaneado sem OCR)
- [ ] PDF contem pecas processuais identificaveis

## Etapas

### Etapa 1: Extracao de Dados do PDF
1. Ler o PDF completo
2. Identificar tipo de peca processual (peticao inicial, contestacao, sentenca, acordao, recurso)
3. Extrair metadados:
   - Numero do processo (formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO)
   - Tribunal e vara/turma
   - Partes (autor, reu, terceiros)
   - Advogados (OAB)
   - Juiz/Relator
   - Data de distribuicao/julgamento
4. Extrair conteudo juridico:
   - Fatos narrados
   - Causa de pedir (proxima e remota)
   - Pedidos (principal e subsidiarios)
   - Fundamentos juridicos citados (leis, artigos, jurisprudencia)
   - Valor da causa
   - Decisoes anteriores (se houver)

### Etapa 2: Classificacao Automatica
1. Encaminhar dados extraidos para @barbosa-classifier
2. Obter: classe processual TPU, assuntos, competencia
3. Gerar codigo DATAJUD

### Etapa 3: Definicao de Escopo da Analise
1. Se usuario definiu objetivo -> focar no objetivo
2. Se nao -> analisar todas as questoes juridicas identificadas
3. Definir quais agentes serao acionados
4. Estimar complexidade e tempo

### Etapa 4: Iniciar Pipeline
1. Encaminhar para Fase 0 (Triagem) do pipeline completo
2. Acompanhar execucao de todas as fases
3. Retornar resultado final formatado

## Output
- **Localizacao:** `output/legal/{numero-processo}/`
- **Formato:** Relatorio completo (MD) + Dados estruturados (YAML)
- **Secoes do relatorio:**
  - Resumo Executivo
  - Dados Extraidos do PDF
  - Classificacao Processual
  - Mapa de Jurisprudencia
  - Perfil do Relator
  - Dados Jurimetricos
  - Fundamentacao Tecnica
  - Estrategia Argumentativa
  - Relatorio de Conformidade CNJ
  - Recomendacoes

## Condicoes de Veto
- PDF ilegivel ou corrompido -> BLOQUEAR, solicitar novo arquivo
- Processo sem numero identificavel -> ALERTA, solicitar numero
- Peca processual nao identificavel -> ALERTA, solicitar esclarecimento

## Criterios de Conclusao
- [ ] Dados extraidos do PDF com sucesso
- [ ] Classificacao processual realizada
- [ ] Pipeline de analise executado
- [ ] Relatorio final gerado
- [ ] Dados formatados conforme DATAJUD
