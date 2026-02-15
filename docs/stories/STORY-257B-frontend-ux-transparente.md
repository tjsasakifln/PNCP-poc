# STORY-257B: Frontend — UX Transparente e Resiliente

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-257B |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | Sprint 2 |
| **Estimate** | 5h |
| **Depends on** | STORY-257A (backend resilience) |
| **Blocks** | GTM launch readiness |
| **Paired with** | STORY-257A (backend) |

## Filosofia

> **"Nunca deixar o usuário sem informação ou sem esperança."**

O usuário de licitação é B2B, profissional, lida com prazos. Ele prefere **transparência brutal** a otimismo falso. Ele precisa saber o que está acontecendo, o que já foi encontrado, e o que pode fazer enquanto espera.

**Regra de linguagem:** NUNCA exibir nomes técnicos de fontes (PNCP, ComprasGov, Portal, etc). Sempre usar **"nossas fontes"**, **"fontes de dados governamentais"**, ou **"bases de dados públicas"**. Termos técnicos ficam APENAS em logs e console — nunca na tela.

## Problema

### O que o usuário vê hoje quando fontes falham:

| Cenário | Experiência atual | Sentimento |
|---------|-------------------|------------|
| Todas as fontes caem | "Nenhuma fonte de dados respondeu" após 16s | Frustração, desconfiança |
| PNCP degraded (circuit breaker) | Zero resultados sem explicação | "O sistema não funciona?" |
| UFs parciais falham | Recebe resultados incompletos sem saber | Falsa confiança nos dados |
| Busca lenta (>10s) | Barra de progresso genérica | "Travou?" |
| Rate limit 429 | Espera 60s com spinner | "Quebrou" |

### O que o usuário DEVERIA ver:

| Cenário | Experiência ideal | Sentimento |
|---------|-------------------|------------|
| Fontes lentas | Grid por UF mostrando progresso individual | "Está trabalhando por mim" |
| Resultados parciais | "67 oportunidades em 4 estados. Ainda tentando RJ e BA..." | Confiança + expectativa |
| Todas as fontes caem + cache | "Fontes temporariamente lentas. Mostrando resultados de 2h atrás." | Serviço premium |
| Todas caem sem cache | "Nossas fontes estão temporariamente indisponíveis. Tente em alguns minutos." | Honestidade respeitosa |
| Busca muito lenta | "Está demorando mais que o normal. Fique tranquilo — quando terminar, seus resultados estarão salvos." | Calma, confiança |

---

## Solução: 4 Tracks

### Track 1: Grid de Progresso por UF (2h)

**Problema:** Barra de progresso genérica não comunica o que está acontecendo. Usuário não sabe se 15 UFs já retornaram dados enquanto 2 estão lentas.

- [ ] **AC1: Componente `UfProgressGrid`**
  - Novo componente que exibe grid responsivo de cards por UF selecionada
  - Cada card mostra: sigla da UF + status visual
  - Status possíveis com ícones/cores:
    - `pending` → cinza, ícone relógio — "Aguardando..."
    - `fetching` → azul, spinner — "Consultando..."
    - `retrying` → amarelo, spinner — "Tentando novamente..."
    - `success` → verde, checkmark — "X oportunidades"
    - `failed` → vermelho sutil, X — "Indisponível"
    - `recovered` → verde, checkmark + badge — "X oportunidades (recuperado)"
  - Grid: 3 colunas mobile, 6 colunas desktop, 9 colunas wide
  - **Critério:** Renderiza corretamente de 1 a 27 UFs com status dinâmico

- [ ] **AC2: Consumir eventos SSE `uf_status`**
  - `useSearch.ts`: parsear novo tipo de evento `uf_status` do SSE
  - Manter state `Map<string, UfStatus>` com último status de cada UF
  - Atualizar `UfProgressGrid` em tempo real conforme eventos chegam
  - Fallback: se SSE não disponível, usar simulação baseada em tempo (padrão atual)
  - **Critério:** Grid atualiza em <200ms após receber evento SSE

