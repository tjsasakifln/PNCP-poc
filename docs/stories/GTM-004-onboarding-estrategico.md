# GTM-004: Onboarding Estratégico + Primeiro Resultado Imediato

## Metadata
| Field | Value |
|-------|-------|
| **ID** | GTM-004 |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | Sprint 1 |
| **Estimate** | 10h |
| **Depends on** | GTM-003 (trial redesign — trial completo deve estar configurado) |
| **Blocks** | GTM-010 (conversão trial→paid — onboarding afeta activation) |
| **Enhances** | STORY-247 (perfil/context collection existente) |

## Filosofia

> **"Time-to-first-value < 5 minutos. Não deixe o usuário explorar sozinho — entregue valor imediato."**

> **"Onboarding não é coleta de dados. É configuração do sistema para trabalhar PARA o usuário."**

O onboarding atual (STORY-247) coleta dados básicos (porte, UFs, experiência com licitações) mas não conecta imediatamente ao valor. Após completar, o sistema redireciona para `/buscar` onde o usuário precisa:
1. Selecionar setor manualmente
2. Escolher UFs
3. Configurar datas
4. Clicar "Buscar"
5. Esperar resultados

**Problema:** Fricção de 4 passos antes do primeiro valor. Usuário pode desistir ou não saber o que fazer.

**Solução:** Após onboarding, executar primeira busca AUTOMATICAMENTE baseada no perfil e entregar oportunidades priorizadas em <15s.

## Problema

### Fluxo Atual (STORY-247 implementado)

```
Signup → Email confirmation → Onboarding (3 steps) → Redirect to /buscar → User explores manually
```

**Onboarding coleta:**
- Porte da empresa (MEI, Pequena, Média, Grande)
- UFs de atuação
- Experiência com licitações (Iniciante, Intermediário, Avançado)

**Após completar:**
- Usuário vê página `/buscar` vazia
- Precisa configurar setor, UFs, datas manualmente
- Clica "Buscar"
- Aguarda 10-15s
- Vê resultados (se tudo funcionar)

**Fricção identificada:**
- Onboarding coleta "UFs de atuação" mas não usa imediatamente
- Usuário não sabe qual setor escolher (dropdown com 9+ opções)
- "Datas" são abstração técnica (usuário não pensa em ranges de data)
- Nenhum resultado tangível em 5 minutos de uso

**Evidência de problema:**
- Activation rate (usuários que completam primeira busca) estimada em ~40% (baseado em similar SaaS)
- Time-to-first-value: 8-12 minutos (signup → onboarding → configurar busca → esperar)

## Solução: Onboarding Estratégico com Primeira Análise Automática

### Novo Fluxo

```
Signup → Email confirmation → Onboarding Estratégico (3 steps) → Primeira Análise Automática → Resultados Priorizados
                                                                       ↓ (happens in background)
                                                                   Redirect to /buscar?auto=true
```

**Mudanças no onboarding:**

| Step | Atual (STORY-247) | Novo (GTM-004) |
|------|------------------|----------------|
| **1** | Porte + UFs + experiência | **CNAE/Segmento** + Objetivo principal |
| **2** | (wizard completo) | **UFs de atuação** + Faixa de valor desejada |
| **3** | (wizard completo) | **Confirmação** + "Ver minhas oportunidades" CTA |

**Após Step 3:**
1. Sistema salva perfil em `profiles.context_data` (já funcional via STORY-247)
2. Backend executa busca automática com params derivados do perfil:
   - `setor_id`: mapeado do CNAE informado
   - `ufs`: UFs selecionadas no Step 2
   - `valor_min/max`: faixa informada no Step 2
   - `data_inicial/final`: últimos 30 dias (padrão inteligente)
   - `modo_busca`: "normal" (não "abrangente")
3. Frontend redireciona para `/buscar?auto=true&search_id=xxx`
4. Página de busca mostra progresso SSE (já implementado em STORY-257B)
5. Resultados chegam em 10-15s, já priorizados

**Resultado:** Usuário vê oportunidades relevantes ao perfil em <5min de signup.

## Escopo — Backend

### Endpoint: `POST /api/first-analysis` (NOVO)

**Arquivo:** `backend/routes/user.py` (ou novo `backend/routes/onboarding.py`)

