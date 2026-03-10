# /war-room-b2g — Dossiê de Participação em Edital B2G

## Purpose

Prepara um dossiê COMPLETO para participar de UM edital específico. Reúne tudo que o cliente precisa para tomar a decisão e executar: análise documental profunda, inteligência de preço, mapa competitivo, checklist de documentos, timeline de preparação, e simulador de proposta. O command mais valioso para o cliente: "me ajuda a GANHAR este edital."

**Output primário:** `docs/war-room/war-room-{cnpj_orgao}-{ano}-{seq}-{YYYY-MM-DD}.md` (dossiê completo)
**Output PDF:** `docs/war-room/war-room-{cnpj_orgao}-{ano}-{seq}-{YYYY-MM-DD}.pdf` (versão entregável)
**Rodapé:** "Tiago Sasaki - Consultor de Licitações (48)9 8834-4559"

---

## Usage

```
/war-room-b2g 80869886000143/2026/10
/war-room-b2g 80869886000143/2026/10 --cnpj 12345678000190
/war-room-b2g https://pncp.gov.br/app/editais/80869886000143/2026/10
/war-room-b2g 80869886000143/2026/10 --cnpj 12345678000190 --preco-alvo 850000
```

**Parâmetros:**
- `{cnpj_orgao}/{ano}/{sequencial}` — Identificador PNCP do edital (obrigatório)
- `--cnpj` — CNPJ da empresa que vai participar (opcional, enriquece a análise)
- `--preco-alvo` — Preço que o cliente pretende ofertar (opcional, valida contra mercado)

## What It Does

### Phase 1: Coleta Completa do Edital (@data-engineer)

**1a. Metadados do edital**
```bash
# Buscar dados do edital via PNCP
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={ano}0101\
  &dataFinal={hoje_YYYYMMDD}\
  &cnpj={cnpj_orgao}\
  &pagina=1&tamanhoPagina=50"
```
- Filtrar pelo sequencialCompra correto
- Extrair todos os metadados (objeto, orgão, UF, valor, modalidade, datas, situação)

**1b. Download de TODOS os documentos**
```bash
# Listar todos os documentos publicados
curl -s "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}/arquivos"

# Baixar CADA documento (não apenas o edital — TUDO)
for seq_doc in $(seq 1 $N_DOCUMENTOS); do
  curl -s -o /tmp/war-room-doc-${seq_doc}.pdf \
    "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}/arquivos/${seq_doc}"
done
```

**Documentos a baixar e analisar (TODOS disponíveis):**
- Edital (obrigatório)
- Termo de Referência (quando disponível — detalha escopo)
- Projeto Básico (quando disponível — especificações técnicas)
- Planilha de Quantitativos (quando disponível — preços unitários)
- Estudo Técnico Preliminar / ETP (quando disponível — justificativa da contratação)
- Minuta de contrato (quando disponível — obrigações contratuais)
- Outros anexos relevantes

**1c. Se `--cnpj` fornecido — perfil da empresa participante**
```bash
curl -s "https://api.opencnpj.org/${CNPJ_LIMPO}"
```
- Dados cadastrais, porte, capital social, CNAEs, QSA
- Será cruzado com requisitos de habilitação na Phase 2

### Phase 2: Análise Documental Profunda (Claude direto)

Diferente do report-b2g (análise rápida), aqui o Claude lê TODOS os documentos do edital integralmente.

**2a. Leitura integral dos documentos**

Para cada PDF baixado:
```
Read(file_path="/tmp/war-room-doc-{n}.pdf", pages="1-20")
Read(file_path="/tmp/war-room-doc-{n}.pdf", pages="21-40")
... (continuar até o fim do documento)
```

Ler o edital INTEIRO, não apenas primeiras 20 páginas. Se 80 páginas, ler em 4 blocos de 20.

**2b. Extração completa**

#### I. Ficha Técnica Completa

| Campo | Fonte |
|-------|-------|
| Número do edital/processo | Cabeçalho |
| Modalidade | Preâmbulo |
| Tipo/Critério de julgamento | Preâmbulo + seção de julgamento |
| Modo de disputa (aberto/fechado) | Preâmbulo |
| Regime de execução (empreitada preço global/unitário/integral) | Cláusula contratual |
| UASG/Código da unidade | Cabeçalho |
| Órgão responsável | Preâmbulo |
| Data/hora abertura das propostas | Seção de prazos |
| Data/hora do início da disputa | Seção de prazos (se diferente da abertura) |
| Data limite para impugnação | Seção de prazos (geralmente 3 dias úteis antes da abertura para pregão) |
| Data limite para esclarecimentos | Seção de prazos |
| Prazo de validade da proposta | Seção de proposta (geralmente 60-90 dias) |
| Prazo de execução | TR ou cláusula contratual |
| Prazo de vigência do contrato | Minuta de contrato |
| Local de execução/entrega | TR |
| Valor estimado (se público) | Edital ou sigiloso |
| Fonte de recursos / dotação | Seção financeira |
| Sistema eletrônico (ComprasGov, BLL, etc.) | Preâmbulo |

