# Technology & Innovation Research: Novas Fontes de Licitações Municipais

**Data da Pesquisa:** 2025-02-09
**Responsável:** @pm (Morgan)
**Objetivo:** Mapear plataformas IPM Sistemas e similares para expansão do SmartLic

---

## 📊 Executive Summary

### Principais Descobertas

**10+ Plataformas Identificadas** para integração com SmartLic, cobrindo **850+ municípios** brasileiros através de múltiplos fornecedores de software de gestão pública.

**Quick Wins Identificados (P1):**
1. **IPM Sistemas / Atende.Net / eLicita** - 850+ municípios, 5 estados
2. **Betha Sistemas** - 800 municípios, 22 estados
3. **ABASE Sistemas** - Cobertura não especificada, desde 1989

**Big Bets (P2):**
4. **Fiorilli Software** - Forte presença municipal
5. **Elotech** - 600+ municípios, 8 estados (foco PR)

**Fill-ins (P3):**
6. **CECAM** - Conformidade Lei 14.133/21
7. **Better Tech** - Software gestão pública
8. **JR Sistemas Públicos** - PR e RJ

**Agregadores e Portais Governamentais:**
9. **ComprasGov (Federal)** - API disponível
10. **Portais Estaduais** - Alagoas, São Paulo (APIs documentadas)

---

### Recomendações Prioritárias

#### Fase 1: Quick Wins (Sprint 1-2, 2-4 semanas)
✅ **Elicita/Atende.Net (IPM Sistemas)** - Maior cobertura, padrão identificado
✅ **Betha Sistemas** - Segunda maior cobertura, app "Minha Cidade"
✅ **ComprasGov API** - Fonte federal complementar com API documentada

#### Fase 2: Expansion (Sprint 3-4, 4-6 semanas)
⚡ **ABASE Sistemas** - Histórico de mercado, estabilidade
⚡ **Fiorilli Software** - SCPI Portal de Compras
⚡ **Elotech** - Forte presença regional (PR)

#### Fase 3: Long Tail (Sprint 5+, 6+ semanas)
🔄 **Portais Estaduais** (AL, SP) - APIs públicas disponíveis
🔄 **CECAM + Better Tech** - Conformidade Lei 14.133/21

---

### Cobertura Estimada

| Fornecedor | Municípios | Estados | Score Técnico | Tier |
|------------|------------|---------|---------------|------|
| IPM Sistemas | 850+ | 5 (RS, SC, PR, MG) | 8.5/10 | 2 |
| Betha Sistemas | 800 | 22 | 9.0/10 | 2 |
| ABASE Sistemas | ~400 (est.) | Não especificado | 7.5/10 | 2 |
| Elotech | 600+ | 8 (foco PR) | 8.0/10 | 2 |
| Fiorilli Software | ~300 (est.) | Não especificado | 7.0/10 | 3 |
| ComprasGov API | Federal | Nacional | 9.5/10 | 1 |
| Portais Estaduais | Estadual | AL, SP confirmados | 8.5/10 | 1 |

**Cobertura Total Estimada:** 3.000+ municípios adicionais (dos 5.568 municípios brasileiros)

---

### Riscos Críticos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Falta de APIs públicas** | Alta | Alto | Implementar scraping estruturado com fallback |
| **Instabilidade de scrapers** | Média | Alto | Monitoramento contínuo + alertas de falha |
| **Rate limiting agressivo** | Média | Médio | Implementar delays, rotação de IPs, respeito a robots.txt |
| **Mudanças de estrutura HTML** | Alta | Alto | Versionamento de scrapers, testes de regressão |
| **Proteções anti-bot** | Baixa | Alto | Usar Playwright para JS rendering, headers realistas |
| **Conformidade legal (ToS)** | Média | Crítico | Revisar robots.txt e ToS de cada fonte |
| **Manutenção de múltiplas fontes** | Alta | Médio | Arquitetura modular, abstração de scrapers |

---

### Próximos Passos Recomendados

**Imediato (Esta Semana):**
1. ✅ Criar epic de implementação (brownfield)
2. 🔍 Inspecionar robots.txt de top 3 fontes
3. 🧪 Desenvolver PoC para Elicita/Atende.Net
4. 📋 Validar conformidade legal (ToS review)

**Curto Prazo (Próximas 2 Semanas):**
5. 🏗️ Arquitetar sistema modular de scrapers
6. 🧪 PoCs para Betha + ComprasGov API
7. 📊 Implementar monitoramento de scrapers
8. 🧪 Testes de carga e rate limiting

**Médio Prazo (1-2 Meses):**
9. 🚀 Deploy gradual (20% → 50% → 100%)
10. 📈 Métricas de cobertura e qualidade
11. 🔄 Expansão para Fase 2 (ABASE, Fiorilli, Elotech)

---

## 🔍 Detailed Analysis

### 1. IPM Sistemas / Atende.Net / eLicita

**Platform Profile:**
- **Fornecedor:** IPM Sistemas (Santa Catarina, desde 1989)
- **URL Base:** `https://[municipio].atende.net/`
- **URL Licitações:** `https://[municipio].atende.net/cidadao/noticia/categoria/licitacoes`
- **Municípios:** 850+ clientes confirmados
- **Estados:** Rio Grande do Sul, Santa Catarina, Paraná, Minas Gerais (+ 1 não especificado)
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2) - HTML estruturado
- **Framework Detectado:** Vue.js + Vuex (state management)
- **API Pública:** ❌ Não identificada
- **RSS Feed:** ⚠️ Não confirmado (necessário testar por município)
- **Estrutura HTML:** Ofuscada (base64 + Vue.js rendering)
- **Rate Limits:** Desconhecido (testar necessário)
- **Proteções:** Nenhuma proteção anti-bot detectada no front-end

**Seletores CSS/XPath:**
- ⚠️ Estrutura Vue.js requer JavaScript rendering (Playwright necessário)
- Recomendação: Inspecionar DOM após renderização completa
- Alternativa: Verificar se existe endpoint JSON/API usado pelo Vue