- [ ] **AC3: Contagem progressiva de resultados**
  - Exibir contador total acima do grid: "Encontradas: **47** oportunidades até agora"
  - Incrementar conforme UFs completam (usar `count` do evento `uf_status`)
  - Animar a transição do número (não pular de 0 para 47)
  - **Critério:** Usuário vê valor chegando em tempo real, não só no final

- [ ] **AC4: Transição elegante grid → resultados**
  - Quando busca completa (todas as UFs finalizadas):
    - Grid faz fade-out suave (300ms)
    - Resultados fazem fade-in
    - Se houve `failed_ufs`: manter mini-banner informativo acima dos resultados
  - **Critério:** Transição sem layout shift (CLS = 0)

### Track 2: Resultados Parciais como Feature (1h)

**Problema:** O sistema espera TODAS as UFs finalizarem antes de mostrar resultados. Se 2 UFs estão lentas, o usuário espera por tudo.

- [ ] **AC5: Prompt de resultados parciais**
  - Após 15s de busca, se `succeeded_ufs.length > 0` e `pending_ufs.length > 0`:
    - Exibir prompt: "Encontramos **X oportunidades** em **Y estados**. Ainda consultando Z estados..."
    - Dois botões: **[Ver resultados parciais]** e **[Aguardar busca completa]**
  - Timer visível: "Consultando há 0:15..."
  - **Critério:** Prompt aparece após 15s se há resultados parciais

- [ ] **AC6: "Ver resultados parciais" exibe dados imediatos**
  - Ao clicar [Ver resultados parciais]:
    - Renderizar resultados já recebidos (da resposta parcial ou do state acumulado via SSE)
    - Manter mini-banner no topo: "Mostrando X de Y estados. Busca em andamento..."
    - Se mais resultados chegarem via SSE retry: atualizar lista e contador
  - **Critério:** Usuário vê dados em <1s após clicar, sem nova requisição

- [ ] **AC7: Banner de UFs faltantes no resultado final**
  - Quando response contém `failed_ufs` (de STORY-257A AC5):
    - Exibir banner informativo (azul/info, não vermelho/erro):
      > "Resultados de **X estados**. Alguns estados ficaram temporariamente indisponíveis. Você pode tentar novamente para consultar todos."
    - Botão: **[Consultar estados restantes]** → nova busca apenas com UFs que falharam
    - **NÃO listar os nomes dos estados que falharam** (pode parecer bug). Apenas dizer "alguns estados".
  - Se TODOS os estados falharam: mensagem diferente (ver Track 3)
  - **Critério:** Usuário informado sem alarme. Tom: informativo, não alarmista.

### Track 3: Cache e Fallback UX (1h)

**Problema:** Quando todas as fontes caem, o backend pode servir cache (STORY-257A). O frontend precisa comunicar isso de forma transparente e útil.

- [ ] **AC8: Banner de dados em cache**
  - Quando response contém `cached: true`:
    - Banner âmbar (warning, não error) no topo dos resultados:
      > "Nossas fontes estão temporariamente lentas. Mostrando resultados de **[tempo relativo]** atrás. Os dados podem estar levemente desatualizados."
    - `[tempo relativo]`: "há 30 minutos", "há 2 horas" (usar `Intl.RelativeTimeFormat` pt-BR)
    - Botão: **[Tentar atualizar]**
  - **Critério:** Banner visível mas não intrusivo. Dados são usáveis.

- [ ] **AC9: Botão "Tentar atualizar" envia `force_fresh`**
  - Ao clicar [Tentar atualizar]:
    - Nova busca com `force_fresh: true` no body do POST
    - Mostrar grid de progresso por UF (Track 1) durante a nova tentativa
    - Se nova busca também falhar: manter dados do cache, exibir toast "Fontes ainda indisponíveis. Mantendo resultados anteriores."
  - **Critério:** Não substituir dados bons por tela vazia em caso de falha no refresh