#### II. Objeto Detalhado

| Item | Extrair do TR/Projeto Básico |
|------|------------------------------|
| Descrição completa do objeto | Escopo detalhado (não apenas título) |
| Quantitativos | Tabela de itens com quantidades e unidades |
| Especificações técnicas | Requisitos de qualidade, normas, certificações |
| Obrigações do contratado | O que a empresa precisa fazer/entregar |
| Obrigações do contratante | O que o órgão fornece/faz |
| Cronograma de execução | Se detalhado no TR |
| Critérios de aceite | Como será avaliada a entrega |
| Garantia do objeto | Prazo de garantia pós-entrega |

#### III. Habilitação — Checklist Exaustivo

Para CADA requisito encontrado, extrair o texto EXATO do edital:

**Habilitação Jurídica:**
- [ ] Ato constitutivo (contrato social / estatuto)
- [ ] Documento de identidade do representante
- [ ] Procuração (se representante não for sócio)
- [ ] Outros: {texto exato do edital}

**Regularidade Fiscal e Trabalhista:**
- [ ] Prova de inscrição no CNPJ
- [ ] Prova de inscrição no cadastro estadual/municipal
- [ ] CND Federal (Receita + PGFN + INSS)
- [ ] CRF do FGTS
- [ ] CNDT (Trabalhista)
- [ ] CND Estadual
- [ ] CND Municipal (ISS)
- [ ] Outros: {texto exato}

**Qualificação Técnica:**
- [ ] Atestado(s) de capacidade técnica: {quantos, de que tipo, percentual mínimo, objeto similar exigido — COPIAR TEXTO EXATO}
- [ ] Registro no conselho profissional (CREA, CRA, etc.): {qual}
- [ ] Equipe técnica mínima: {profissionais, qualificações, vínculo exigido}
- [ ] Visita técnica: {obrigatória/facultativa, data limite, local, agendamento}
- [ ] Declaração de disponibilidade de equipamentos: {quais}
- [ ] Outros: {texto exato}

**Qualificação Econômico-Financeira:**
- [ ] Balanço patrimonial (último exercício)
- [ ] Índices contábeis: {LG ≥ X, SG ≥ X, LC ≥ X — valores exatos}
- [ ] Patrimônio líquido mínimo: R${valor} ({%} do valor estimado)
- [ ] Capital social mínimo: R${valor}
- [ ] Certidão negativa de falência/recuperação judicial
- [ ] Garantia de proposta: {%} do valor estimado, tipos aceitos
- [ ] Outros: {texto exato}

**Declarações:**
- [ ] Declaração de inexistência de fato impeditivo
- [ ] Declaração de cumprimento art. 7º CF (trabalho infantil)
- [ ] Declaração ME/EPP (se aplicável)
- [ ] Declaração de elaboração independente de proposta
- [ ] Outras: {texto exato}

#### IV. Condições da Proposta

| Item | Valor/Detalhe |
|------|---------------|
| Formato da proposta | Planilha de preços / Preço global / Por item |
| Moeda | Real (BRL) |
| Inclusões obrigatórias | BDI, encargos, tributos, frete, seguro, etc. |
| BDI máximo aceito | {%} (se especificado) |
| Encargos sociais referência | {%} (se especificado) |
| Proposta inexequível | Critério: <{X}% do valor estimado ou <{X}% da média |
| Marca/fabricante | Obrigatório informar? |
| Amostra/demonstração | Prazo e condições |
| Catálogo/folder | Obrigatório? |

#### V. Condições Contratuais

| Item | Valor/Detalhe |
|------|---------------|
| Vigência | {X} meses, prorrogável até {Y} |
| Garantia contratual | {%}, tipos: {caução/seguro/fiança} |
| Subcontratação | Permitida até {%} / Vedada |
| Consórcio | Permitido / Vedado |
| Pagamento | {X} dias após {evento} |
| Reajuste | Índice: {IPCA/INPC/outro}, periodicidade: {anual} |
| Penalidades | Multa diária: {%}, máx: {%}, suspensão: {prazo} |
| Rescisão | Condições |
| Seguro | Obrigatório? Tipo e valor |

#### VI. Tratamento Diferenciado

| Item | Valor |
|------|-------|
| Exclusivo ME/EPP | Sim/Não (itens <R$80k) |
| Cota reservada ME/EPP | Sim/Não (até 25%) |
| Margem de preferência | {%} para {tipo} |
| Benefício Lei Complementar 123 | Empate ficto até 5%/10% |