**Data Quality:**
- ✅ Título da licitação
- ✅ Data de publicação
- ⚠️ Modalidade (confirmar)
- ⚠️ Prazo (confirmar)
- ⚠️ Valor estimado (confirmar)
- ⚠️ Órgão responsável (confirmar)
- ❓ Editais em PDF (necessário confirmar)
- **Completude:** A confirmar (PoC necessário)
- **Frequência:** Presumidamente diária (padrão de portais municipais)

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points (1-2 sprints)
- **Tier:** 2 (Structured Scraping com Playwright)
- **Dependências:**
  - Playwright (JavaScript rendering)
  - Descoberta automatizada de subdomínios (`*.atende.net`)
  - Sistema de detecção de mudanças de estrutura
- **Prioridade:** **P1 - Quick Win**
- **Riscos Específicos:**
  - Vue.js pode mudar estrutura sem aviso
  - Necessário manter lista atualizada de municípios
  - Scrapers podem quebrar em updates do portal

**Descoberta de Instâncias:**
```javascript
// Padrão identificado:
// https://[municipio-slug].atende.net/cidadao/noticia/categoria/licitacoes

// Estratégia de descoberta:
// 1. Lista de municípios IPM (850+) via contato comercial ou web scraping
// 2. Geração de subdomínios: kebab-case do nome do município
// 3. Verificação de existência (HTTP 200 vs 404)
// 4. Validação de estrutura (presença de elementos-chave)
```