**Input Schema:**
```python
class FirstAnalysisRequest(BaseModel):
    cnae: str  # Código CNAE ou segmento (ex: "4781-4/00 — Comércio varejista de uniformes")
    objetivo_principal: str  # Ex: "Encontrar licitações de uniformes escolares acima de R$ 100k"
    ufs: list[str]  # Ex: ["SP", "RJ", "MG"]
    faixa_valor_min: int  # Em centavos, ex: 10000000 = R$ 100k
    faixa_valor_max: int  # Ex: 50000000 = R$ 500k
```

**Lógica:**
1. Validar `cnae` → mapear para `setor_id` (uniforms, facilities, etc.)
   - Mapeamento: CNAE 4781 → "uniforms"
   - CNAE 8121 → "facilities"
   - (criar tabela de mapeamento CNAE→setor)
2. Construir `BuscaRequest` automaticamente:
   ```python
   busca_request = BuscaRequest(
       setor_id=map_cnae_to_setor(cnae),
       ufs=ufs,
       valor_min=faixa_valor_min,
       valor_max=faixa_valor_max,
       data_inicial=(date.today() - timedelta(days=30)).isoformat(),
       data_final=date.today().isoformat(),
       modalidades=["todos"],  # Padrão
       modo_busca="normal",
       status_licitacao=["aberta", "em_andamento"]
   )
   ```
3. Chamar `buscar_licitacoes()` internamente (reutilizar pipeline existente)
4. Retornar `search_id` para frontend rastrear via SSE

**Response Schema:**
```python
class FirstAnalysisResponse(BaseModel):
    search_id: str  # UUID para rastrear progresso
    status: str  # "in_progress"
    message: str  # "Analisando oportunidades em SP, RJ, MG..."
```

**Tratamento de erro:**
- Se não houver resultados para o perfil exato: sugerir filtros mais amplos
  - Ex: "Nenhuma oportunidade encontrada para uniformes em SP nos últimos 30 dias. Sugestão: expandir para últimos 90 dias ou adicionar MG, RJ."
- Se busca falhar (todas fontes caem): retornar erro amigável + sugestão de tentar novamente

**Linhas afetadas:** ~150 linhas (novo endpoint + lógica de mapeamento CNAE→setor)

### Schema: `PerfilContexto` (atualizar)

**Arquivo:** `backend/schemas.py`

**Antes (STORY-247):**
```python
class PerfilContexto(BaseModel):
    porte: str | None
    ufs_atuacao: list[str] | None
    experiencia: str | None
```

**Depois (GTM-004):**
```python
class PerfilContexto(BaseModel):
    # Campos existentes (manter para backward compatibility)
    porte: str | None = None
    ufs_atuacao: list[str] | None = None
    experiencia: str | None = None

    # Novos campos estratégicos
    cnae: str | None = None
    objetivo_principal: str | None = None
    ticket_medio_desejado: int | None = None  # Faixa valor, em centavos
```

**Linhas afetadas:** ~10 linhas

### Função: Mapeamento CNAE → Setor (NOVA)

**Arquivo:** `backend/utils/cnae_mapping.py` (novo)

**Lógica:**
```python
CNAE_TO_SETOR: dict[str, str] = {
    "4781": "uniforms",  # Comércio varejista de artigos de vestuário
    "1412": "uniforms",  # Confecção de roupas profissionais
    "8121": "facilities",  # Limpeza em prédios e domicílios
    "8011": "facilities",  # Atividades de vigilância e segurança
    # ... expandir conforme necessário
}

def map_cnae_to_setor(cnae: str) -> str:
    """
    Mapeia código CNAE para setor do SmartLic.
    Se CNAE não mapeado, retorna "uniforms" como fallback (setor mais comum).
    """
    cnae_prefix = cnae.split("-")[0]  # Ex: "4781-4/00" → "4781"
    return CNAE_TO_SETOR.get(cnae_prefix, "uniforms")
```

**Linhas afetadas:** ~50 linhas (mapeamento inicial + testes)

## Escopo — Frontend

### Arquivo: `frontend/app/onboarding/page.tsx`

**Mudança:** Reescrever wizard com novos steps

**Step 1: CNAE/Segmento + Objetivo**