- [ ] **AC10: Fallback total — nenhum cache, nenhum resultado**
  - Quando response indica all-sources-failed E `cached: false`:
    - Tela específica (NÃO genérica de erro):
      > **"Nossas fontes de dados governamentais estão temporariamente indisponíveis"**
      > "Isso geralmente se resolve em alguns minutos. Seus resultados anteriores continuam acessíveis."
    - Botões:
      - **[Tentar novamente]** (com cooldown visual de 30s antes de habilitar)
      - **[Ver última busca salva]** (se existir em Supabase, via STORY-257A AC11)
    - Ilustração ou ícone amigável (não o ❌ vermelho padrão)
  - **Critério:** Tela transmite "problema temporário", não "sistema quebrado"

- [ ] **AC11: Carregar última busca salva**
  - Novo endpoint GET `/api/search-history/latest?setor_id=X`
  - Frontend: ao clicar [Ver última busca salva], carregar resultados do Supabase
  - Exibir com banner: "Resultados da sua busca de **[data]**."
  - Se não existir busca salva: desabilitar botão, tooltip "Nenhuma busca anterior encontrada"
  - **Critério:** Usuário SEMPRE tem uma saída — nunca dead-end

### Track 4: Retry UX e Polish (1h)

- [ ] **AC12: Retry automático expandido**
  - `useSearch.ts`: expandir retry para incluir 500 e 502 (além de 503)
  - Máximo 2 retries com delay progressivo: 3s, 8s
  - Durante retry, mostrar no grid: "Nossas fontes estão lentas. Tentativa 2 de 3..."
  - **Critério:** 500 e 502 são retentados automaticamente com feedback visual

- [ ] **AC13: Cooldown visual no "Tentar novamente"**
  - Após erro total, botão [Tentar novamente] tem cooldown de 30s
  - Exibir countdown no botão: "Tentar novamente (0:28)"
  - Botão desabilitado durante cooldown (prevenir spam de requests)
  - **Critério:** Usuário não bombardeia o backend com retries

- [ ] **AC14: Mensagens com acentos corretos (pt-BR)**
  - Auditar todos os textos em `DegradationBanner.tsx`, `SearchResults.tsx`, `useSearch.ts`
  - Substituir ASCII por português correto: "estao" → "estão", "indisponiveis" → "indisponíveis", etc.
  - Padrão: todas as strings user-facing em pt-BR com acentos
  - **Critério:** Zero strings ASCII-only visíveis ao usuário

- [ ] **AC15: Console e logs sem termos técnicos para o usuário**
  - Auditar todas as mensagens de toast, banner, alert, modal
  - Substituir: "PNCP" → remover ou "nossas fontes"
  - Substituir: "ComprasGov" → remover ou "fontes governamentais"
  - Substituir: "Circuit breaker" → nunca mostrar
  - Substituir: "HTTP 503" → "temporariamente indisponível"
  - **Critério:** `grep -r "PNCP\|ComprasGov\|circuit.breaker\|HTTP [45]" --include="*.tsx" --include="*.ts"` em componentes UI retorna zero matches (excluindo console.log/logger)

---

## Testes

### Frontend (8 testes)

- [ ] **T1:** `UfProgressGrid` renderiza corretamente com 1, 5, 27 UFs
- [ ] **T2:** Grid atualiza status ao receber evento SSE `uf_status`
- [ ] **T3:** Prompt de resultados parciais aparece após 15s com dados parciais
- [ ] **T4:** Banner de cache exibe tempo relativo correto ("há 2 horas")
- [ ] **T5:** Botão "Tentar atualizar" envia `force_fresh: true`
- [ ] **T6:** Tela de fallback total não exibe nomes técnicos de fontes
- [ ] **T7:** Retry automático em 500 e 502 (mock fetch, verificar delay)
- [ ] **T8:** Mensagens com acentos corretos (snapshot test em pt-BR)

---

## Arquivos a Modificar/Criar