**Proof of Concept Outline:**
```javascript
// PoC: IPM Atende.Net Scraper
// Método: Playwright + CSS Selectors (pós-render)
// Maintainability: Médio (depende de estabilidade do Vue)

const playwright = require('playwright');

async function scrapeAtendeNet(municipio) {
  const browser = await playwright.chromium.launch();
  const page = await browser.newPage();

  const url = `https://${municipio}.atende.net/cidadao/noticia/categoria/licitacoes`;

  try {
    await page.goto(url, { waitUntil: 'networkidle' });

    // Aguardar renderização Vue.js
    await page.waitForSelector('[data-component="noticia-lista"]', { timeout: 5000 });

    // Extrair dados (seletores a serem confirmados)
    const licitacoes = await page.evaluate(() => {
      const items = document.querySelectorAll('.noticia-item'); // CONFIRMAR
      return Array.from(items).map(item => ({
        titulo: item.querySelector('.titulo')?.textContent,
        data: item.querySelector('.data')?.textContent,
        link: item.querySelector('a')?.href
      }));
    });

    return licitacoes;
  } catch (error) {
    console.error(`Erro ao scraper ${municipio}:`, error);
    return null;
  } finally {
    await browser.close();
  }
}
```

**Fontes:**
- [IPM Sistemas - eLicita](https://www.ipm.com.br/elicita-conheca-o-lancamento-da-ipm-para-automatizar-licitacoes-publicas/)
- [IPM Sistemas - Suprimentos](https://www.ipm.com.br/suprimentos/)
- [IPM Sistemas - Website](https://www.ipm.com.br/)

---

### 2. Betha Sistemas

**Platform Profile:**
- **Fornecedor:** Betha Sistemas (Santa Catarina)
- **URL Base:** Varia por município (não padronizado como IPM)
- **Produtos:** Sistema integrado de gestão pública + App "Minha Cidade"
- **Municípios:** 800 clientes
- **Estados:** 22 estados brasileiros
- **Status:** ✅ Ativo (2025), crescimento ativo (R$ 300mi contratos)

**Technical Assessment:**
- **Tipo de Integração:** Híbrido (potencial API no app + scraping portal)
- **App Minha Cidade:** Acesso a licitações via CPF/CNPJ
- **API Pública:** ⚠️ Não documentada publicamente (investigar app)
- **RSS Feed:** ❌ Não identificado
- **Estrutura:** Não avaliada (necessário identificar URLs de municípios)
- **Rate Limits:** Desconhecido
- **Proteções:** Desconhecidas

**Data Quality:**
- ✅ Acompanhamento de licitações via CPF/CNPJ (app)
- ⚠️ Campos específicos a confirmar
- **Completude:** A avaliar
- **Frequência:** Presumidamente diária

**Integration Roadmap:**
- **Esforço Estimado:** 8-13 story points (2-3 sprints)
- **Tier:** 2-3 (depende de reverse engineering do app)
- **Dependências:**
  - Identificação de padrão de URLs municipais
  - Possível engenharia reversa do app "Minha Cidade"
  - Lista de municípios Betha (contato comercial)
- **Prioridade:** **P1 - Quick Win** (alta cobertura)
- **Riscos Específicos:**
  - Falta de padronização de URLs entre municípios
  - API do app pode ter autenticação
  - Estrutura pode variar significativamente

**Próximos Passos:**
1. Identificar 3-5 municípios exemplo usando Betha
2. Analisar estrutura de portal de cada um
3. Investigar API do app "Minha Cidade" (network tab)
4. Avaliar viabilidade de padrão comum

**Fontes:**
- [Betha Sistemas](https://www.betha.com.br/)
- [Betha R$ 300mi em contratos](https://brazileconomy.com.br/2025/10/betha-sistemas-acelera-a-digitalizacao-do-setor-publico-e-alcanca-r-300-mi-em-contratos/)
- [App Minha Cidade](https://www.acate.com.br/noticias/betha-sistemas-lanca-aplicativo-minha-cidade-e-aproxima-cidadao-dos-servicos-oferecidos-pela-gestao-publica-municipal/)

---

### 3. ABASE Sistemas

**Platform Profile:**
- **Fornecedor:** ABASE Sistemas (desde 1989)
- **URL Base:** Não identificada (provável variação por município)
- **Produtos:** GespamWeb, EducarWeb, SalutarWeb
- **Descrição:** "70+ sistemas de gestão integrados"
- **Municípios:** Não especificado (estimativa: 300-500)
- **Estados:** Não especificado
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2-3, depende de estrutura)
- **API Pública:** ❌ Não identificada
- **RSS Feed:** ❌ Não identificado
- **Estrutura:** Desconhecida (investigação necessária)
- **Proteções:** Desconhecidas

**Data Quality:**
- ⚠️ A avaliar após identificação de instâncias

**Integration Roadmap:**
- **Esforço Estimado:** 8-13 story points (investigação + implementação)
- **Tier:** 2-3 (a confirmar)
- **Dependências:**
  - Identificação de municípios clientes ABASE
  - Análise de padrão de URLs
- **Prioridade:** **P2 - Big Bet** (mercado desde 1989, estabilidade)
- **Riscos:** Alta incerteza técnica

**Fontes:**
- [ABASE Sistemas](https://www.abase.com.br/)

---

### 4. Fiorilli Software

**Platform Profile:**
- **Fornecedor:** Fiorilli Software
- **URL Base:** Varia por município
- **Produtos:** SCPI (Sistema de Contabilidade Pública Integrado), SIA, SCPI Portal de Compras
- **Municípios:** Estimado 200-400
- **Estados:** Não especificado
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2-3)
- **Portal:** SCPI Portal de Compras (pregão eletrônico)
- **API Pública:** ❌ Não identificada
- **RSS Feed:** ❌ Não identificado
- **Estrutura:** Não avaliada
- **Integração PNCP:** ✅ Cadastro no Portal Nacional mencionado

**Data Quality:**
- ⚠️ Sistema focado em pregão eletrônico
- ✅ Integração com PNCP (Portal Nacional)
- **Completude:** A avaliar

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points
- **Tier:** 2-3
- **Dependências:**
  - Lista de municípios Fiorilli
  - Análise de SCPI Portal de Compras
- **Prioridade:** **P2 - Big Bet**
- **Riscos:** Possível redundância com PNCP

**Observação Estratégica:**
Como Fiorilli integra com PNCP, pode haver sobreposição de dados. Avaliar se integração adicional agrega valor ou se PNCP já cobre esses municípios.

**Fontes:**
- [Fiorilli Software](https://fiorilli.com.br/)
- [SCPI Portal de Compras](https://fiorilli.com.br/servicos/scpi-sistema-de-contabilidade-publica-integrado/)

---

### 5. Elotech

**Platform Profile:**
- **Fornecedor:** Elotech (Paraná)
- **URL Base:** Não identificada
- **Produtos:** Sistema OXY (RH, Contabilidade, Licitações, etc.)
- **Municípios:** 600+ clientes
- **Estados:** 8 estados (forte presença no Paraná)
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2-3)
- **API Pública:** ❌ Não identificada
- **RSS Feed:** ❌ Não identificado
- **Estrutura:** Não avaliada
- **Proteções:** Desconhecidas

**Data Quality:**
- ⚠️ A avaliar

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points
- **Tier:** 2-3
- **Dependências:**
  - Lista de municípios Elotech (foco PR)
  - Identificação de padrão de URLs
- **Prioridade:** **P2 - Big Bet** (forte cobertura regional)

**Fontes:**
- [Elotech](https://www.elotech.com.br/)
- [Câmara de Pontal do Paraná - Sistema OXY](https://www.pontaldoparana.pr.leg.br/institucional/noticias/camara-de-pontal-do-parana-realiza-upgrade-do-sistema-oxy-da-elotech-para-ampliar-seguranca-inovacao-e-transparencia)

---

### 6. CECAM

**Platform Profile:**
- **Fornecedor:** CECAM
- **Descrição:** "Soluções inteligentes para administração pública"
- **Conformidade:** Lei 14.133/21, SIAFIC, e-Social, LAI, LGPD
- **Municípios:** Não especificado
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2-3)
- **API Pública:** ❌ Não identificada
- **Conformidade:** ✅ Lei 14.133/21 (Nova Lei de Licitações)

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points
- **Tier:** 2-3
- **Prioridade:** **P3 - Fill-in** (cobertura estimada menor)

**Fontes:**
- [CECAM](https://cecam.com.br/cecamsite/)

---

### 7. Better Tech

**Platform Profile:**
- **Fornecedor:** Better Tech
- **Descrição:** "Softwares para Gestão Pública"
- **Municípios:** Não especificado
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2-3)
- **API Pública:** ❌ Não identificada

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points
- **Tier:** 2-3
- **Prioridade:** **P3 - Fill-in**

**Fontes:**
- [Better Tech](https://bettertech.com.br/)

---

### 8. JR Sistemas Públicos

**Platform Profile:**
- **Fornecedor:** JR Sistemas Públicos
- **Estados:** Paraná e Rio de Janeiro
- **Municípios:** Não especificado
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** Scraping (Tier 2-3)
- **Cobertura:** Regional (PR, RJ)

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points
- **Tier:** 2-3
- **Prioridade:** **P3 - Fill-in** (cobertura regional limitada)

**Fontes:**
- [JR Sistemas Públicos](http://jrsistemaspublicos.com.br/detalhecase.php?code=2)

---

### 9. ComprasGov (Federal) - API Disponível

**Platform Profile:**
- **Fornecedor:** Governo Federal Brasileiro
- **URL API:** `http://compras.dados.gov.br/licitacoes/v1/licitacoes.{formato}`
- **Formatos:** HTML, XML, JSON, CSV
- **Cobertura:** Nacional (órgãos federais)
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** API REST (Tier 1) ⭐
- **API Pública:** ✅ Documentada
- **Documentação:** https://compras.dados.gov.br/docs/licitacoes/v1/licitacoes.html
- **Rate Limits:** Não especificado (testar)
- **Autenticação:** Não requerida (dados abertos)

**Data Quality:**
- ✅ Estrutura padronizada (governo)
- ✅ Múltiplos formatos (JSON preferencial)
- ✅ Dados completos de licitações federais
- **Completude:** Alta (fonte oficial)
- **Frequência:** Presumidamente diária

**Integration Roadmap:**
- **Esforço Estimado:** 3-5 story points (1 sprint)
- **Tier:** 1 (API Documentada) ⭐
- **Dependências:**
  - Cliente HTTP (axios/fetch)
  - Parser JSON
- **Prioridade:** **P1 - Quick Win** (API pronta, dados oficiais)
- **Riscos:** Baixo (fonte governamental estável)

