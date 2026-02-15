# Relatório de Análise Comparativa: PNCP vs BidIQ

**Data:** 06/02/2026
**Autor:** Análise automatizada via Claude Code
**Objetivo:** Identificar oportunidades de UI/UX para diferenciar o BidIQ do acesso direto ao PNCP

---

## 1. Resumo Executivo

### Contexto
Foi realizada uma análise comparativa entre o Portal Nacional de Contratações Públicas (PNCP) e o sistema BidIQ (SmartLic), utilizando a busca por "uniforme escolar" como caso de teste.

### Principais Descobertas

| Aspecto | PNCP | BidIQ | Veredicto |
|---------|------|-------|-----------|
| **Filtros disponíveis** | 11 filtros | 4 filtros | PNCP superior |
| **UX/Interface** | Básica/Governamental | Moderna/Dark mode | BidIQ superior |
| **Inteligência** | Nenhuma | IA + Setores | BidIQ superior |
| **Export** | Manual | Automático | BidIQ superior |

### Conclusão
O BidIQ possui diferenciais importantes (IA, UX moderna, setores), mas **está faltando filtros essenciais** que o PNCP oferece nativamente. Isso representa uma perda de funcionalidade para o usuário.

---

## 2. Análise Detalhada dos Filtros

### 2.1 Filtros do PNCP (Portal Oficial)

```
┌─────────────────────────────────────────────────────────────┐
│                    FILTROS DO PNCP                          │
├─────────────────────────────────────────────────────────────┤
│ ✅ Palavra-chave (texto livre)                              │
│ ✅ Status da Licitação                                      │
│    ├── A Receber/Recebendo Proposta                         │
│    ├── Em Julgamento/Propostas Encerradas                   │
│    ├── Encerradas                                           │
│    └── Todos                                                │
│ ✅ Tipos de Instrumento Convocatório                        │
│ ✅ Modalidades da Contratação                               │
│    ├── Pregão Eletrônico                                    │
│    ├── Pregão Presencial                                    │
│    ├── Dispensa                                             │
│    ├── Credenciamento                                       │
│    ├── Concorrência                                         │
│    └── Outros...                                            │
│ ✅ Órgãos                                                   │
│ ✅ Unidades                                                 │
│ ✅ UFs (Estados)                                            │
│ ✅ Municípios                                               │
│ ✅ Esferas (Federal/Estadual/Municipal)                     │
│ ✅ Poderes (Executivo/Legislativo/Judiciário)               │
│ ✅ Fontes Orçamentárias                                     │
│ ✅ Tipos de Margens de Preferência                          │
│ ✅ Exigência de Conteúdo Nacional                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Filtros do BidIQ (Atual)

```
┌─────────────────────────────────────────────────────────────┐
│                    FILTROS DO BIDIQ                         │
├─────────────────────────────────────────────────────────────┤
│ ✅ Busca por Setor (9 setores pré-definidos)                │
│ ✅ Busca por Termos Específicos (tags múltiplas)            │
│ ✅ Estados (UFs) - com seleção visual por região            │
│ ✅ Período (Data inicial / Data final)                      │
│                                                             │
│ ❌ Status da Licitação - NÃO IMPLEMENTADO                   │
│ ❌ Modalidade de Contratação - NÃO IMPLEMENTADO             │
│ ❌ Faixa de Valor - NÃO IMPLEMENTADO                        │
│ ❌ Município - NÃO IMPLEMENTADO                             │
│ ❌ Esfera - NÃO IMPLEMENTADO                                │
│ ❌ Órgão - NÃO IMPLEMENTADO                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Gap Analysis

| Filtro | Prioridade | Justificativa |
|--------|------------|---------------|
| Status da Licitação | **P0 - CRÍTICO** | Fornecedores só querem ver licitações ABERTAS |
| Modalidade de Contratação | **P0 - CRÍTICO** | Empresas têm preferência por modalidades específicas |
| Faixa de Valor | **P0 - CRÍTICO** | Filtrar por capacidade de fornecimento |
| Esfera (Fed/Est/Mun) | **P1 - ALTA** | Muitas empresas só atendem determinadas esferas |
| Município | **P1 - ALTA** | Empresas locais precisam filtrar por cidade |
| Órgão | **P2 - MÉDIA** | Útil para quem já fornece para órgãos específicos |
| Tipos de Instrumento | **P3 - BAIXA** | Uso menos frequente |
| Poderes | **P3 - BAIXA** | Uso especializado |

---

## 3. Melhorias Necessárias

### 3.1 PRIORIDADE 0 - CRÍTICO (Implementar Imediatamente)

#### 3.1.1 Filtro de Status da Licitação

**Problema:** O BidIQ não permite filtrar por status. Usuários precisam ver apenas licitações abertas para enviar propostas.