```tsx
<WizardStep number={1} title="Qual é o seu negócio?">
  <CNAEInput
    label="Segmento / CNAE"
    placeholder="Ex: Comércio de uniformes, Limpeza e facilities..."
    value={cnae}
    onChange={setCnae}
    suggestions={cnaeSuggestions}  // Autocomplete com CNAEs comuns
  />

  <TextArea
    label="Qual é seu objetivo principal?"
    placeholder="Ex: Encontrar licitações de uniformes escolares acima de R$ 100.000 em São Paulo"
    value={objetivo}
    onChange={setObjetivo}
    maxLength={200}
  />

  <Button onClick={nextStep}>Continuar</Button>
</WizardStep>
```

**Step 2: UFs + Faixa Valor**

```tsx
<WizardStep number={2} title="Onde você atua e qual valor busca?">
  <UFMultiSelect
    label="Estados onde você atua"
    selected={ufs}
    onChange={setUfs}
  />

  <ValueRangeSlider
    label="Faixa de valor ideal"
    min={50000}     // R$ 50k
    max={5000000}   // R$ 5M
    value={[valorMin, valorMax]}
    onChange={setValorRange}
    formatLabel={(v) => `R$ ${(v / 100).toLocaleString('pt-BR')}`}
  />

  <Button onClick={nextStep}>Continuar</Button>
</WizardStep>
```

**Step 3: Confirmação + Primeira Análise**

```tsx
<WizardStep number={3} title="Pronto para começar">
  <ProfileSummary>
    <p>Segmento: {cnae}</p>
    <p>Atuação: {ufs.join(", ")}</p>
    <p>Faixa de valor: R$ {valorMin.toLocaleString()} - R$ {valorMax.toLocaleString()}</p>
  </ProfileSummary>

  <Message>
    Vamos encontrar suas primeiras oportunidades agora. Isso leva ~15 segundos.
  </Message>

  <Button onClick={submitAndAnalyze} loading={isAnalyzing}>
    Ver Minhas Oportunidades
  </Button>
</WizardStep>
```

**Após Step 3:**
```typescript
const submitAndAnalyze = async () => {
  setIsAnalyzing(true);

  // 1. Salvar perfil
  await fetch('/api/user/profile/context', {
    method: 'POST',
    body: JSON.stringify({ cnae, objetivo_principal, ufs, ticket_medio_desejado: valorMax })
  });

  // 2. Iniciar primeira análise
  const response = await fetch('/api/first-analysis', {
    method: 'POST',
    body: JSON.stringify({
      cnae,
      objetivo_principal: objetivo,
      ufs,
      faixa_valor_min: valorMin * 100,  // Converter para centavos
      faixa_valor_max: valorMax * 100
    })
  });

  const { search_id } = await response.json();

  // 3. Redirecionar para busca com auto=true
  router.push(`/buscar?auto=true&search_id=${search_id}`);
};
```

**Linhas afetadas:** ~300 linhas (wizard completo + submission logic)

### Arquivo: `frontend/app/buscar/page.tsx`

**Mudança:** Detectar param `?auto=true` e exibir mensagem de onboarding

**Lógica:**
```typescript
const searchParams = useSearchParams();
const isAutoSearch = searchParams.get('auto') === 'true';

useEffect(() => {
  if (isAutoSearch) {
    setMessage("Buscando oportunidades baseadas no seu perfil...");
    // SSE já está conectado e vai receber progresso
  }
}, [isAutoSearch]);
```

**UI quando `auto=true`:**
```tsx
{isAutoSearch && (
  <OnboardingBanner>
    <Icon name="sparkles" />
    <p>Analisando oportunidades com base no seu perfil. Aguarde ~15 segundos.</p>
  </OnboardingBanner>
)}
```

**Após resultados chegarem:**
```tsx
{isAutoSearch && results.length > 0 && (
  <SuccessMessage>
    <Icon name="check-circle" />
    <p>Encontramos {results.length} oportunidades para você! Explore abaixo.</p>
    <Button onClick={() => setIsAutoSearch(false)}>Entendi</Button>
  </SuccessMessage>
)}
```

**Se nenhum resultado:**
```tsx
{isAutoSearch && results.length === 0 && (
  <EmptyStateOnboarding>
    <p>Não encontramos oportunidades exatas para seu perfil nos últimos 30 dias.</p>
    <p>Sugestão: Expandir para últimos 90 dias ou adicionar mais UFs.</p>
    <Button onClick={adjustFilters}>Ajustar Filtros</Button>
  </EmptyStateOnboarding>
)}
```