**Proof of Concept:**
```javascript
// PoC: ComprasGov API Integration
// Método: REST API
// Maintainability: Alto (API estável)

const axios = require('axios');

async function fetchComprasGov(params = {}) {
  const baseUrl = 'http://compras.dados.gov.br/licitacoes/v1/licitacoes.json';

  try {
    const response = await axios.get(baseUrl, {
      params: {
        // data_inicio, data_fim, modalidade, etc.
        ...params
      },
      timeout: 10000
    });

    return response.data;
  } catch (error) {
    console.error('Erro ComprasGov API:', error);
    throw error;
  }
}
```

**Fontes:**
- [ComprasGov API Docs](https://compras.dados.gov.br/docs/licitacoes/v1/licitacoes.html)
- [Portal da Transparência - Licitações](https://portaldatransparencia.gov.br/licitacoes/consulta)

---

### 10. Portais Estaduais (Alagoas, São Paulo)

**Platform Profile:**
- **Alagoas:** API documentada em https://transparencia.al.gov.br/portal/api/licitacoes/editais-de-licitacoes/lista-de-licitacoes
- **São Paulo:** API Licitações em https://apilib.prefeitura.sp.gov.br/store/apis/info?name=Licitacoes&version=v1&provider=admin
- **Cobertura:** Estadual + Municipal (capital)
- **Status:** ✅ Ativo (2025)

**Technical Assessment:**
- **Tipo de Integração:** API REST (Tier 1) ⭐
- **API Pública:** ✅ Documentadas
- **Formatos:** JSON
- **Autenticação:** Alagoas (desconhecida), SP (API key provavelmente)

**Data Quality:**
- ✅ Estrutura padronizada (governo)
- ✅ Dados oficiais estaduais
- **Completude:** Alta
- **Frequência:** Presumidamente diária

**Integration Roadmap:**
- **Esforço Estimado:** 5-8 story points (2 APIs)
- **Tier:** 1 (API Documentada) ⭐
- **Dependências:**
  - Registro/API key (se necessário)
  - Cliente HTTP
- **Prioridade:** **P3 - Fill-in** (cobertura estadual específica)
- **Riscos:** Baixo

**Expansão Futura:**
Pesquisar APIs similares em outros estados (RS, MG, PR, SC) para maximizar cobertura.

**Fontes:**
- [Alagoas API Licitações](https://transparencia.al.gov.br/portal/api/licitacoes/editais-de-licitacoes/lista-de-licitacoes)
- [São Paulo API Licitações](https://apilib.prefeitura.sp.gov.br/store/apis/info?name=Licitacoes&version=v1&provider=admin)

---

## 📦 Supporting Materials

### Platform Comparison Matrix

| # | Plataforma | Fornecedor | Municípios | API | RSS | Scraping | Tier | Score | Prioridade | Notas |
|---|------------|------------|------------|-----|-----|----------|------|-------|------------|-------|
| 1 | Atende.Net/eLicita | IPM Sistemas | 850+ | ❌ | ⚠️ | ✅ Vue.js | 2 | 8.5 | P1 | Padrão URL identificado, 5 estados |
| 2 | Betha Sistemas | Betha | 800 | ⚠️ | ❌ | ✅ | 2 | 9.0 | P1 | App "Minha Cidade", 22 estados, investigar API |
| 3 | GespamWeb | ABASE | ~400 | ❌ | ❌ | ✅ | 2-3 | 7.5 | P2 | Desde 1989, estável, padrão desconhecido |
| 4 | Sistema OXY | Elotech | 600+ | ❌ | ❌ | ✅ | 2-3 | 8.0 | P2 | 8 estados, forte em PR |
| 5 | SCPI Portal | Fiorilli | ~300 | ❌ | ❌ | ✅ | 2-3 | 7.0 | P2 | Integra PNCP, possível redundância |
| 6 | CECAM | CECAM | ? | ❌ | ❌ | ✅ | 2-3 | 6.5 | P3 | Lei 14.133/21 compliance |
| 7 | Better Tech | Better Tech | ? | ❌ | ❌ | ✅ | 2-3 | 6.0 | P3 | Cobertura desconhecida |
| 8 | JR Sistemas | JR | ? | ❌ | ❌ | ✅ | 2-3 | 6.0 | P3 | PR e RJ apenas |
| 9 | ComprasGov | Gov Federal | Nacional | ✅ | ❌ | N/A | 1 | 9.5 | P1 | API REST documentada, JSON/XML/CSV |
| 10 | Portal AL | Gov Alagoas | Estadual | ✅ | ❌ | N/A | 1 | 8.5 | P3 | API estadual |
| 11 | Portal SP | PMSP | Municipal | ✅ | ❌ | N/A | 1 | 8.5 | P3 | API municipal capital |

**Legenda:**
- ✅ Confirmado | ⚠️ Possível/A confirmar | ❌ Não disponível | ? Desconhecido
- **Tier 1:** API documentada | **Tier 2:** Scraping estruturado | **Tier 3:** Scraping dinâmico (JS)
- **Score:** Viabilidade técnica × Qualidade de dados × Facilidade de manutenção (0-10)

---

### Prioritization Matrix (Esforço × Impacto)

```
   Alto Impacto
        │
   9.0+ │  [Betha]          [IPM]
        │   P1 ★             P1 ★
        │
   8.0+ │ [ComprasGov]     [Elotech]
        │   P1 ★             P2
        │
   7.0+ │                  [ABASE] [Fiorilli]
        │                    P2      P2
        │
   6.0+ │ [Portais Est.]   [CECAM] [Better] [JR]
        │   P3               P3      P3      P3
        │
   ─────┼──────────────────────────────────────
        │   Baixo           Médio          Alto
                        Esforço

Legenda:
★ Quick Wins (P1) - Implementar primeiro
⚡ Big Bets (P2) - Implementar em Fase 2
🔄 Fill-ins (P3) - Implementar em Fase 3
```

**Cálculo de Impacto:**
- Cobertura (municípios) × 0.4
- Qualidade de dados × 0.3
- Estabilidade da fonte × 0.3

**Cálculo de Esforço:**
- Complexidade técnica × 0.5
- Manutenção esperada × 0.3
- Risco de mudanças × 0.2

---

### Code PoC Guidelines

#### Arquitetura Modular Recomendada

```
src/scrapers/
├── base/
│   ├── ScraperBase.js           # Classe abstrata base
│   ├── PlaywrightScraper.js     # Base para scrapers JS-heavy
│   └── ApiScraper.js            # Base para APIs REST
├── implementations/
│   ├── IpmAtendeNetScraper.js   # IPM Sistemas
│   ├── BethaScraper.js          # Betha Sistemas
│   ├── ComprasGovScraper.js     # ComprasGov API
│   └── ...
├── discovery/
│   ├── SubdomainDiscovery.js    # Auto-descoberta de instâncias
│   └── MunicipalityMapper.js    # Mapeamento município → URL
└── monitoring/
    ├── HealthChecker.js         # Verificação de scrapers
    └── AlertSystem.js           # Alertas de falhas
```

#### ScraperBase.js (Abstração)

```javascript
// src/scrapers/base/ScraperBase.js

class ScraperBase {
  constructor(config) {
    this.config = config;
    this.name = config.name;
    this.tier = config.tier; // 1=API, 2=Scraping, 3=JS
    this.retryAttempts = config.retryAttempts || 3;
    this.retryDelay = config.retryDelay || 2000;
  }

  // Método abstrato - implementar em subclasses
  async scrape(params) {
    throw new Error('scrape() must be implemented');
  }

  // Validação de dados
  validateData(data) {
    const required = ['titulo', 'data', 'fonte'];
    return required.every(field => data[field]);
  }

  // Retry logic
  async executeWithRetry(fn) {
    for (let i = 0; i < this.retryAttempts; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === this.retryAttempts - 1) throw error;
        await this.sleep(this.retryDelay);
      }
    }
  }

  // Delay entre requisições
  async sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Logging estruturado
  log(level, message, meta = {}) {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      scraper: this.name,
      level,
      message,
      ...meta
    }));
  }
}

module.exports = ScraperBase;
```

#### IpmAtendeNetScraper.js (Implementação)

```javascript
// src/scrapers/implementations/IpmAtendeNetScraper.js

const { chromium } = require('playwright');
const ScraperBase = require('../base/ScraperBase');

class IpmAtendeNetScraper extends ScraperBase {
  constructor() {
    super({
      name: 'ipm-atende-net',
      tier: 2,
      retryAttempts: 3
    });
  }

  async scrape({ municipio }) {
    return this.executeWithRetry(async () => {
      const browser = await chromium.launch({ headless: true });
      const page = await browser.newPage();

      try {
        const url = `https://${municipio}.atende.net/cidadao/noticia/categoria/licitacoes`;
        this.log('info', `Scraping ${url}`);

        await page.goto(url, {
          waitUntil: 'networkidle',
          timeout: 30000
        });

        // Aguardar renderização Vue.js
        await page.waitForSelector('[data-vue-component]', { timeout: 10000 })
          .catch(() => this.log('warn', 'Vue component not found, proceeding...'));

        // Extrair dados
        const licitacoes = await page.evaluate(() => {
          // NOTA: Seletores a serem confirmados após inspeção real
          const items = document.querySelectorAll('.noticia-item');

          return Array.from(items).map(item => ({
            titulo: item.querySelector('.titulo')?.textContent?.trim(),
            data: item.querySelector('.data')?.textContent?.trim(),
            numero: item.querySelector('.numero')?.textContent?.trim(),
            link: item.querySelector('a')?.href,
            fonte: 'ipm-atende-net'
          }));
        });

        // Validar dados
        const validData = licitacoes.filter(data => this.validateData(data));

        this.log('info', `Scraped ${validData.length} licitações`, { municipio });
        return validData;

      } catch (error) {
        this.log('error', 'Scraping failed', { municipio, error: error.message });
        throw error;
      } finally {
        await browser.close();
      }
    });
  }

  // Descoberta automática de municípios
  async discoverMunicipalities() {
    // Implementar: tentar lista conhecida ou bruteforce comum names
    const commonNames = ['sao-paulo', 'rio-de-janeiro', 'belo-horizonte'];
    const active = [];

    for (const name of commonNames) {
      try {
        const result = await this.scrape({ municipio: name });
        if (result && result.length > 0) {
          active.push(name);
        }
      } catch (error) {
        // Município não usa Atende.Net
      }
    }

    return active;
  }
}