| Arquivo | Track | Mudanças |
|---------|-------|---------|
| `frontend/app/buscar/components/UfProgressGrid.tsx` | T1 | **NOVO** — grid de status por UF |
| `frontend/app/buscar/hooks/useSearch.ts` | T1,T2,T4 | AC2,AC5,AC12: SSE uf_status, parciais, retry |
| `frontend/app/buscar/components/SearchResults.tsx` | T2,T3 | AC7,AC8,AC10: banners parciais/cache/fallback |
| `frontend/app/buscar/components/DegradationBanner.tsx` | T3,T4 | AC8,AC14: banner cache, acentos |
| `frontend/app/buscar/components/PartialResultsPrompt.tsx` | T2 | **NOVO** — prompt "ver parciais ou aguardar" |
| `frontend/app/buscar/components/SourcesUnavailable.tsx` | T3 | **NOVO** — tela de fallback total |
| `frontend/app/buscar/page.tsx` | T1,T2 | Integrar UfProgressGrid e PartialResultsPrompt |
| `frontend/app/api/search-history/route.ts` | T3 | **NOVO** — proxy para busca salva |

---

## Design Specs (Referência para implementação)

### UfProgressGrid — Layout

```
┌─────────────────────────────────────────────────────────┐
│  Encontradas: 67 oportunidades até agora                │
├────────┬────────┬────────┬────────┬────────┬────────────┤
│ SP ✅  │ RJ ⏳  │ MG ✅  │ BA ❌  │ PR ✅  │ RS ✅     │
│ 47     │ tent.2 │ 12     │ indisp │ 8      │ 3         │
├────────┼────────┼────────┼────────┼────────┼────────────┤
│ SC ✅  │ CE ⏳  │ PE ✅  │ GO ⏳  │ ...    │ ...       │
│ 5      │ tent.1 │ 2      │ aguard │        │           │
└────────┴────────┴────────┴────────┴────────┴────────────┘
```

### Cores (Tailwind)

| Status | Bg | Text | Border |
|--------|-----|------|--------|
| pending | gray-50 | gray-400 | gray-200 |
| fetching | blue-50 | blue-600 | blue-200 |
| retrying | amber-50 | amber-600 | amber-200 |
| success | emerald-50 | emerald-700 | emerald-200 |
| failed | red-50 | red-400 | red-200 |
| recovered | emerald-50 | emerald-700 | emerald-300 (thicker) |

### Banner de cache

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Nossas fontes estão temporariamente lentas.          │
│    Mostrando resultados de há 2 horas.                  │
│    Os dados podem estar levemente desatualizados.       │
│                                    [Tentar atualizar]   │
└─────────────────────────────────────────────────────────┘
  Background: amber-50  Border: amber-200  Text: amber-800
```

### Tela de fallback total

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│         🔄  (ícone amigável, NÃO ❌)                    │
│                                                         │
│   Nossas fontes de dados governamentais estão           │
│   temporariamente indisponíveis                         │
│                                                         │
│   Isso geralmente se resolve em poucos minutos.         │
│                                                         │
│   [Tentar novamente (0:28)]  [Ver última busca salva]   │
│                                                         │
└─────────────────────────────────────────────────────────┘
  Background: white  Text: gray-600  Buttons: primary + ghost
```

---

## Riscos e Mitigações

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| SSE `uf_status` não chega (rede instável) | Média | Grid não atualiza | Fallback: simulação baseada em tempo (padrão atual) |
| Prompt de parciais interrompe fluxo do usuário | Baixa | UX intrusiva | Só aparece após 15s; não é modal, é inline |
| Cache exibe licitação já encerrada | Baixa | Usuário tenta participar | Banner claro com horário; botão atualizar proeminente |
| Grid com 27 UFs fica poluído em mobile | Média | UX mobile ruim | 3 colunas mobile; scroll horizontal se necessário |

## Definition of Done

- [ ] Todos os ACs checked
- [ ] `npm test` sem regressões (baseline: 70 pre-existing)
- [ ] `npx tsc --noEmit` clean
- [ ] Grid de progresso por UF funcional com SSE
- [ ] Resultados parciais acessíveis após 15s
- [ ] Cache banner com tempo relativo correto
- [ ] Tela de fallback total sem dead-ends
- [ ] Zero nomes técnicos de fontes visíveis ao usuário
- [ ] Todas as mensagens em pt-BR com acentos corretos
- [ ] Transições suaves, sem layout shift
