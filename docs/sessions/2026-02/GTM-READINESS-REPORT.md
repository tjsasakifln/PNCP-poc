# Relatório de Prontidão GTM - Smart PNCP

**Data:** 2026-02-06
**Versão:** POC v0.3
**Objetivo:** Avaliar prontidão para lançamento com 50 usuários iniciais de diferentes setores

---

## Sumário Executivo

O sistema Smart PNCP está **funcionalmente pronto para GTM**, com fluxos principais operacionais. Identificamos **3 bugs críticos (P0)**, **3 problemas importantes (P1)** e **8 melhorias de UX** que devem ser endereçados em ordem de prioridade.

**Fontes de Dados:** Atualmente apenas PNCP está ativo. O sistema tem infraestrutura pronta para Portal de Compras Públicas e Licitar Digital, mas para os 50 usuários iniciais, **PNCP é suficiente** (fonte oficial do governo, mais completa).

**⚠️ BUG CRÍTICO DESCOBERTO:** Busca por "Termos Específicos" está quebrada - retorna 0 resultados enquanto PNCP oficial retorna 336 para mesma busca.

**Veredicto:** ⚠️ BLOQUEADO ATÉ CORREÇÃO DO BUG "TERMOS ESPECÍFICOS"

---

## Inspeção por Nível de Acesso

### 1. Usuário Master (marinalvabaron@gmail.com)

| Funcionalidade | Status | Observação |
|----------------|--------|------------|
| Login/Logout | OK | Fluxo normal |
| Busca por Setor | OK | 12 setores disponíveis |
| Filtros (UF, Data, Status, Modalidade, Valor) | OK | Todos funcionais |
| Download Excel | OK | 125 licitações em ~40s |
| Histórico | OK | 14 buscas registradas |
| Buscas Salvas | OK | 1/10 slots usados |
| Minha Conta | OK | Alteração de senha funcional |
| Página Planos | OK | Mostra "Sala de Guerra" ativo |

**BUG CRÍTICO IDENTIFICADO:**
- Master mostra "30 dias restantes" e "1000 créditos" - deveria ser ILIMITADO

### 2. Usuário Admin (tiago.sasaki@gmail.com)

| Funcionalidade | Status | Observação |
|----------------|--------|------------|
| Login/Logout | OK | |
| Badge Admin | OK | Ícone de escudo visível |
| Painel /admin | OK | Lista 4 usuários |
| Gerenciar Planos | OK | Dropdown funcional |
| Gerenciar Créditos | OK | Exibe corretamente |
| Criar Usuário | NÃO TESTADO | Botão existe |
| Excluir Usuário | NÃO TESTADO | Link existe |

**Admin corretamente configurado com ∞ créditos**

### 3. Usuário FREE (Gratuito)

| Funcionalidade | Status | Observação |
|----------------|--------|------------|
| Signup | OK | "Comece com 3 buscas gratuitas" |
| Login | OK | Email+Senha e Magic Link |
| Preview com Blur | IMPLEMENTADO | 5 itens visíveis, resto blur |
| CTA Upgrade | OK | Aparece sobre blur |
| Download Excel | BLOQUEADO | Conforme esperado |

**Implementação blur verificada no código:**
- `previewCount = 5` (hardcoded)
- Valores aparecem como "R$ ***"
- CTA "Ver Planos" funcional

---

## Análise Multidisciplinar dos Agentes

### @dev (Desenvolvimento)

**Bugs Funcionais:**
1. **[P0] CRÍTICO - Master com limite de créditos**
   - Arquivo: Supabase/profiles ou lógica de plano
   - Master tem `plan_type = "sala_de_guerra"` com 1000 créditos e expiração
   - DEVERIA: Master ilimitado sem expiração

2. **[P0] CRÍTICO - Busca por "Termos Específicos" quebrada**
   - Arquivo: `backend/filter.py` - função `aplicar_todos_filtros()`
   - **Sintoma:** Busca "notebook" em SP retorna 0 resultados
   - **PNCP Oficial:** Mesma busca retorna 336 resultados
   - **Causa:** Filtro de keywords do setor está sendo aplicado mesmo em modo "Termos Específicos"
   - **Log:** "1000 licitações encontradas, 0 passaram filtros" + "Sem palavras-chave do setor"
   - **Impacto:** TOTAL - usuários não conseguem buscar por termos customizados
   - **Evidência:** Screenshots `gtm-inspection-13-termos-especificos-bug.png` e `gtm-inspection-14-pncp-oficial-336-results.png`