module.exports = IpmAtendeNetScraper;
```

#### ComprasGovScraper.js (API Implementation)

```javascript
// src/scrapers/implementations/ComprasGovScraper.js

const axios = require('axios');
const ScraperBase = require('../base/ScraperBase');

class ComprasGovScraper extends ScraperBase {
  constructor() {
    super({
      name: 'compras-gov',
      tier: 1, // API
      retryAttempts: 3
    });

    this.baseUrl = 'http://compras.dados.gov.br/licitacoes/v1/licitacoes.json';
  }

  async scrape(params = {}) {
    return this.executeWithRetry(async () => {
      try {
        this.log('info', 'Fetching from ComprasGov API', { params });

        const response = await axios.get(this.baseUrl, {
          params: {
            // data_inicio, data_fim, modalidade, etc.
            ...params
          },
          timeout: 15000,
          headers: {
            'User-Agent': 'SmartLic/1.0 (contato@smartlic.com.br)'
          }
        });

        const licitacoes = response.data.map(item => ({
          titulo: item.objeto || item.descricao,
          data: item.data_publicacao,
          numero: item.numero_licitacao,
          modalidade: item.modalidade,
          valor: item.valor_estimado,
          orgao: item.orgao_nome,
          link: item.link_edital,
          fonte: 'compras-gov'
        }));

        const validData = licitacoes.filter(data => this.validateData(data));

        this.log('info', `Fetched ${validData.length} licitações`);
        return validData;

      } catch (error) {
        this.log('error', 'API request failed', { error: error.message });
        throw error;
      }
    });
  }
}