**Linhas afetadas:** ~80 linhas (detecção auto + banners)

## Acceptance Criteria

### Backend

- [x] **AC1: Endpoint `/api/first-analysis` aceita CNAE e deriva setor automaticamente**
  - Input: `cnae="4781-4/00"` → Output: `setor_id="uniforms"`
  - Input: `cnae="8121-4/00"` → Output: `setor_id="facilities"`
  - **Critério de validação:** `POST /api/first-analysis` com CNAE válido retorna `search_id`

- [x] **AC2: Endpoint deriva params de busca do perfil**
  - `ufs`: direto do input
  - `valor_min/max`: direto do input (convertido para centavos)
  - `data_inicial/final`: últimos 30 dias automaticamente
  - `modalidades`: ["todos"] padrão
  - **Critério de validação:** Endpoint não requer usuário configurar datas/modalidades manualmente

- [x] **AC3: Primeira busca executa em background e retorna `search_id`**
  - Response: `{"search_id": "uuid", "status": "in_progress"}`
  - Frontend pode rastrear via `/buscar-progress/{search_id}` SSE (já implementado)
  - **Critério de validação:** Chamar endpoint → receber search_id → SSE conecta e recebe eventos

- [ ] **AC4: Se não houver resultados, backend sugere ajustes**
  - Cenário: CNAE válido mas nenhum resultado nos últimos 30 dias
  - Response: `{"results": [], "suggestion": "Expandir para últimos 90 dias ou adicionar mais UFs"}`
  - **Critério de validação:** Busca sem resultados retorna campo `suggestion` não-vazio

- [x] **AC5: Schema `PerfilContexto` aceita novos campos**
  - `cnae`, `objetivo_principal`, `ticket_medio_desejado` são opcionais
  - Backward compatible com onboarding antigo (porte, ufs_atuacao, experiencia)
  - **Critério de validação:** `POST /api/user/profile/context` aceita payload com novos campos

- [x] **AC6: Mapeamento CNAE→setor coberto para top 10 CNAEs**
  - Uniformes: 4781, 1412
  - Facilities: 8121, 8011
  - Equipamentos: 2710, 3250
  - Alimentos: 1011, 1091
  - TI: 6201, 6202
  - **Critério de validação:** `map_cnae_to_setor()` retorna setor correto para top 10 CNAEs

### Frontend — Wizard

- [x] **AC7: Wizard coleta CNAE/segmento como campo principal**
  - Step 1 tem input de CNAE com autocomplete de CNAEs comuns
  - Aceita texto livre (ex: "Limpeza e facilities") ou CNAE estruturado (ex: "8121-4/00")
  - **Critério de validação:** Input CNAE renderiza, autocomplete funciona, aceita ambos formatos

- [x] **AC8: Wizard coleta objetivo em texto livre**
  - Step 1 tem textarea "Qual é seu objetivo principal?"
  - Placeholder: "Ex: Encontrar licitações de uniformes acima de R$ 100k em SP"
  - Max 200 caracteres
  - **Critério de validação:** Textarea renderiza, limita a 200 chars, salva valor

- [x] **AC9: Wizard coleta UFs e faixa de valor no Step 2**
  - UF multi-select (reutilizar componente existente)
  - Slider de faixa de valor (R$ 50k - R$ 5M, default R$ 100k - R$ 500k)
  - **Critério de validação:** Ambos inputs funcionam, valores salvos corretamente

- [x] **AC10: Step 3 mostra confirmação e dispara busca automática**
  - Resumo do perfil (CNAE, UFs, faixa valor)
  - Botão "Ver Minhas Oportunidades" (não "Concluir" ou "Salvar")
  - Ao clicar: salva perfil + chama `/api/first-analysis` + redireciona para `/buscar?auto=true`
  - **Critério de validação:** Clicar botão → requisições de perfil e first-analysis disparadas → redirect acontece

### Frontend — Busca Auto

- [x] **AC11: `/buscar?auto=true` mostra banner de onboarding**
  - Banner: "Analisando oportunidades com base no seu perfil..."
  - SSE conecta automaticamente e mostra progresso
  - **Critério de validação:** URL com `?auto=true` → banner renderiza, SSE conecta

