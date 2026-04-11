# STORY-432: Calculadora de Oportunidades Embeddável — Link Bait com Backlink Automático

**Priority:** P1 — Link Bait Secundário (meta: 30 embeds = 30 backlinks dofollow)
**Effort:** M (2-3 dias)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 2 (paralelo com STORY-431)

---

## Contexto

A calculadora em `/calculadora` já existe no SmartLic. O problema: ela é fechada (não embeddável) e não gera backlinks quando alguém a compartilha.

**Estratégia do link bait embeddável:** Criar uma versão pública da calculadora que qualquer blog de consultoria, associação ou portal de licitações possa **incorporar no próprio site via iframe** — e que automaticamente inclua um link `href="https://smartlic.tech/calculadora"` no rodapé do embed. Cada site que incorporar = 1 backlink dofollow permanente.

**Por que funciona:**
- Consultores de licitação têm blogs e sites com tráfego mas sem ferramentas
- Associações setoriais (FENACON, CNI, SEBRAE) linkam para ferramentas úteis para seus membros
- Uma calculadora que mostra "Sua empresa está perdendo R$ X em oportunidades" é viral por natureza — cada usuario quer compartilhar o resultado

**A calculadora atual** (`/calculadora`) responde: "Dado seu setor + UF + número de análises mensais que você faz, quantas licitações relevantes você provavelmente está perdendo e qual o valor estimado dessas oportunidades?"

**Dados do datalake para alimentar a calculadora:**
- Total de licitações ativas por (setor, UF) — já disponível em `pncp_raw_bids`
- Valor médio estimado por setor — já calculável com AVG(valor_estimado)
- Taxa de conversão de mercado para o setor (benchmark público)

---

## Acceptance Criteria

### AC1: Calculadora pública sem autenticação
- [ ] `GET /calculadora` funciona para usuários não autenticados (zero friction — sem login)
- [ ] Campos de entrada: (1) Setor (dropdown dos 20 setores do SmartLic), (2) UF (dropdown dos 27 estados), (3) "Quantas licitações você analisa por mês?" (slider 1-50)
- [ ] Saída calculada:
  - **"Total de licitações relevantes disponíveis no seu setor/UF este mês"** — dado real do datalake
  - **"Você analisa X%% do mercado disponível"** — (input_usuario / total_datalake) × 100
  - **"Valor estimado das oportunidades não analisadas"** — (total - analisadas) × valor_medio_setor
  - **"Potencial de receita incremental (assumindo taxa de vitória de mercado de 15%)"** — oportunidades_perdidas × valor_medio × 0.15

### AC2: Rota embed isolada
- [ ] Criar `frontend/app/calculadora/embed/page.tsx` — versão stripped da calculadora (sem header, footer, nav)
- [ ] Layout minimalista: logo SmartLic pequeno no canto + calculadora + rodapé fixo com:
  ```
  Calculadora por SmartLic — Inteligência em Licitações
  [Ver relatório completo] (link para smartlic.tech/calculadora)
  ```
- [ ] O link no rodapé é `rel="noopener"` mas **sem** `rel="nofollow"` — backlink seguível
- [ ] Dimensões responsivas: funciona em 600×400 mínimo

### AC3: Gerador de código embed na página principal
- [ ] Na página `/calculadora`, adicionar seção "Incorpore esta calculadora no seu site":
  - Preview visual do embed
  - Code snippet copiável:
    ```html
    <iframe src="https://smartlic.tech/calculadora/embed" 
            width="700" height="500" frameborder="0" 
            style="border:1px solid #e2e8f0; border-radius:8px;">
    </iframe>
    <p style="font-size:12px; color:#666;">
      Calculadora de Oportunidades por 
      <a href="https://smartlic.tech">SmartLic</a>
    </p>
    ```
  - Botão "Copiar código" com feedback visual (✓ Copiado!)
- [ ] O snippet inclui explicitamente o link `<a href="https://smartlic.tech">SmartLic</a>` — qualquer site que colar o snippet gera backlink

### AC4: Endpoint público de dados da calculadora
- [ ] Criar `GET /api/public/calculadora?setor={setor}&uf={uf}` no backend
- [ ] Retorna: `{ total_ativas: int, valor_medio: float, percentil_50: float, fonte: "PNCP via SmartLic datalake", atualizado_em: datetime }`
- [ ] Rate limit: 60 req/min por IP (sem token) — suficiente para embed em múltiplos sites simultaneamente
- [ ] Cache Redis 1h por (setor, uf)
- [ ] CORS: `Access-Control-Allow-Origin: *` (público)