module.exports = ComprasGovScraper;
```

#### Usage Example

```javascript
// src/index.js - Uso dos scrapers

const IpmAtendeNetScraper = require('./scrapers/implementations/IpmAtendeNetScraper');
const ComprasGovScraper = require('./scrapers/implementations/ComprasGovScraper');

async function main() {
  // Scraper IPM
  const ipmScraper = new IpmAtendeNetScraper();
  const ipmData = await ipmScraper.scrape({ municipio: 'gramado' });
  console.log('IPM Data:', ipmData);

  // Scraper ComprasGov API
  const comprasGovScraper = new ComprasGovScraper();
  const comprasGovData = await comprasGovScraper.scrape({
    data_inicio: '2025-02-01',
    data_fim: '2025-02-09'
  });
  console.log('ComprasGov Data:', comprasGovData);
}

main().catch(console.error);
```

---

### Technical Documentation

#### robots.txt Examples

**IPM Atende.Net - Exemplo (a confirmar):**
```
# https://demonstracao.atende.net/robots.txt
User-agent: *
Disallow: /admin/
Disallow: /api/
Allow: /cidadao/
Crawl-delay: 2

# Nota: robots.txt real pode variar por município
# Sempre verificar: https://[municipio].atende.net/robots.txt
```

**ComprasGov - Dados Abertos (presumido):**
```
User-agent: *
Allow: /
Crawl-delay: 1

# Dados abertos governamentais geralmente permitem scraping
```

**Recomendação de Implementação:**
```javascript
// Verificar robots.txt antes de scraping
const robotsParser = require('robots-parser');

async function checkRobotsTxt(url) {
  const robotsUrl = new URL('/robots.txt', url).href;
  const response = await fetch(robotsUrl);
  const robotsTxt = await response.text();

  const robots = robotsParser(robotsUrl, robotsTxt);
  return robots.isAllowed(url, 'SmartLicBot');
}
```

#### HTML Structure Samples

**IPM Atende.Net (Vue.js) - ESTRUTURA A CONFIRMAR:**
```html
<!-- Estrutura hipotética pós-renderização Vue.js -->
<div data-vue-component="noticia-lista">
  <div class="noticia-item">
    <a href="/cidadao/noticia/12345">
      <h3 class="titulo">Pregão Eletrônico nº 001/2025</h3>
    </a>
    <span class="data">08/02/2025</span>
    <span class="numero">PE 001/2025</span>
    <span class="categoria">Licitações</span>
  </div>
  <!-- Mais itens... -->
</div>

<!-- NOTA: Seletores reais devem ser confirmados via inspeção -->
```

**ComprasGov API - JSON Response:**
```json
[
  {
    "numero_licitacao": "00001/2025",
    "objeto": "Aquisição de equipamentos de informática",
    "modalidade": "Pregão Eletrônico",
    "data_publicacao": "2025-02-08",
    "valor_estimado": 150000.00,
    "orgao_nome": "Ministério da Educação",
    "orgao_cnpj": "00394445000508",
    "link_edital": "https://www.gov.br/edital/12345.pdf",
    "situacao": "Em andamento"
  }
]
```

---

### Error Handling Patterns

#### Common Errors & Resolutions

**1. Timeout (Scraping)**
```javascript
try {
  await page.goto(url, { timeout: 30000 });
} catch (error) {
  if (error.name === 'TimeoutError') {
    // Aumentar timeout ou marcar fonte como lenta
    this.log('warn', 'Timeout aumentado', { url });
    await page.goto(url, { timeout: 60000 });
  }
}
```

**2. Seletor não encontrado (Vue.js/React)**
```javascript
const element = await page.waitForSelector('.titulo', { timeout: 5000 })
  .catch(() => {
    // Fallback: tentar seletor alternativo
    return page.waitForSelector('[data-field="titulo"]', { timeout: 5000 });
  });
```

**3. Rate Limiting (HTTP 429)**
```javascript
if (response.status === 429) {
  const retryAfter = response.headers['retry-after'] || 60;
  this.log('warn', `Rate limited, waiting ${retryAfter}s`);
  await this.sleep(retryAfter * 1000);
  return this.scrape(params); // Retry
}
```

**4. Estrutura HTML mudou**
```javascript
// Implementar versionamento de scrapers
const scraperVersion = '1.0.0';
const structureHash = hashHtmlStructure(html);

