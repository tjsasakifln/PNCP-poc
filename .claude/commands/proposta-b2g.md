# /proposta-b2g — Gerador de Proposta Comercial B2G

## Purpose

Gera um PDF de proposta comercial personalizada e profissional para um lead especifico de QUALQUER setor. Cruza perfil da empresa + panorama de mercado + historico gov para construir uma proposta irrecusavel que mostra ao decisor exatamente quanto dinheiro ele esta deixando na mesa.

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
| **Mensal** | R$997/mes | 1x/mes | Ate 3 editais | UF sede | Comercial |
| **Semanal (Rec.)** | R$1.500/mes | 4x semanal + 1x mensal | Ate 8 editais | UF sede + limitrofes (de `uf_abrangencia.semanal`) | Estendido |
| **Diario** | R$2.997/mes | Diario + semanal + mensal | Ilimitada | Cobertura ampla (de `uf_abrangencia.diario`) | Dedicado |

Todos os pacotes tem desconto anual: pague 10, leve 12.

Se `--pacote` nao for informado, o command seleciona automaticamente baseado no tier/score do `/qualify-b2g`.

**Cobertura de UFs e dinamica:** O campo `uf_abrangencia` no JSON de dados define quais UFs cada pacote cobre, calculado a partir da UF-sede da empresa. Nunca hardcodar UFs na proposta.

## Principios de Conversao

- **Autoridade**: Tiago Sasaki e consultor especializado em licitacoes publicas com experiencia comprovada. Analisa editais profissionalmente, identificando armadilhas que eliminam licitantes desavisados.
- **Escassez temporal**: Novos editais sao publicados toda semana. Cada semana sem monitoramento = oportunidades perdidas. O CTA usa urgencia generica, nunca datas de editais especificos.
- **Prova de valor**: A proposta em si E o produto. Mostra exatamente o que o relatorio /intel-busca entrega.
- **Reciprocidade**: Primeiro mes de cortesia para contratacoes na vigencia da proposta.
- **Contraste**: Tabela "COM vs SEM monitoramento" e "Consultoria Tradicional vs Esta Consultoria".
- **Dados reais, nao promessas**: Todo numero vem de fonte publica verificavel (PNCP, PCP v2, Portal da Transparencia, OpenCNPJ, IBGE).

## What It Does

### Phase 1: Coleta de Inteligencia (@data-engineer)

1. **Perfil da empresa** — OpenCNPJ (razao social, CNAE, porte, capital, cidade, QSA, decisor)
   ```bash
   CNPJ_LIMPO=$(echo "{CNPJ}" | tr -d './-')
   curl -s "https://api.opencnpj.org/${CNPJ_LIMPO}"
   ```

2. **Mapeamento CNAE -> Setor** — Determinar o setor da empresa para keywords e contexto
   - Ler `backend/sectors_data.yaml` e mapear o CNAE principal para um dos 15 setores
   - Se CNAE nao mapear diretamente, usar LLM fallback (GPT-4.1-nano): "Dado o CNAE {codigo} - {descricao}, qual dos seguintes setores e mais relevante: {lista_setores}?"
   - O setor determina: keywords de busca, faixa de valor, intro da proposta, exemplos de autoridade
   - **Campos derivados do mapeamento:**
     - `setor_intro`: Paragrafo introdutorio dinamico para a carta ao decisor, contextualizado ao setor (ex: "O mercado de licitacoes para {setor} movimenta R${valor} anualmente em {UFs}..." — nunca texto especifico de construcao/engenharia)
     - `uf_abrangencia`: Dict com chaves `semanal` (lista de UFs proximas da sede) e `diario` (lista ampla de UFs regionais). Calculado a partir da UF-sede da empresa.
     - `taxa_vitoria_setor`: Float, default 0.20. Ajustavel por setor (ex: TI=0.25, construcao=0.15, saude=0.20)
     - `autoridade_exemplos`: Lista de 4 bullets genericos de autoridade (ex: "Identificacao de clausulas restritivas disfarcadas", "Analise de indices financeiros eliminatorios", "Verificacao de conformidade documental completa", "Deteccao de exigencias acima do permitido pela Lei 14.133")

3. **Panorama do mercado** — Executar `python scripts/build-proposta-data.py {CNPJ_LIMPO} --pacote {pacote}`
   - O script coleta PNCP, detecta setor, filtra keywords, agrega volumes
   - Output: `docs/propostas/data-{CNPJ}-{YYYY-MM-DD}.json`
   - **NAO buscar historico de contratos** — suprimido da proposta
   - **NAO listar editais individuais** — apenas volumes e valores agregados
   - Se script falhar, coletar manualmente: OpenCNPJ + PNCP por UF/modalidade

4. **Cross-reference qualify** — Se `--from-qualify` fornecido, puxar score e tier do lead

### Phase 2: Calculo de ROI (@analyst)

O coracao da proposta. Demonstrar matematicamente o retorno do investimento.