#### VII. Red Flags e Alertas Detalhados

Analisar com olhar crítico e identificar:

| Tipo | O que procurar | Impacto |
|------|----------------|---------|
| **Direcionamento** | Especificações que apontam para marca/fornecedor único, exigências desproporcionais ao objeto | ALTO — considerar impugnação |
| **Prazo irreal** | Prazo de execução incompatível com escopo, prazo de entrega impossível | ALTO — risco de inadimplência |
| **Habilitação restritiva** | Atestados com quantitativos >50% em cada item (TCU limita), exigência de vínculo empregatício (vedado pela Lei 14.133) | ALTO — possível impugnação |
| **Risco financeiro** | Garantia >5% (limite legal), patrimônio líquido desproporcional, BDI imposto abaixo do mercado | MÉDIO — margem comprimida |
| **Cláusulas abusivas** | Penalidades desproporcionais, prazo de pagamento >30 dias, vedação de reajuste em contrato >12 meses | MÉDIO — risco contratual |
| **Ambiguidades** | Escopo indefinido, critérios de aceite vagos, quantitativos inconsistentes | MÉDIO — risco de aditivos / litígio |
| **Oportunidade de esclarecimento** | Pontos que podem ser questionados para esclarecer antes da proposta | BAIXO — ação proativa |

Para cada red flag, citar:
- O trecho EXATO do edital (com número da cláusula/página)
- O fundamento legal que sustenta a objeção (Lei 14.133, Acórdão TCU, etc.)
- Ação recomendada: Impugnar / Solicitar esclarecimento / Aceitar risco / Desistir

### Phase 3: Inteligência de Preço (inline /pricing-b2g)

Executar análise de preço contextualizada para ESTE edital específico:

**3a. Histórico de preços do órgão**
```bash
# Contratos anteriores do MESMO órgão para objetos similares (24 meses)
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={24_meses_atras_YYYYMMDD}\
  &dataFinal={hoje_YYYYMMDD}\
  &cnpj={cnpj_orgao}\
  &pagina=1&tamanhoPagina=50"
```
- Filtrar por objeto similar (keywords)
- Extrair valorTotalHomologado (preço efetivamente pago)

**3b. Preços de mercado**
- Buscar contratos de OUTROS órgãos para mesmo objeto
- Calcular: mediana, P25, P75, desconto médio sobre estimado
- Mesma metodologia do `/pricing-b2g`

**3c. Recomendação de preço**
| Estratégia | Valor | Desconto | Quando usar |
|------------|:-----:|:--------:|-------------|
| **Agressivo** | R${P25} | {X}% | Mercado competitivo, quer ganhar a qualquer custo |
| **Competitivo** | R${mediana} | {X}% | Equilíbrio preço × margem |
| **Conservador** | R${P75} | {X}% | Pouca competição ou técnica+preço |

Se `--preco-alvo` fornecido:
- Posicionar o preço-alvo vs distribuição do mercado
- "Seu preço está no P{X} — {abaixo/dentro/acima} da faixa competitiva"
- Alertar se abaixo do P10 (risco de inexequibilidade) ou acima do P90 (risco de perder)

### Phase 4: Mapa Competitivo (inline /report-b2g Phase 3b)

**4a. Incumbentes do órgão**
- Top 5 fornecedores que já contrataram com este órgão (mesmo setor)
- Enriquecimento via OpenCNPJ (porte, capital, cidade)

**4b. Se `--cnpj` fornecido — posição competitiva do cliente**
- O cliente já forneceu para este órgão? Quantas vezes?
- Porte do cliente vs porte dos incumbentes
- Capital social vs requisito de PL/capital mínimo
- UF do cliente vs local de execução

**4c. Nível de competição esperado**
- Baseado no histórico: quantos licitantes participaram na última licitação similar deste órgão?
- Estimativa: Baixa (<5), Média (5-10), Alta (10-20), Muito Alta (>20)

### Phase 5: Análise de Viabilidade — GO/NO-GO (@analyst)

**Se `--cnpj` fornecido**, cruzar TODOS os requisitos do edital com perfil REAL da empresa:

| Requisito | Exigido | Empresa tem? | Status |
|-----------|---------|:------------:|--------|
| Capital social mínimo R${X} | R${exigido} | R${real} | OK / FALHA |
| Índices contábeis (LG≥{X}) | {exigido} | {real ou "verificar"} | OK / VERIFICAR / FALHA |
| Atestado técnico — {descrição} | {quant. exigida} | {quant. estimada do cliente} | OK / PARCIAL / FALHA |
| Equipe técnica — {profissional} | {exigido} | {verificar} | VERIFICAR |
| Registro no {conselho} | Sim | {verificar} | VERIFICAR |
| Certidão negativa de falência | Sim | {verificar} | VERIFICAR |
| ... | | | |