### AC5: Resultado compartilhável
- [ ] Botão "Compartilhar resultado" gera URL com query params: `/calculadora?setor=informatica&uf=SP&analisa=5`
- [ ] URL com params pré-preenche a calculadora e exibe o resultado automaticamente
- [ ] Meta tags Open Graph dinâmicas baseadas nos params: `og:title = "Sua empresa pode estar perdendo R$ X em licitações de TI em SP"`
- [ ] Share button abre WhatsApp Web + LinkedIn com texto pré-formatado + URL

### AC6: CTA de conversão (não-intrusivo)
- [ ] Após calcular, exibir: "Quer ver quais são essas licitações agora? [Trial grátis por 14 dias]"
- [ ] CTA não bloqueia o resultado — aparece abaixo, não em modal
- [ ] Na versão embed: CTA simplificado: "Ver licitações completas → [smartlic.tech]"

### AC7: SEO da página /calculadora
- [ ] title: `"Calculadora de Oportunidades em Licitações Públicas | SmartLic"` (52 chars ✓)
- [ ] description: `"Descubra quantas licitações do seu setor você está perdendo. Calcule o valor das oportunidades não analisadas. Dados reais do PNCP, atualizado diariamente."` (155 chars ✓)
- [ ] `robots: { index: true }` — esta página deve ser indexada
- [ ] Schema.org `SoftwareApplication` com `offers.price = "0"` (ferramenta gratuita)
- [ ] H1 visível: "Calculadora de Oportunidades em Licitações"

### AC8: Testes
- [ ] `npm test` passa sem regressões
- [ ] Teste: cálculo correto quando total_ativas = 0 (edge case — setor raro em UF pequena)
- [ ] Teste: cálculo correto quando analisa > total_ativas (mostra "Você analisa mais que o disponível")
- [ ] Teste: endpoint `/api/public/calculadora` retorna 200 sem autenticação

---

## Scope

**IN:**
- `frontend/app/calculadora/page.tsx` — adicionar seção embed + AC5 share
- `frontend/app/calculadora/embed/page.tsx` (novo)
- `backend/routes/public.py` ou novo arquivo para endpoint público (sem auth)
- Lógica de cálculo no frontend

**OUT:**
- Alterar calculadora existente (only additive — embed é nova rota)
- Histórico de cálculos do usuário (requer autenticação)
- Email capture no resultado (fora de escopo)
- Automação de distribuição do embed

---

## Dependências

- Datalake `pncp_raw_bids` com dados por (setor, UF) — confirmado operacional
- Endpoint `/api/public/calculadora` não requer autenticação (novo — verificar que não conflita com middleware de auth)

---

## Riscos

- **Valores inflados assustam:** Se valor_medio_setor for muito alto (ex: engenharia = R$10M), o "potencial perdido" em valores absolutos pode parecer irreal. Mitigação: usar P50 (mediana) ao invés de média, comunicar claramente "valor mediano de contratos".
- **Embed em sites com CSP restritivo:** Algumas prefeituras e portais gov têm CSP que bloqueia iframes externos. Fora do controle — documentar que o site que embute deve ter CSP permissivo para iframes de smartlic.tech.

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `frontend/app/calculadora/page.tsx`
- `frontend/app/calculadora/embed/page.tsx` (novo)
- `backend/routes/public.py` (novo ou existente)
- `frontend/__tests__/calculadora.test.tsx` (novos testes)

---

## Definition of Done

- [ ] `/calculadora` acessível sem login, calculando com dados reais do datalake
- [ ] `/calculadora/embed` funcional em iframe externo (testar em sandbox HTML)
- [ ] Code snippet com backlink copiável na página principal
- [ ] `npx tsc --noEmit` + `npm test` passando
- [ ] Share URL gera preview correto no WhatsApp/LinkedIn (testar via og debugger)
- [ ] Rate limit verificado: 60+ req sem throttle, 61ª recebe 429

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — calculadora embeddável é o link bait com maior ROI documentado para SaaS B2B: cada embed = 1 backlink permanente sem esforço adicional |