**Metricas calculadas:**

1. **Volume de oportunidades no setor** — Total de editais abertos no setor nas UFs de interesse
   ```
   Editais_setoriais_abertos = Total de editais encontrados na varredura
   ```

2. **Valor em disputa** — Soma dos valores estimados dos editais do setor
   ```
   Valor_em_disputa = SUM(valor_estimado dos editais encontrados)
   ```

3. **Taxa de vitoria estimada** — Baseada no historico do lead ou default do setor
   ```
   Taxa_vitoria = taxa_vitoria_setor (default 0.20, ajustavel)
   Se historico disponivel: Contratos_ganhos / Participacoes_estimadas
   ```

4. **Receita incremental projetada** — O que o lead ganharia com a consultoria
   ```
   Receita_incremental = Valor_em_disputa x Taxa_vitoria x Fator_melhoria(1.3)
   ```

5. **ROI da consultoria**
   ```
   ROI = (Receita_incremental_anual - Custo_consultoria_anual) / Custo_consultoria_anual x 100
   ```

6. **Payback** — Em quantos meses o investimento se paga
   ```
   Payback_meses = Custo_consultoria_mensal / (Receita_incremental_mensal)
   ```

### Phase 3: Construcao da Proposta (@analyst + @dev)

**Estrutura do PDF (11 secoes):**

#### 1. Capa
- Dinamica: data=hoje, validade=hoje+15dias, CNPJ/nome do JSON
- Titulo: "Proposta de Consultoria em Licitacoes Publicas"
- Subtitulo: "Preparada exclusivamente para {Nome_Fantasia}"
- Visual limpo e profissional

#### 2. Carta ao Decisor
- Personalizada com deteccao de genero (Sr./Sra.) a partir do QSA
- Usa `setor_intro` do JSON para contextualizar o mercado do lead (dinamico por setor)
- Tom: consultivo, direto, sem floreios
- Nunca referenciar editais individuais com datas

#### 3. Diagnostico da Empresa
- Dinamico do JSON: pontos fortes/atencao derivados dos dados coletados
- Dados cadastrais (razao, fantasia, CNAE, porte, capital, cidade)
- **NAO incluir historico de contratos ou faturamento gov** — suprimido da proposta
- Pontos fortes e de atencao derivados exclusivamente dos dados cadastrais

#### 4. Panorama do Mercado
- Volume total: "{N} editais abertos no setor de {setor} nos ultimos 30 dias"
- Valor total em disputa: "R${valor} em oportunidades abertas"
- Distribuicao por faixa de valor (tabela: ate R$100k, R$100k-500k, R$500k-1M, R$1M-5M, acima R$5M)
- Distribuicao por modalidade (Pregao Eletronico, Concorrencia, etc.)
- Distribuicao por UF (tabela computada dos editais)
- **NAO listar editais individuais** — apenas agregados de volume e valor

#### 5. Dimensionamento da Oportunidade
- ROI computado a partir de contagens/valores reais dos editais
- Tabela comparativa COM vs SEM monitoramento
- Tabela de projecao anual
- Disclaimer: "Projecoes baseadas em dados publicos. Resultados dependem da execucao."

#### 6. O Que Cada Relatorio Entrega
- Showcase do que o /intel-busca entrega de fato:
  - **Perfil da Empresa** — Dados cadastrais, porte, capital, CNAE, QSA
  - **Resumo Executivo** — Visao geral do mercado e posicionamento da empresa
  - **Top 20 Editais Analisados** — 17 campos por edital (objeto, orgao, valor, UF, modalidade, status, datas, score, recomendacao, justificativa, etc.)
  - **Analise Documental** — Requisitos de habilitacao extraidos dos editais
  - **Recomendacao PARTICIPAR / NAO PARTICIPAR** — Veredicto claro com justificativa por edital
  - **Qualificacao Economica** — Analise de indices financeiros exigidos
  - **Plano de Acao** — Proximos passos concretos e priorizados
- Demonstra que a proposta EM SI e o produto
- **NAO incluir:** "Mapa Competitivo", "Diarios Oficiais", "Inteligencia de Mercado" (nao existem no intel-busca)

#### 7. Pacotes de Monitoramento
- 3 tiers: Mensal R$997 | Semanal R$1.500 (RECOMENDADO) | Diario R$2.997
- Cobertura de UFs dinamica: usa `uf_abrangencia.semanal` e `uf_abrangencia.diario` do JSON
- Comparativo rapido entre pacotes
- Desconto anual destacado: pague 10, leve 12

#### 8. Quem Analisa Seus Editais
- Secao de AUTORIDADE (generica, aplicavel a qualquer setor)
- Experiencia comprovada em analise de licitacoes publicas
- Usa `autoridade_exemplos` do JSON (4 bullets genericos):
  - Identificacao de clausulas restritivas disfarcadas
  - Analise de indices financeiros eliminatorios
  - Verificacao de conformidade documental completa
  - Deteccao de exigencias acima do permitido pela Lei 14.133