**Veredito:**

| Status | Critério | Recomendação |
|--------|----------|-------------|
| **GO** | Todos os requisitos OK ou VERIFICAR (nenhum FALHA) | Prosseguir com preparação |
| **GO COM RESSALVA** | 1-2 requisitos VERIFICAR em itens críticos | Prosseguir mas verificar ANTES os itens pendentes |
| **NO-GO** | 1+ requisito FALHA em item eliminatório | Não participar — explicar o motivo |
| **IMPUGNAR PRIMEIRO** | Requisito é FALHA mas possivelmente ilegal | Impugnar a cláusula antes de decidir |

### Phase 6: Plano de Ação — Timeline de Preparação (@analyst)

Gerar cronograma reverso a partir da data de encerramento:

```
D-{N} HOJE ─────────────────────────────────────── D-0 ENCERRAMENTO
  │                                                      │
  ├─ D-{X} Impugnação (se necessário)                   │
  ├─ D-{X} Esclarecimentos (se necessário)               │
  ├─ D-{X} Visita técnica (se obrigatória/facultativa)   │
  ├─ D-{X} Preparar atestados/certidões                  │
  ├─ D-{X} Elaborar proposta de preço                    │
  ├─ D-{X} Elaborar proposta técnica (se T+P)            │
  ├─ D-{X} Revisão final + assinaturas                   │
  ├─ D-{X} Upload no sistema                             │
  └─ D-0   Sessão de abertura                            │
```

Para cada tarefa:
- Data limite
- Responsável sugerido (empresário, contador, engenheiro, advogado)
- Documentos/inputs necessários
- Tempo estimado de preparo

### Phase 7: Geração do Dossiê (@dev)

**Estrutura do Dossiê (Markdown + PDF):**

```markdown
# WAR ROOM — Edital {número}
## {Órgão} — {Município}/{UF}
### {Objeto (1ª linha)}

**Data:** {data} | **Encerramento:** {data} ({N} dias)
**Valor estimado:** R${valor} | **Modalidade:** {tipo}

---

## 1. VEREDITO: {GO / GO COM RESSALVA / NO-GO / IMPUGNAR}
[Resumo em 3 bullets do motivo]

## 2. Ficha Técnica
[Tabela completa Phase 2 seção I]

## 3. O Que Está Sendo Comprado
[Seção II — escopo real em linguagem clara]

## 4. Checklist de Habilitação
[Seção III — checklist com status OK/VERIFICAR/FALHA por item]

## 5. Proposta de Preço
[Phase 3 — distribuição, recomendação, posição do preço-alvo]

## 6. Mapa Competitivo
[Phase 4 — incumbentes, nível de competição, posição do cliente]

## 7. Condições Contratuais
[Seção V — pagamento, garantia, penalidades, reajuste]

## 8. Red Flags e Alertas
[Seção VII — com fundamentação legal e ação recomendada]

## 9. Plano de Ação
[Phase 6 — timeline reversa com responsáveis]

## 10. Documentos a Preparar
[Lista EXATA de todos os documentos exigidos, consolidada do checklist]

---
Tiago Sasaki - Consultor de Licitações
(48)9 8834-4559
```

## Por Que Este é o Command Mais Valioso

| Métrica | Sem war-room | Com war-room |
|---------|:---:|:---:|
| Tempo de preparação | 3-5 dias | 1-2 dias |
| Risco de inabilitação | Alto (esquece documento) | Baixo (checklist completo) |
| Qualidade da proposta de preço | Chute | Baseado em dados reais |
| Detecção de red flags | Só descobre durante a sessão | Antecipado com ação |
| Decisão GO/NO-GO | Feeling | Análise objetiva |

## Downstream

```
/radar-b2g                               → identifica edital quente (score >80)
/war-room-b2g {edital} --cnpj {CNPJ}    → dossiê completo para participar
/cadencia-b2g {CNPJ}                     → se o war-room gerar uma conquista, usar como case na cadência
/retention-b2g {CNPJ}                    → registrar resultado no report mensal
```

## APIs Reference

| API | Endpoint | Uso |
|-----|----------|-----|
| PNCP Consulta | `/api/consulta/v1/contratacoes/publicacao` | Metadados + histórico |
| PNCP Arquivos | `/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos` | Lista documentos |
| PNCP Download | `/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}` | PDFs completos |
| PNCP Itens | `/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens` | Preços unitários |
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Perfil empresa + concorrentes |
| Portal Transparência | `api.portaldatransparencia.gov.br/api-de-dados/` | Sanções + contratos |

## Params

$ARGUMENTS