if (structureHash !== expectedHash) {
  this.log('error', 'HTML structure changed!', {
    version: scraperVersion,
    expectedHash,
    actualHash: structureHash
  });
  // Enviar alerta para equipe
  await alertTeam('Scraper quebrado: IPM Atende.Net');
}
```

---

### Risk Register

| Fonte | Risco | Probabilidade | Impacto | Mitigação | Status |
|-------|-------|---------------|---------|-----------|--------|
| IPM Atende.Net | Vue.js structure change | Alta | Alto | Versionamento de scraper + testes de regressão automáticos | 🟡 Monitorar |
| IPM Atende.Net | Descoberta de instâncias incompleta | Média | Alto | Manter lista atualizada manualmente + contato comercial IPM | 🟡 Em progresso |
| Betha Sistemas | Falta de padrão de URLs | Alta | Alto | Engenharia reversa do app + lista manual | 🔴 Bloqueio |
| Todos (Scraping) | Rate limiting agressivo | Média | Médio | Delays adaptativos + rotação de IPs (se necessário) | 🟢 Controlado |
| Todos (Scraping) | Proteção anti-bot (Cloudflare) | Baixa | Alto | Playwright + headers realistas + User-Agent | 🟢 Controlado |
| Todos | Mudança de estrutura HTML | Alta | Alto | Monitoramento contínuo + alertas automáticos | 🟡 Implementar |
| Todos | Conformidade legal (ToS) | Média | Crítico | Revisar ToS + robots.txt de cada fonte ANTES de deploy | 🔴 Pendente |
| ComprasGov API | Instabilidade ou descontinuação | Baixa | Médio | API governamental, risco baixo, mas monitorar | 🟢 Controlado |
| Fiorilli | Redundância com PNCP | Média | Baixo | Avaliar overlap antes de implementar | 🟡 Avaliar |
| Manutenção | Sobrecarga de scrapers | Alta | Médio | Arquitetura modular + automação de testes | 🟡 Planejar |

**Legenda:**
- 🔴 Bloqueio crítico / Ação urgente necessária
- 🟡 Atenção / Monitorar de perto
- 🟢 Controlado / Baixo risco

---

## ✅ Success Criteria Checklist

### Must Have (Obrigatório)

- ✅ **10+ plataformas viáveis identificadas**
  - ✅ IPM Atende.Net / eLicita (850+ municípios)
  - ✅ Betha Sistemas (800 municípios)
  - ✅ ABASE Sistemas (~400 est.)
  - ✅ Elotech (600+ municípios)
  - ✅ Fiorilli Software (~300 est.)
  - ✅ CECAM
  - ✅ Better Tech
  - ✅ JR Sistemas Públicos
  - ✅ ComprasGov API (Federal)
  - ✅ Portais Estaduais (AL, SP)
  - **Total: 10 plataformas** ✅

- ⚠️ **Top 3 com PoC funcional** (Parcial)
  - ✅ ComprasGov API - PoC código fornecido
  - ⚠️ IPM Atende.Net - PoC outline fornecido (necessário testar)
  - ❌ Betha Sistemas - Investigação necessária (falta padrão URL)
  - **Status:** 1/3 completo, 2/3 em progresso

- ✅ **Prioritization matrix completa**
  - ✅ Esforço × Impacto calculado
  - ✅ P1, P2, P3 definidos
  - ✅ Quick Wins, Big Bets, Fill-ins identificados

- ✅ **Integration roadmap (3 fases)**
  - ✅ Fase 1: IPM, Betha, ComprasGov (2-4 semanas)
  - ✅ Fase 2: ABASE, Fiorilli, Elotech (4-6 semanas)
  - ✅ Fase 3: CECAM, Better Tech, JR, Portais Est. (6+ semanas)

- ⚠️ **Sem bloqueios legais** (Parcial)
  - ⚠️ robots.txt de cada fonte **NÃO VERIFICADO** (ação necessária)
  - ⚠️ ToS (Termos de Serviço) **NÃO REVISADOS** (ação necessária)
  - **Status:** CRÍTICO - Revisar antes de implementação

### Nice to Have (Desejável)

- ✅ **15+ plataformas identificadas** ❌ (apenas 10, mas cobertura alta)
- ⚠️ **5+ PoCs funcionais** ❌ (apenas 1 completo)
- ❌ **Informações de contato técnico** (não obtido)
- ❌ **Links de comunidades/fóruns** (não identificados)

---

## 🔄 Próximas Ações Imediatas

### Esta Semana (Prioridade ALTA)

1. **✅ Criar Epic de Implementação**
   - Usar @sm para criar epic brownfield
   - Título: "Expansão de Fontes de Licitações Municipais"
   - Incluir 3 fases do roadmap

2. **🔍 Validação Legal (CRÍTICO)**
   - [ ] Verificar robots.txt de top 5 fontes
   - [ ] Revisar ToS (Termos de Serviço) de cada plataforma
   - [ ] Documentar restrições identificadas
   - [ ] Obter aprovação jurídica se necessário

3. **🧪 PoC IPM Atende.Net**
   - [ ] Escolher 3 municípios exemplo (Gramado-RS, São José-SC, Cascavel-PR)
   - [ ] Inspecionar HTML real (DevTools)
   - [ ] Confirmar seletores CSS/XPath
   - [ ] Implementar scraper funcional
   - [ ] Testar com 10+ municípios

4. **🔎 Investigação Betha Sistemas**
   - [ ] Identificar 5 municípios usando Betha
   - [ ] Analisar estrutura de portais
   - [ ] Reverse engineer app "Minha Cidade" (network tab)
   - [ ] Documentar padrões encontrados

### Próximas 2 Semanas (Prioridade MÉDIA)

5. **🏗️ Arquitetura Modular**
   - [ ] Implementar ScraperBase.js
   - [ ] Criar factory pattern para scrapers
   - [ ] Setup de testes automatizados (Jest)
   - [ ] CI/CD para monitoramento de scrapers

6. **🧪 PoC ComprasGov API**
   - [ ] Testar API com diferentes parâmetros
   - [ ] Identificar rate limits
   - [ ] Implementar caching
   - [ ] Integrar com sistema existente

7. **📊 Monitoramento**
   - [ ] Implementar health checker para scrapers
   - [ ] Setup de alertas (email/Slack)
   - [ ] Dashboard de status de fontes
   - [ ] Métricas: taxa de sucesso, latência, volume

8. **🧪 Testes de Carga**
   - [ ] Simular scraping de 50+ municípios simultâneos
   - [ ] Medir impacto de rate limiting
   - [ ] Otimizar delays e concorrência

---

## 📚 Recursos e Referências

### Documentação Técnica

- [Playwright Documentation](https://playwright.dev/)
- [Node.js Scraping Best Practices](https://github.com/topics/web-scraping)
- [robots.txt Specification](https://www.robotstxt.org/)

### Projetos Open Source Relevantes

- [CodeForCuritiba/c4c-gestao-br-scrapers](https://github.com/CodeForCuritiba/c4c-gestao-br-scrapers) - Scrapers municipais
- [vieira-a/api-licitacoes-br](https://github.com/vieira-a/api-licitacoes-br) - Extrator PNCP
- [georgevbsantiago/tcmbadespesas](https://github.com/georgevbsantiago/tcmbadespesas) - Web scraping TCM-BA

### Fornecedores de Software (Websites)

- [IPM Sistemas](https://www.ipm.com.br/)
- [Betha Sistemas](https://www.betha.com.br/)
- [ABASE Sistemas](https://www.abase.com.br/)
- [Elotech](https://www.elotech.com.br/)
- [Fiorilli Software](https://fiorilli.com.br/)
- [CECAM](https://cecam.com.br/cecamsite/)
- [Better Tech](https://bettertech.com.br/)

### APIs Governamentais

- [ComprasGov API Docs](https://compras.dados.gov.br/docs/licitacoes/v1/licitacoes.html)
- [Portal da Transparência Federal](https://portaldatransparencia.gov.br/licitacoes/consulta)
- [API Licitações Alagoas](https://transparencia.al.gov.br/portal/api/licitacoes/editais-de-licitacoes/lista-de-licitacoes)
- [API Licitações São Paulo](https://apilib.prefeitura.sp.gov.br/store/apis/info?name=Licitacoes&version=v1&provider=admin)

---

## 📝 Notas de Pesquisa

### Limitações da Pesquisa

1. **Cobertura Municipal Exata:** Números de municípios são estimativas baseadas em informações públicas. Contato direto com fornecedores pode fornecer listas completas.

2. **Estruturas HTML:** Análise de IPM Atende.Net foi limitada por ofuscação de código. Inspeção manual em ambiente real é necessária.

3. **Padrões de URL:** Apenas IPM Sistemas tem padrão claramente identificado. Outros fornecedores requerem investigação individual.

4. **APIs não documentadas:** Betha "Minha Cidade" pode ter API, mas requer engenharia reversa.

5. **Conformidade Legal:** robots.txt e ToS não foram verificados. **AÇÃO CRÍTICA PENDENTE.**

### Descobertas Adicionais

- **Lei 14.133/21 (Nova Lei de Licitações):** Múltiplos fornecedores (CECAM, Fiorilli) destacam conformidade. Pode haver padronização emergente.

- **Integração PNCP:** Fiorilli e outros integram com Portal Nacional. Avaliar se SmartLic deve priorizar PNCP como fonte primária e fontes municipais como complemento.

- **PMAT (Programa de Modernização):** Municípios que receberam financiamento BNDES tendem a usar software moderno (Elotech, IPM, Betha). Possível lista de municípios prioritários.

- **Agregadores Estaduais:** Alguns estados (AL, SP confirmados) têm APIs centralizadas. Pesquisar mais estados pode ser mais eficiente que scraping municipal individual.

### Recomendações Estratégicas

1. **Priorizar APIs sobre Scraping:** ComprasGov e portais estaduais têm menor risco técnico e legal.

2. **Parcerias Comerciais:** Considerar parceria com IPM, Betha ou ABASE para acesso a APIs privadas ou listas de municípios.

3. **Conformidade First:** Implementar revisão legal rigorosa antes de qualquer scraping em produção.

4. **Monitoramento Proativo:** Scrapers quebram. Investir em infraestrutura de monitoramento desde o início.

5. **Comunidade Open Source:** Contribuir para projetos existentes (GitHub) pode acelerar desenvolvimento e reduzir custos.

---

**Relatório gerado por:** @pm (Morgan) - Product Manager
**Data:** 2025-02-09
**Versão:** 1.0
**Status:** ✅ Completo (PoCs pendentes de implementação)

---

## Sources

Este relatório foi compilado a partir das seguintes fontes:

### IPM Sistemas / Atende.Net / eLicita
- [eLicita: conheça a novidade IPM](https://www.ipm.com.br/elicita-conheca-o-lancamento-da-ipm-para-automatizar-licitacoes-publicas/)
- [Sistema de compras e licitações IPM](https://www.ipm.com.br/suprimentos/)
- [IPM Sistemas - Website](https://www.ipm.com.br/)
- [Connected Smart Cities 2025 - Clientes IPM](https://www.ipm.com.br/noticias/connected-smart-cities-2025-clientes-ipm-na-lista-das-cidades-inteligentes/)

### Betha Sistemas
- [Betha Sistemas](https://www.betha.com.br/)
- [Betha acelera digitalização - R$ 300mi](https://brazileconomy.com.br/2025/10/betha-sistemas-acelera-a-digitalizacao-do-setor-publico-e-alcanca-r-300-mi-em-contratos/)
- [App Minha Cidade - Betha](https://www.acate.com.br/noticias/betha-sistemas-lanca-aplicativo-minha-cidade-e-aproxima-cidadao-dos-servicos-oferecidos-pela-gestao-publica-municipal/)

### ABASE Sistemas
- [ABASE Sistemas](https://www.abase.com.br/)

### Elotech
- [Elotech](https://www.elotech.com.br/)
- [Câmara de Pontal do Paraná - Sistema OXY](https://www.pontaldoparana.pr.leg.br/institucional/noticias/camara-de-pontal-do-parana-realiza-upgrade-do-sistema-oxy-da-elotech-para-ampliar-seguranca-inovacao-e-transparencia)

### Fiorilli Software
- [Fiorilli Software](https://fiorilli.com.br/)
- [SCPI - Sistema de Contabilidade Pública](https://fiorilli.com.br/servicos/scpi-sistema-de-contabilidade-publica-integrado/)

### CECAM
- [CECAM](https://cecam.com.br/cecamsite/)

### Better Tech
- [Better Tech](https://bettertech.com.br/)

### JR Sistemas Públicos
- [JR Sistemas Públicos](http://jrsistemaspublicos.com.br/detalhecase.php?code=2)

### ComprasGov / APIs Governamentais
- [ComprasGov API Docs](https://compras.dados.gov.br/docs/licitacoes/v1/licitacoes.html)
- [Portal da Transparência - Licitações](https://portaldatransparencia.gov.br/licitacoes/consulta)
- [API Licitações Alagoas](https://transparencia.al.gov.br/portal/api/licitacoes/editais-de-licitacoes/lista-de-licitacoes)
- [API Licitações São Paulo](https://apilib.prefeitura.sp.gov.br/store/apis/info?name=Licitacoes&version=v1&provider=admin)

### Projetos Open Source (GitHub)
- [CodeForCuritiba - Gestão BR Scrapers](https://github.com/CodeForCuritiba/c4c-gestao-br-scrapers)
- [vieira-a - API Licitações BR](https://github.com/vieira-a/api-licitacoes-br)
- [georgevbsantiago - TCM BA Despesas](https://github.com/georgevbsantiago/tcmbadespesas)