3. **[P1] Erro JavaScript no Console**
   - Mensagem: "Illegal return statement"
   - Aparece em todas as páginas
   - Impacto: Possível quebra de funcionalidade não identificada

4. **[P2] Contador de buscas inconsistente**
   - Master: mostra "986 buscas restantes"
   - Admin: não mostra contador (correto para ∞)

**Código Positivo:**
- Componente LicitacoesPreview bem estruturado
- Retry logic no PNCP client funcionando
- Download Excel com nome descritivo
- Progress bar com 5 estágios informativos

### @qa (Qualidade)

**Testes Necessários Pré-GTM:**

1. **Fluxo Crítico - Busca → Download**
   - [ ] Busca retorna 0 resultados - mensagem adequada?
   - [ ] Busca com timeout do PNCP - retry funciona?
   - [ ] Download de arquivo grande (1000+ licitações)

2. **Edge Cases não testados:**
   - [ ] Usuário atinge limite de créditos
   - [ ] Sessão expira durante busca
   - [ ] Dois usuários mesma conta simultaneamente

3. **Regressão crítica:**
   - [ ] Filtro de status "Abertas" realmente filtra
   - [ ] Datas inválidas são rejeitadas
   - [ ] UFs selecionadas são enviadas corretamente

### @architect (Arquitetura)

**Riscos Técnicos para 50 usuários:**

1. **Rate Limiting PNCP** - MITIGADO
   - 10 req/s com exponential backoff implementado
   - OK para volume inicial

2. **Geração de Excel** - MONITORAR
   - Gerado em memória no backend
   - Para 1000+ licitações pode consumir RAM
   - Recomendação: Monitorar uso de memória Railway

3. **Cache de Download** - OK
   - TTL 10min em memória
   - Adequado para POC

**Débito Técnico (não bloqueante):**
- Logs estruturados não implementados
- Métricas de uso por setor não coletadas
- Sem rate limiting próprio (apenas do PNCP)

### @ux-design-expert (UX/UI)

**Pontos Positivos:**
- Dark mode elegante e consistente
- Progress bar informativa durante busca
- Seleção de UF por região intuitiva
- Badges de plano claros

**Frustrações Potenciais para 50 usuários:**

1. **[P1] Plano Consultor Ágil sem Download Excel**
   - R$ 297/mês e não pode baixar Excel
   - MUITO frustrante - principal deliverable

2. **[P2] Tempo de busca ~40s**
   - Aceitável com progress bar
   - Adicionar estimativa "~30s restantes"

3. **[P3] Histórico sem detalhes**
   - Não mostra filtros usados na busca
   - Difícil reproduzir busca anterior

4. **[P3] Campo município sem autocomplete**
   - Placeholder diz "Digite para buscar"
   - Mas não há sugestões automáticas

**Acessibilidade:**
- "Pular para conteúdo principal" - OK
- Atalhos de teclado disponíveis
- Contraste adequado no dark mode

### @devops (Infraestrutura)

**Status de Deploy:**
- Frontend: Railway (bidiq-frontend-production)
- Backend: Railway
- Domínio: bidiq-frontend-production.up.railway.app

**Monitoramento Necessário:**
1. [ ] Alertas de erro no console (atual: 1 erro JS)
2. [ ] Latência de resposta backend
3. [ ] Uso de memória (geração Excel)
4. [ ] Rate limit hits no PNCP

**Recomendações:**
- Configurar Sentry ou similar para erros JS
- Adicionar health check endpoint
- Configurar logs estruturados no Railway

---

## Lista de Ações Priorizadas

### P0 - CRÍTICO (Fazer ANTES do GTM)

| # | Ação | Responsável | Esforço |
|---|------|-------------|---------|
| 1 | **🔴 CORRIGIR busca "Termos Específicos" - retornando 0 resultados** | @dev | 2-4h |
| 2 | **Corrigir Master para créditos ilimitados** | @dev | 1h |
| 3 | **Investigar e corrigir "Illegal return statement"** | @dev | 2h |

### P1 - IMPORTANTE (Fazer na primeira semana)

