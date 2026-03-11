# /proposta-b2g — Gerador de Proposta Comercial B2G

## Purpose

Gera um PDF de proposta comercial personalizada e profissional para um lead especifico. Cruza perfil da empresa + oportunidades abertas + historico gov para construir uma proposta irrecusavel que mostra ao decisor exatamente quanto dinheiro ele esta deixando na mesa.

**Output primario:** `docs/propostas/proposta-{CNPJ}-{YYYY-MM-DD}.pdf`
**Output secundario:** `docs/propostas/proposta-{CNPJ}-{YYYY-MM-DD}.md` (markdown)
**Rodape:** "Tiago Sasaki - Consultor de Licitacoes (48)9 8834-4559"

---

## Usage

```
/proposta-b2g 12.345.678/0001-90
/proposta-b2g 12345678000190 --pacote premium
/proposta-b2g 12345678000190 --pacote basico --desconto 10
/proposta-b2g 12345678000190 --from-qualify docs/intel-b2g/qualified-medicamentos-2026-03-10.xlsx
```

## Pacotes Disponiveis

| Pacote | Preco | Report freq | PDF analysis | UFs | Suporte |
|--------|-------|-------------|-------------|-----|---------|
| **Mensal** | R$997/mes | 1x/mes | Ate 3 editais | SC | Comercial |
| **Semanal (Rec.)** | R$1.500/mes | 4x semanal + 1x mensal | Ate 8 editais | SC+PR+RS | Estendido |
| **Diario** | R$2.997/mes | Diario + semanal + mensal | Ilimitada | 5 estados | Dedicado |

Todos os pacotes tem desconto anual: pague 10, leve 12.

Se `--pacote` nao for informado, o command seleciona automaticamente baseado no tier/score do `/qualify-b2g`.

## Principios de Conversao

- **Autoridade**: Tiago Sasaki e servidor efetivo da SIE/SC ha 7 anos. Conhece a maquina por dentro. Ja analisou 500+ propostas de habilitacao. Sabe onde 80% das inabilitacoes acontecem.
- **Escassez temporal**: Editais tem prazo. Cada dia sem monitoramento = edital perdido. O CTA usa o edital mais proximo de encerrar como ancora.
- **Prova de valor**: A proposta em si E o produto. Mostra exatamente o que o relatorio /report-b2g entrega.
- **Reciprocidade**: Primeiro mes de cortesia para contratacoes na vigencia da proposta.
- **Contraste**: Tabela "COM vs SEM monitoramento" e "Consultoria Tradicional vs Esta Consultoria".
- **Dados reais, nao promessas**: Todo numero vem de fonte publica verificavel (PNCP, Portal da Transparencia, OpenCNPJ).

## What It Does

### Phase 1: Coleta de Inteligencia (@data-engineer)

1. **Perfil da empresa** — OpenCNPJ (razao social, CNAE, porte, capital, cidade, QSA, decisor)
   ```bash
   CNPJ_LIMPO=$(echo "{CNPJ}" | tr -d './-')
   curl -s "https://api.opencnpj.org/${CNPJ_LIMPO}"
   ```

2. **Historico governamental** — PNCP contratos (ultimos 12 meses deste CNPJ)
   ```bash
   curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
     ?dataInicial={12_meses_atras_YYYYMMDD}\
     &dataFinal={hoje_YYYYMMDD}\
     &cnpj=${CNPJ_LIMPO}\
     &pagina=1&tamanhoPagina=50"
   ```
   - Contar contratos, somar valores, listar orgaos, mapear UFs
   - Calcular faturamento gov mensal medio
   - Identificar concentracao (% de receita do top orgao)

3. **Sancoes** — Portal da Transparencia (verificar impedimentos)
   ```bash
   PT_KEY=$(grep PORTAL_TRANSPARENCIA_API_KEY backend/.env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
   curl -s -H "chave-api-dados: ${PT_KEY}" \
     "https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-juridica?cnpj=${CNPJ_LIMPO}"
   ```

4. **Oportunidades abertas** — Varredura PNCP + PCP dos editais ATUALMENTE abertos no setor
   - Usar keywords do setor mapeado via CNAE
   - Filtrar ultimos 30 dias
   - Contar: total de editais, valor total, por UF, por modalidade

5. **Cross-reference qualify** — Se `--from-qualify` fornecido, puxar score e tier do lead

### Phase 2: Calculo de ROI (@analyst)

O coracao da proposta. Demonstrar matematicamente o retorno do investimento.

**Metricas calculadas:**

1. **Oportunidades perdidas** — Editais abertos AGORA que o lead poderia participar mas provavelmente nao sabe
   ```
   Editais_setoriais_abertos - Editais_que_o_lead_participa = Oportunidades_perdidas
   ```

2. **Valor na mesa** — Soma dos valores estimados das oportunidades perdidas
   ```
   Valor_na_mesa = SUM(valor_estimado dos editais nao participados)
   ```

3. **Taxa de vitoria estimada** — Baseada no historico do lead
   ```
   Taxa_vitoria = Contratos_ganhos / Participacoes_estimadas
   Se sem historico suficiente, usar media setorial: 15-25%
   ```

4. **Receita incremental projetada** — O que o lead ganharia com a consultoria
   ```
   Receita_incremental = Valor_na_mesa × Taxa_vitoria × Fator_melhoria(1.3)
   ```

5. **ROI da consultoria**
   ```
   ROI = (Receita_incremental_anual - Custo_consultoria_anual) / Custo_consultoria_anual × 100
   ```

6. **Payback** — Em quantos meses o investimento se paga
   ```
   Payback_meses = Custo_consultoria_mensal / (Receita_incremental_mensal)
   ```