- SmartLic como tecnologia proprietaria de monitoramento e analise
- **Nunca mencionar cargo especifico em orgao publico, nunca mencionar "acompanhei obras" ou experiencia setorial especifica**

#### 9. Condicoes Comerciais
- Preco dinamico baseado em `--pacote`
- Condicao especial com destaque visual e prazo (hoje+15dias)
- Desconto (se `--desconto` informado): "Condicao especial: {X}% — valida ate {data+15dias}"
- Forma de pagamento: Boleto, PIX, Cartao
- Prazo de contrato: Minimo 3 meses; Cancelamento: 30 dias de antecedencia

#### 10. Proximos Passos
- CTA de ALTA CONVERSAO com urgencia generica
- Urgencia: "Novos editais sao publicados toda semana. Cada semana sem monitoramento sao oportunidades que passam despercebidas."
- **Nunca listar calendario de editais com datas especificas**
- **Nunca referenciar prazos de editais individuais**
- CTA claro: "Para iniciar, responda este WhatsApp ou ligue para (48)9 8834-4559"

#### 11. Fontes Consultadas
- Lista das fontes reais utilizadas:
  - PNCP — Portal Nacional de Contratacoes Publicas
  - PCP v2 — Portal de Compras Publicas
  - OpenCNPJ — Dados cadastrais de empresas
  - Portal da Transparencia — Verificacao de sancoes e impedimentos
  - PDFs dos Editais — Documentos originais quando disponiveis
  - IBGE — Dados demograficos e economicos regionais
- **Nunca listar:** Querido Diario, Mapa Competitivo, Diarios Oficiais

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
- Travessao no lugar de meia-risca em todo o documento
- Tabelas usam KeepTogether para evitar quebra entre paginas
- Colunas dimensionadas para word-wrap (Paragraph), nunca truncamento de texto
- Todo conteudo e dinamico do JSON — nenhum valor hardcoded no script

## Campos Obrigatorios no JSON de Dados

O JSON gerado na Phase 1 DEVE incluir estes campos para suportar a proposta sector-agnostic:

```json
{
  "cnpj": "12345678000190",
  "razao_social": "...",
  "nome_fantasia": "...",
  "cnae_principal": "4120-4/00",
  "setor_mapeado": "engenharia_construcao",
  "setor_nome": "Engenharia e Construcao",
  "setor_intro": "O mercado de licitacoes para engenharia e construcao...",
  "uf_sede": "SC",
  "uf_abrangencia": {
    "semanal": ["SC", "PR", "RS"],
    "diario": ["SC", "PR", "RS", "SP", "MG"]
  },
  "taxa_vitoria_setor": 0.15,
  "autoridade_exemplos": [
    "Identificacao de clausulas restritivas disfarcadas",
    "Analise de indices financeiros eliminatorios",
    "Verificacao de conformidade documental completa",
    "Deteccao de exigencias acima do permitido pela Lei 14.133"
  ],
  "panorama_mercado": {
    "total_editais": 142,
    "valor_total": 85000000.0,
    "por_faixa_valor": {},
    "por_modalidade": {},
    "por_uf": {}
  },
  "decisor": {},
  "historico_gov": {},
  "sancoes": {},
  "roi": {}
}
```

**Campo `historico_contratos` NAO deve existir no JSON** — dados de contratos sao usados apenas internamente para calculo de ROI, nunca expostos na proposta.

## Suppressions (nunca incluir na proposta)

- `historico_contratos` — nunca mostrar lista de contratos individuais
- Editais individuais com datas — nunca listar oportunidades abertas especificas
- "Mapa Competitivo" — nao existe no intel-busca
- "Querido Diario" / "Diarios Oficiais" — nao e fonte utilizada
- "Inteligencia de Mercado" como secao — nao existe como funcionalidade separada
- Calendario de editais em andamento — nao incluir datas de encerramento
- Referencias a cargo publico especifico (ex: "engenheiro da SIE/SC")
- Referencias a experiencia setorial especifica (ex: "acompanhei obras")

## APIs Reference

| API | Endpoint | Auth | Rate Limit |
|-----|----------|------|------------|
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Nenhuma | 50 req/s |
| Portal Transparencia | `api.portaldatransparencia.gov.br/api-de-dados/` | `chave-api-dados` header | 90 req/min |
| PNCP | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | Nenhuma | ~100 req/min |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Nenhuma | ~60 req/min |
| IBGE | `servicodados.ibge.gov.br` | Nenhuma | — |

## Downstream

```
/intel-b2g leads de {setor}                 -> 150 leads brutos
/qualify-b2g {setor}                        -> 35 Tier1
/proposta-b2g {CNPJ_tier1_top}             -> PDF proposta personalizada
/cadencia-b2g {setor} --tier 1              -> cadencia com proposta em anexo
```

## Params

$ARGUMENTS