- [x] **AC12: Resultados aparecem em <15s com UX de sucesso**
  - Quando resultados chegam: banner de sucesso "Encontramos X oportunidades para você!"
  - Botão "Entendi" para dismissar banner
  - **Critério de validação:** Resultados chegam → banner de sucesso aparece com count correto

- [x] **AC13: Se sem resultados, mostra sugestão de ajuste**
  - Empty state: "Não encontramos oportunidades exatas para seu perfil..."
  - Sugestão: "Expandir para últimos 90 dias ou adicionar mais UFs"
  - Botão "Ajustar Filtros" que abre filtros manuais
  - **Critério de validação:** Busca auto sem resultados → empty state customizado com sugestão

### Copy

- [x] **AC14: Copy do wizard nunca menciona "busca"**
  - Banned: "busca", "buscar", "pesquisa"
  - Preferred: "análise", "oportunidades", "perfil estratégico", "encontrar"
  - **Critério de validação:** Grep de "busca", "buscar" em `onboarding/page.tsx` retorna zero (exceto query params)

- [x] **AC15: Copy de confirmação foca em resultado imediato**
  - "Vamos encontrar suas primeiras oportunidades agora" (não "Configure seu perfil")
  - "Isso leva ~15 segundos" (gerenciar expectativa de tempo)
  - **Critério de validação:** Step 3 contém copy que menciona tempo e resultado

### Quality

- [x] **AC16: Dados do onboarding salvos em `profiles.context_data`**
  - Após Step 3, `context_data` contém: `cnae`, `objetivo_principal`, `ufs_atuacao`, `ticket_medio_desejado`
  - Formato JSON no campo `context_data` (já funcional via STORY-247)
  - **Critério de validação:** Completar onboarding → query `SELECT context_data FROM profiles WHERE id=X` retorna JSON com novos campos

- [ ] **AC17: Mobile responsive (375px)**
  - Wizard completo funciona em viewport mobile
  - Slider de valor usável em touch
  - **Critério de validação:** Chrome DevTools mobile emulation 375px → wizard completo funcional

## Definition of Done

- [ ] Todos os 17 Acceptance Criteria passam (16/17 — AC4 e AC17 pendentes)
- [x] Backend: endpoint `/api/first-analysis` implementado e testado
- [x] Backend: mapeamento CNAE→setor coberto para top 10 CNAEs
- [x] Frontend: wizard redesenhado com 3 steps novos
- [x] Frontend: `/buscar?auto=true` detectado e exibe banners apropriados
- [ ] Teste end-to-end:
  - Signup novo usuário
  - Completar wizard com CNAE "4781" (uniformes)
  - Ver busca automática disparar
  - Resultados chegarem em <15s
  - Ver oportunidades priorizadas
- [x] Teste edge case: busca auto sem resultados → sugestão de ajuste aparece
- [ ] Monitoring: Track activation rate (usuários que completam onboarding → veem primeira análise)
- [ ] Merged to main, deployed to production

## File List

### Backend New
- `backend/routes/onboarding.py` (ou adicionar endpoint em `user.py`)
- `backend/utils/cnae_mapping.py`

### Backend Modified
- `backend/schemas.py` (PerfilContexto)

### Frontend Modified
- `frontend/app/onboarding/page.tsx` (~300 linhas de mudança)
- `frontend/app/buscar/page.tsx` (~80 linhas de mudança — detecção auto + banners)

### Frontend New (possivelmente)
- `frontend/app/components/onboarding/CNAEInput.tsx` (autocomplete CNAE)
- `frontend/app/components/onboarding/ValueRangeSlider.tsx` (slider de valor)
- `frontend/app/components/OnboardingBanner.tsx` (banner de auto-search)

## Notes

- Esta story **enhances** STORY-247 (não substitui) — mantém coleta de perfil, adiciona campos estratégicos
- Depende de GTM-003 completar primeiro (trial completo) para que primeira análise mostre valor real
- Bloqueia GTM-010 (conversão trial→paid) pois activation rate afeta trial→paid conversion
- **Estimativa de 10h:** 3h backend (endpoint + CNAE mapping) + 5h frontend (wizard redesign + auto-search UX) + 2h testing
- **Risco:** Se backend demorar >15s, UX degrada. Mitigação: usar SSE para mostrar progresso granular (já implementado)
- **Oportunidade:** Dados de onboarding (CNAE, objetivo) podem alimentar personalização futura (recomendações, email marketing)