**Solução:**
```
┌─────────────────────────────────────────────────────────────┐
│ Status da Licitação:                                        │
│                                                             │
│ ○ Recebendo Propostas (padrão)                              │
│ ○ Em Julgamento                                             │
│ ○ Encerradas                                                │
│ ○ Todas                                                     │
└─────────────────────────────────────────────────────────────┘
```

**Implementação Backend:**
- Adicionar parâmetro `status` na API: `recebendo_proposta`, `em_julgamento`, `encerrada`, `todos`
- Passar para a API do PNCP: `&status=recebendo_proposta`

**Implementação Frontend:**
- Adicionar radio buttons ou toggle group abaixo do campo de busca
- Default: "Recebendo Propostas" (comportamento atual implícito)

**Arquivos a modificar:**
- `frontend/app/page.tsx` - Adicionar componente de filtro
- `frontend/app/api/buscar/route.ts` - Passar parâmetro status
- `backend/main.py` - Aceitar e processar parâmetro status
- `backend/pncp_client.py` - Incluir status na query PNCP

---

#### 3.1.2 Filtro de Modalidade de Contratação

**Problema:** Empresas têm expertise em modalidades específicas (ex: só participam de Pregão Eletrônico).

**Solução:**
```
┌─────────────────────────────────────────────────────────────┐
│ Modalidade:                        [Todas as modalidades ▼] │
│                                                             │
│ ☑ Pregão Eletrônico                                         │
│ ☑ Pregão Presencial                                         │
│ ☑ Dispensa de Licitação                                     │
│ ☐ Concorrência                                              │
│ ☐ Credenciamento                                            │
│ ☐ Tomada de Preços                                          │
│ ☐ Convite                                                   │
│ ☐ Leilão                                                    │
└─────────────────────────────────────────────────────────────┘
```

**Implementação:**
- Multi-select dropdown com checkboxes
- Valores mapeados para códigos PNCP

**Arquivos a modificar:**
- `frontend/components/ModalidadeFilter.tsx` (novo)
- `backend/schemas.py` - Adicionar enum de modalidades
- `backend/filter.py` - Filtrar por modalidade

---

#### 3.1.3 Filtro de Faixa de Valor

**Problema:** Empresas têm capacidade financeira limitada e querem filtrar por valor estimado.

**Solução:**
```
┌─────────────────────────────────────────────────────────────┐
│ Valor Estimado:                                             │
│                                                             │
│ Mínimo: R$ [     50.000,00]  Máximo: R$ [  5.000.000,00]   │
│                                                             │
│ Ou selecione uma faixa:                                     │
│ ○ Até R$ 100 mil                                            │
│ ○ R$ 100 mil - R$ 500 mil                                   │
│ ○ R$ 500 mil - R$ 2 milhões                                 │
│ ● R$ 2 milhões - R$ 10 milhões                              │
│ ○ Acima de R$ 10 milhões                                    │
│ ○ Qualquer valor                                            │
└─────────────────────────────────────────────────────────────┘
```

**Implementação:**
- Slider duplo (range) ou campos numéricos
- Faixas pré-definidas para seleção rápida
- Formatação brasileira (R$ com pontos e vírgulas)

**Arquivos a modificar:**
- `frontend/components/ValorFilter.tsx` (novo)
- `backend/filter.py` - Já existe lógica de valor, expor na API
- `backend/schemas.py` - Adicionar valor_min/valor_max no request

---

### 3.2 PRIORIDADE 1 - ALTA (Próximo Sprint)

#### 3.2.1 Filtro de Esfera Governamental

**Problema:** Empresas que só fornecem para prefeituras não querem ver licitações federais.

**Solução:**
```
┌─────────────────────────────────────────────────────────────┐
│ Esfera:                                                     │
│                                                             │
│ [Federal] [Estadual] [Municipal]                            │
│     ☐         ☐          ☑                                  │
└─────────────────────────────────────────────────────────────┘
```

**Implementação:**
- Toggle buttons similares aos de UF
- Pode selecionar múltiplas esferas

---

#### 3.2.2 Filtro de Município

**Problema:** Empresas locais precisam filtrar por cidade específica.

**Solução:**
```
┌─────────────────────────────────────────────────────────────┐
│ Município: (disponível quando UF selecionada)               │
│                                                             │
│ [Digite o município...                              🔍]     │
│                                                             │
│ Sugestões:                                                  │
│ ├── São Paulo                                               │
│ ├── Campinas                                                │
│ └── Santos                                                  │
└─────────────────────────────────────────────────────────────┘
```

**Implementação:**
- Campo com autocomplete
- Carregar municípios dinamicamente baseado nas UFs selecionadas
- API do IBGE para lista de municípios

---

#### 3.2.3 Melhorar Performance da Busca

**Problema:** Busca em 27 estados leva ~4 minutos (muito lento).