### Phase 3: Construcao da Proposta (@analyst + @dev)

**Estrutura do PDF (12 secoes):**

#### 1. Capa
- Dinamica: data=hoje, validade=hoje+15dias, CNPJ/nome do JSON
- Titulo: "Proposta de Consultoria em Licitacoes Publicas"
- Subtitulo: "Preparada exclusivamente para {Nome_Fantasia}"
- Visual limpo e profissional

#### 2. Carta ao Decisor
- Personalizada com deteccao de genero (Sr./Sra.) a partir do QSA
- Template-driven, referencia dados reais do edital prioritario
- Tom: consultivo, direto, sem floreios

#### 3. Diagnostico da Empresa
- Dinamico do JSON: pontos fortes/atencao derivados dos dados coletados
- Dados cadastrais (razao, fantasia, CNAE, porte, capital, cidade)
- Historico gov: {N} contratos em 12 meses, R${valor} faturamento gov
- UFs de atuacao, orgaos mais frequentes
- Analise de concentracao: "{X}% da receita gov vem de {orgao_top}" — risco ou oportunidade

#### 4. Radiografia do Mercado
- Dinamica: distribuicao municipal computada de editais via groupby
- Tendencias extraidas de `inteligencia_mercado` do JSON
- Total de editais abertos no setor: {N}, valor total em disputa: R${valor}
- Distribuicao por UF (tabela computada dos editais)

#### 5. Top Oportunidades
- Dinamica: ordenadas por (prioridade de recomendacao, valor desc), sem truncamento
- Datas no formato DD/MM/YYYY (nunca ISO)
- Separador travessao (—) no objeto/orgao
- Todos os editais listados, nao apenas top 10

#### 6. Analise Detalhada — Edital Prioritario
- Primeiro edital com recomendacao PARTICIPAR
- Analise de habilitacao (requisitos do edital)
- Analise estrategica com 6 fatores
- Perguntas e respostas para o decisor (Q&A)

#### 7. Dimensionamento da Oportunidade
- ROI computado a partir de contagens/valores reais dos editais
- Tabela comparativa COM vs SEM monitoramento
- Tabela de projecao anual
- Disclaimer: "Projecoes baseadas em dados publicos. Resultados dependem da execucao."

#### 8. O Que Cada Relatorio Entrega
- Showcase da qualidade do /report-b2g (10 secoes + 6 fontes)
- Demonstra que a proposta EM SI e o produto

#### 9. Pacotes de Monitoramento
- 3 tiers: Mensal R$997 | Semanal R$1.500 (RECOMENDADO) | Diario R$2.997
- Comparativo rapido entre pacotes
- Desconto anual destacado: pague 10, leve 12

#### 10. Quem Analisa Seus Editais
- Secao de AUTORIDADE
- 7 anos como servidor efetivo da SIE/SC
- 500+ propostas de habilitacao analisadas pelo lado do orgao
- Exemplos concretos de red flags detectadas (clausulas restritivas disfarcadas, indices eliminatorios)
- Conhecimento dos criterios nao escritos das comissoes
- Historico de pagamento dos orgaos
- SmartLic como tecnologia proprietaria

#### 11. Condicoes Comerciais
- Preco dinamico baseado em `--pacote`
- Condicao especial com destaque visual e prazo (hoje+15dias)
- Desconto (se `--desconto` informado): "Condicao especial: {X}% — valida ate {data+15dias}"
- Forma de pagamento: Boleto, PIX, Cartao
- Prazo de contrato: Minimo 3 meses; Cancelamento: 30 dias de antecedencia

#### 12. Proximos Passos
- Calendario de prazo dos editais (ancora de urgencia)
- CTA de ALTA CONVERSAO com urgencia baseada no edital mais proximo de encerrar
- CTA claro: "Para iniciar, responda este WhatsApp ou ligue para (48)9 8834-4559"

**Rodape em todas as paginas:** "Tiago Sasaki - Consultor de Licitacoes (48)9 8834-4559"

### Phase 4: Geracao do PDF (@dev)

```bash
python scripts/generate-proposta-pdf.py \
  --input docs/propostas/data-{CNPJ}-{data}.json \
  --output docs/propostas/proposta-{CNPJ}-{nome-slug}-{data}.pdf \
  --pacote semanal
```

Se o script nao existir, gerar o JSON de dados e criar o PDF via reportlab/weasyprint ou equivalente disponivel.

## Regras de Formatacao do PDF

- Acentuacao PT-BR automatica (fix_accents) aplicada a todos os textos do JSON
- Datas sempre no formato DD/MM/YYYY (nunca ISO)
- Travessao (—) no lugar de meia-risca (–) em todo o documento
- Tabelas usam KeepTogether para evitar quebra entre paginas
- Colunas dimensionadas para word-wrap (Paragraph), nunca truncamento de texto
- Todo conteudo e dinamico do JSON — nenhum valor hardcoded no script

## APIs Reference

| API | Endpoint | Auth | Rate Limit |
|-----|----------|------|------------|
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Nenhuma | 50 req/s |
| Portal Transparencia | `api.portaldatransparencia.gov.br/api-de-dados/` | `chave-api-dados` header | 90 req/min |
| PNCP | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | Nenhuma | ~100 req/min |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Nenhuma | ~60 req/min |

## Downstream

```
/intel-b2g leads de engenharia           → 150 leads brutos
/qualify-b2g engenharia                  → 35 Tier1
/proposta-b2g {CNPJ_tier1_top}          → PDF proposta personalizada
/cadencia-b2g engenharia --tier 1        → cadencia com proposta em anexo
```

## Params

$ARGUMENTS