| # | Ação | Responsável | Esforço |
|---|------|-------------|---------|
| 3 | Adicionar Download Excel ao plano Consultor Ágil | @pm/@dev | 30min |
| 4 | Adicionar estimativa de tempo na progress bar | @dev | 1h |
| 5 | Testar fluxo de limite de créditos atingido | @qa | 2h |

### P2 - DESEJÁVEL (Fazer nas primeiras 2 semanas)

| # | Ação | Responsável | Esforço |
|---|------|-------------|---------|
| 6 | Mostrar filtros usados no histórico de buscas | @dev | 3h |
| 7 | Implementar autocomplete de município | @dev | 4h |
| 8 | Configurar Sentry para monitoramento de erros | @devops | 2h |
| 9 | Adicionar métricas de uso por setor | @dev | 3h |

### P3 - BACKLOG (Pós-GTM)

| # | Ação | Responsável |
|---|------|-------------|
| 10 | Implementar alertas automáticos por setor |
| 11 | API pública para clientes enterprise |
| 12 | Dashboard de analytics interno |
| 13 | Exportação em outros formatos (CSV, PDF) |

---

## Checklist Final GTM

### Funcionalidades Core
- [x] Fluxo de busca funcionando
- [x] Download Excel funcionando
- [x] 12 setores configurados
- [x] Filtros avançados operacionais
- [x] Sistema de planos implementado
- [x] Preview com blur para FREE
- [x] Painel admin funcional

### Fontes de Dados (APIs)
- [x] PNCP ativo e funcionando
- [x] Infraestrutura multi-source implementada
- [ ] Portal de Compras Públicas (pós-GTM)
- [ ] Licitar Digital (pós-GTM)

### Bugs Pendentes
- [ ] **🔴 Busca "Termos Específicos" quebrada** (BUG P0 - BLOQUEANTE)
- [ ] **Master com créditos ilimitados** (BUG P0)
- [ ] **Erro JS console corrigido** (BUG P0)

### Testes
- [ ] Testes de edge cases

---

## Análise de Fontes de Dados (APIs)

### Status Atual: APENAS PNCP ATIVO

**Evidência:** Todas as licitações na planilha Excel mostram "publicado no PNCP" como fonte.

### APIs Configuradas no Sistema

| Fonte | Status | API Key | Gratuita | Observação |
|-------|--------|---------|----------|------------|
| **PNCP** | ATIVA | Não requer | Sim | Única fonte em uso |
| Portal de Compras Públicas | INATIVA | `PORTAL_COMPRAS_API_KEY` não configurada | Sim* | Código pronto, falta API key |
| Licitar Digital | INATIVA | `LICITAR_API_KEY` não configurada | Sim* | Código pronto, falta API key |
| BLL Compras | DESABILITADA | - | - | Sincroniza com PNCP (redundante) |
| BNC | DESABILITADA | - | - | Sincroniza com PNCP (redundante) |

*Gratuita: Algumas APIs são gratuitas ou têm tier gratuito para volume inicial.

### Infraestrutura Multi-Source

O sistema possui infraestrutura completa para múltiplas fontes (`backend/source_config/sources.py`):

```
source_config/
├── sources.py          # Configuração de 5 fontes
├── __init__.py
clients/
├── base.py             # Interface SourceAdapter
├── portal_compras_client.py  # Adapter Portal de Compras (PRONTO)
├── __init__.py
```

**Arquitetura implementada:**
- Consolidação de múltiplas fontes
- Deduplicação (strategy: "first_seen")
- Rate limiting por fonte
- Timeout configurável por fonte
- Prioridade de fontes (PNCP = 1, Portal = 2, Licitar = 3)

### Recomendação para GTM

**PARA OS 50 USUÁRIOS INICIAIS:**
- Manter apenas PNCP é **SUFICIENTE**
- PNCP é a fonte oficial e mais completa do governo
- Outras fontes (Portal, Licitar) são agregadores que também publicam no PNCP

**PARA ESCALA FUTURA (pós-GTM):**
- Ativar Portal de Compras Públicas para licitações não-PNCP
- Solicitar API keys gratuitas:
  - Portal: https://bibliotecapcp.zendesk.com/hc/pt-br/articles/4593549708570
  - Licitar: Contato comercial necessário
- Benefício: Captura de licitações em trânsito (ainda não no PNCP)

### Ação Recomendada