**Soluções:**
1. **Busca paralela otimizada** - Aumentar concorrência de requests
2. **Cache de resultados** - Cache Redis por UF/período
3. **Busca incremental** - Mostrar resultados conforme chegam
4. **Estimativa de tempo mais precisa** - Baseada em histórico real

---

### 3.3 PRIORIDADE 2 - MÉDIA (Backlog)

#### 3.3.1 Filtro de Órgão/Entidade

```
┌─────────────────────────────────────────────────────────────┐
│ Órgão:                                                      │
│                                                             │
│ [Buscar órgão...                                    🔍]     │
│                                                             │
│ Órgãos frequentes:                                          │
│ ├── Ministério da Saúde                                     │
│ ├── Prefeitura de São Paulo                                 │
│ └── INSS                                                    │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Ordenação de Resultados

```
┌─────────────────────────────────────────────────────────────┐
│ Ordenar por:                    [Mais recente ▼]            │
│                                                             │
│ ○ Mais recente (padrão)                                     │
│ ○ Maior valor                                               │
│ ○ Menor valor                                               │
│ ○ Prazo mais próximo                                        │
│ ○ Relevância                                                │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.3 Paginação/Quantidade por Página

```
┌─────────────────────────────────────────────────────────────┐
│ Exibindo 1-20 de 688 resultados    [10] [20] [50] [100]     │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.4 PRIORIDADE 3 - BAIXA (Futuro)

| Melhoria | Descrição |
|----------|-----------|
| Filtro de Poderes | Executivo, Legislativo, Judiciário |
| Fontes Orçamentárias | Recursos federais, estaduais, próprios |
| Conteúdo Nacional | Margem de preferência para produtos nacionais |
| Busca Booleana | Suporte a AND, OR, NOT, aspas para frase exata |
| Filtros salvos | Salvar combinações de filtros frequentes |

---

## 4. Melhorias de UI/UX

### 4.1 Interface de Busca Proposta

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔍 SmartLic - Busca Inteligente                              [Dark] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Buscar por:  [Setor ▼] [Termos Específicos]                           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [uniforme] [escolar] [+Adicionar termo...]                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─ Status ──────────┐  ┌─ Modalidade ────────────────────────────┐   │
│  │ ● Abertas         │  │ ☑ Pregão Eletrônico  ☐ Concorrência    │   │
│  │ ○ Em julgamento   │  │ ☑ Dispensa           ☐ Credenciamento  │   │
│  │ ○ Encerradas      │  │ ☐ Pregão Presencial  ☐ Outras          │   │
│  │ ○ Todas           │  └─────────────────────────────────────────┘   │
│  └───────────────────┘                                                  │
│                                                                         │
│  ┌─ Valor Estimado ──────────────────────────────────────────────────┐ │
│  │  R$ [50.000] ════════════●═══════════════════●══════ R$ [5.000.000]│ │
│  │              Mínimo                            Máximo              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌─ Localização ─────────────────────────────────────────────────────┐ │
│  │  Esfera: [Federal] [Estadual] [●Municipal]                        │ │
│  │                                                                    │ │
│  │  Regiões: [Norte] [Nordeste] [Centro-Oeste] [●Sudeste] [Sul]     │ │
│  │                                                                    │ │
│  │  Estados: [AC][AL][AP][AM][BA][CE][DF][ES][GO][MA][MT][MS]       │ │
│  │           [●MG][PA][PB][PR][PE][PI][●RJ][RN][RS][RO][RR][SC]     │ │
│  │           [●SP][SE][TO]                     3 estados selecionados │ │
│  │                                                                    │ │
│  │  Município: [São Paulo, Campinas...               ] (opcional)    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌─ Período ─────────────────────────────────────────────────────────┐ │
│  │  De: [30/01/2026 📅]    Até: [06/02/2026 📅]    [Últimos 7 dias]  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌─ Filtros Avançados ─────────────────────────────────────────── ▼ ┐ │
│  │  Órgão: [Buscar...]  Poderes: [Todos ▼]  Fonte: [Todas ▼]        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│            [═══════════ 🔍 BUSCAR LICITAÇÕES ═══════════]              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Melhorias nos Resultados

#### Atual (PNCP):
```
┌─────────────────────────────────────────────────────────────┐
│ Edital nº 002/2026                                          │
│ Id contratação PNCP: 13694658000192-1-000008/2026          │
│ Modalidade: Pregão Eletrônico                               │
│ Última Atualização: 05/02/2026                              │
│ Órgão: MUNICIPIO DE PIRIPA                                  │
│ Local: Piripá/BA                                            │
│ Objeto: [LICITANET] - Registro de preços para futura...    │
└─────────────────────────────────────────────────────────────┘
```

#### Proposta (BidIQ melhorado):
```
┌─────────────────────────────────────────────────────────────┐
│ 🟢 ABERTA                                    ⏱️ 5 dias │
│                                                             │
│ Uniformes Escolares - Prefeitura de Piripá/BA              │
│ ══════════════════════════════════════════════════════════ │
│                                                             │
│ 💰 R$ 250.000,00          📋 Pregão Eletrônico             │
│ 🏛️ Prefeitura Municipal   📍 Piripá/BA                     │
│                                                             │
│ Registro de preços para aquisição de fardamento             │
│ (uniformes) para servidores públicos municipais...          │
│                                                             │
│ 📅 Abertura: 12/02/2026 às 09:00                           │
│                                                             │
│ [Ver Edital] [Baixar Documentos] [⭐ Favoritar]            │
└─────────────────────────────────────────────────────────────┘
```

**Melhorias propostas:**
1. **Badge de status visual** (verde=aberta, amarelo=julgamento, vermelho=encerrada)
2. **Countdown** para abertura de propostas
3. **Valor em destaque** (maior visibilidade)
4. **Título semântico** gerado por IA (não só "Edital nº X")
5. **Ícones** para melhor escaneabilidade
6. **Ações rápidas** (favoritar, ver edital, baixar)

---

## 5. Diferenciais a Manter e Fortalecer

### 5.1 O que o BidIQ já faz melhor que o PNCP

| Feature | Valor para o Usuário |
|---------|---------------------|
| **Busca por Setor** | Encontra licitações do nicho sem conhecer termos técnicos |
| **Resumo com IA** | Economia de horas de análise manual |
| **Seleção visual de UFs** | Muito mais rápido que dropdown |
| **Seleção por Região** | Um clique para selecionar 9 estados |
| **Export Excel automático** | Relatório pronto para análise |
| **Buscas salvas** | Não precisa reconfigurar filtros |
| **Dark mode** | Conforto visual para uso prolongado |
| **Progress indicator** | Feedback claro durante busca longa |

### 5.2 Sugestões para Fortalecer Diferenciais

1. **IA mais visível** - Destacar o resumo executivo como feature principal
2. **Alertas de novas licitações** - Notificação quando surgir licitação nos filtros salvos
3. **Análise de concorrência** - Mostrar quantas empresas já baixaram o edital
4. **Histórico de preços** - Comparar com licitações similares anteriores
5. **Score de relevância** - IA indicar % de match com o perfil da empresa

---

## 6. Roadmap de Implementação

### Sprint 1 (Atual + 2 semanas)
- [ ] Implementar filtro de Status da Licitação
- [ ] Implementar filtro de Modalidade de Contratação
- [ ] Implementar filtro de Faixa de Valor

### Sprint 2 (+ 2 semanas)
- [ ] Implementar filtro de Esfera (Federal/Estadual/Municipal)
- [ ] Implementar filtro de Município
- [ ] Otimizar performance da busca (parallelização)

### Sprint 3 (+ 2 semanas)
- [ ] Implementar filtro de Órgão com autocomplete
- [ ] Adicionar ordenação de resultados
- [ ] Implementar paginação configurável
- [ ] Melhorar cards de resultado (badges, ícones)

### Sprint 4 (+ 2 semanas)
- [ ] Filtros avançados (poderes, fontes)
- [ ] Busca booleana
- [ ] Filtros salvos como templates
- [ ] Alertas por email/push

---

## 7. Métricas de Sucesso

| Métrica | Atual | Meta |
|---------|-------|------|
| Filtros disponíveis | 4 | 10+ |
| Tempo médio de busca | ~4 min | < 1 min |
| Precisão dos resultados | ~60% | > 90% |
| Taxa de conversão (busca → download) | ? | > 40% |
| NPS de usuários | ? | > 50 |

---

## 8. Anexos

### 8.1 Screenshots de Referência

Os screenshots capturados durante a análise estão em:
- `.playwright-mcp/page-2026-02-06T11-09-18-221Z.png` - PNCP filtros
- `.playwright-mcp/page-2026-02-06T11-09-32-905Z.png` - PNCP resultados
- `.playwright-mcp/page-2026-02-06T11-10-06-740Z.png` - BidIQ interface
- `.playwright-mcp/page-2026-02-06T11-14-29-865Z.png` - BidIQ busca em progresso

### 8.2 APIs do PNCP Relevantes

```
Base URL: https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao

Parâmetros importantes:
- q: termo de busca
- uf: código do estado
- status: recebendo_proposta | em_julgamento | encerrada
- modalidadeId: código da modalidade
- valorMinimo / valorMaximo: faixa de valor
- dataPublicacaoInicio / dataPublicacaoFim: período
- codigoMunicipio: código IBGE do município
- esfera: federal | estadual | municipal
```

---

**Documento gerado automaticamente**
**SmartLic - Análise de Produto**