| Prioridade | Ação | Esforço |
|------------|------|---------|
| P3 (Pós-GTM) | Solicitar API key Portal de Compras Públicas | 1 dia |
| P3 (Pós-GTM) | Configurar `PORTAL_COMPRAS_API_KEY` no Railway | 10min |
| P3 (Pós-GTM) | Testar consolidação multi-source | 4h |
| Backlog | Avaliar integração Licitar Digital | - |

### Conclusão APIs

**Para GTM com 50 usuários: PNCP é suficiente.**

O sistema tem a arquitetura pronta para escalar com múltiplas fontes quando necessário. A ativação de fontes adicionais é uma questão de configuração (API keys), não de desenvolvimento.

---

## Teste de Comparação: Smart PNCP vs PNCP Oficial

### Metodologia

Teste realizado para verificar se os resultados do Smart PNCP são consistentes com o portal oficial do governo, já que usuários inevitavelmente farão essa comparação.

### Teste Executado

| Parâmetro | Valor |
|-----------|-------|
| **Busca** | "notebook" (Termos Específicos) |
| **UF** | SP |
| **Período** | 30/01/2026 - 06/02/2026 |
| **Status** | Abertas (A Receber/Recebendo Proposta) |

### Resultados

| Sistema | Licitações Encontradas | Resultado Final |
|---------|----------------------|-----------------|
| **PNCP Oficial** | 336 | ✅ 336 exibidas |
| **Smart PNCP** | 1000 (da API) | ❌ **0 aprovadas** |

### Análise do Bug

**Fluxo observado no Smart PNCP:**

```
1. API PNCP retornou: 1000 licitações ✅
2. Filtro aplicado: "Sem palavras-chave do setor" ❌
3. Resultado final: 0 licitações aprovadas
```

**Causa Raiz:**
O sistema está aplicando o filtro de keywords do **setor** mesmo quando o usuário escolhe buscar por **"Termos Específicos"**.

Em modo "Termos Específicos", o sistema deveria:
- ✅ Buscar pelo termo digitado pelo usuário ("notebook")
- ❌ **NÃO** aplicar filtro de keywords do setor

**Comportamento Atual (ERRADO):**
- Busca pelo termo "notebook" na API ✅
- Aplica filtro de keywords do setor (ex: "uniforme", "jaleco") ❌
- Como "notebook" não está nas keywords do setor, rejeita TUDO

### Evidências

| Screenshot | Descrição |
|------------|-----------|
| `gtm-inspection-13-termos-especificos-bug.png` | Smart PNCP mostrando 0 resultados |
| `gtm-inspection-14-pncp-oficial-336-results.png` | PNCP oficial mostrando 336 resultados |

### Impacto

**CRÍTICO** - Este bug é o mais grave de todos porque:

1. **Destrói a confiança do usuário** - Ao comparar com PNCP oficial, verão discrepância ENORME (0 vs 336)
2. **Afeta funcionalidade CORE** - Busca por termos específicos é feature principal
3. **Afeta TODOS os planos** - FREE, Consultor, Máquina e Sala de Guerra
4. **Mensagem confusa** - Sistema sugere "Considere mudar de setor econômico" quando o problema é técnico

### Correção Recomendada

No arquivo `backend/filter.py`, função `aplicar_todos_filtros()`:

```python
# ANTES: sempre aplica filtro de keywords do setor
if not match_keywords(licitacao, setor_keywords):
    return False, "Sem palavras-chave do setor"

# DEPOIS: pular filtro de setor se busca for por termos específicos
if modo_busca != "termos_especificos":
    if not match_keywords(licitacao, setor_keywords):
        return False, "Sem palavras-chave do setor"
```

---

## Conclusão

O Smart PNCP está **bloqueado para GTM** devido ao bug crítico na busca por "Termos Específicos". Este bug deve ser corrigido **ANTES** de qualquer lançamento, pois afeta a funcionalidade principal do sistema.

**Status:** ⚠️ **NÃO APROVADO** até correção do P0 #1

**Trabalho estimado para P0s:**
- P0 #1 (Termos Específicos): 2-4h
- P0 #2 (Master ilimitado): 1h
- P0 #3 (JS Error): 2h
- **Total: 5-7 horas de trabalho**

**Recomendação:** Corrigir P0 #1 IMEDIATAMENTE, testar, validar comparação com PNCP oficial, depois corrigir P0 #2 e #3.

---

*Relatório gerado por AIOS Master Orchestrator*
*Agentes consultados: @dev, @qa, @architect, @ux-design-expert, @devops*
