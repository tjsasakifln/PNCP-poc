# STORY-247: Onboarding Profundo — Perfil de Contextualização

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-247 |
| **Priority** | P2 |
| **Sprint** | Sprint 4 |
| **Estimate** | 8h |
| **Depends on** | STORY-243 (nomes corretos de setor), STORY-246 (one-click usa perfil) |
| **Blocks** | Nenhuma |

## Problema
Hoje coletamos apenas: nome, empresa, setor, email, telefone, senha. Não sabemos:
- Em quais UFs a empresa atua
- Faixa de valor dos contratos que persegue
- Se é microempresa (ME/EPP com preferência legal)
- Quais modalidades já participou
- Palavras-chave específicas do seu nicho

Sem isso, não podemos personalizar resultados nem fazer recomendações relevantes.

## Solução
Onboarding pós-signup com wizard de 3 passos que coleta contexto de negócio. Dados salvos no perfil Supabase e usados para personalizar busca (STORY-246) e curadoria LLM (STORY-245).

## Investigação Técnica

### Dados a Coletar

| Campo | Tipo | Obrigatório | Uso |
|-------|------|-------------|-----|
| `ufs_atuacao` | string[] | Sim | Default de UFs na busca |
| `faixa_valor_min` | float | Não | Default de valor_minimo |
| `faixa_valor_max` | float | Não | Default de valor_maximo |
| `porte_empresa` | enum(ME, EPP, MEDIO, GRANDE) | Sim | Filtro por porte (futuro), contexto LLM |
| `modalidades_interesse` | int[] | Não | Default de modalidades |
| `palavras_chave` | string[] | Não | Boost em relevância, contexto LLM |
| `experiencia_licitacoes` | enum(PRIMEIRA_VEZ, INICIANTE, EXPERIENTE) | Sim | Ajusta complexidade da UI e do resumo LLM |

### Wizard de 3 Passos

**Passo 1 — Sua Empresa:**
- Porte (ME/EPP/Médio/Grande) — radio buttons com ícones
- UFs de atuação — mapa clicável ou checkboxes por região
- Experiência com licitações — radio

**Passo 2 — Seu Interesse:**
- Setor principal (já coletado no signup, confirmar)
- Faixa de valor — slider duplo (R$ 0 – R$ 50M)
- Palavras-chave específicas — tag input

**Passo 3 — Personalização:**
- Resumo do que foi coletado
- "Com base no seu perfil, encontramos X oportunidades abertas agora"
- Botão "Ver minhas oportunidades" → redireciona para busca com filtros pré-preenchidos

### Arquivos a Criar/Modificar

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/onboarding/page.tsx` | Nova página com wizard 3 passos |
| `frontend/app/onboarding/components/` | StepOne, StepTwo, StepThree, ProgressBar |
| `backend/schemas.py` | Schema `PerfilContexto` com os novos campos |
| `backend/routes/profile.py` (ou equivalente) | Endpoint `PUT /v1/profile/context` |
| Supabase migration | Coluna `context_data` (jsonb) em `profiles` |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | Carregar defaults do perfil contextualizado |

### Fluxo de Ativação
1. Após primeiro login (email confirmado), redirecionar para `/onboarding`
2. Wizard é skippable ("Pular por agora" → usa defaults genéricos)
3. Wizard pode ser re-acessado via menu de perfil ("Atualizar meu perfil")
4. Dados persistem em `profiles.context_data` (JSONB, flexível)

## Acceptance Criteria

### Backend
- [ ] **AC1:** Schema `PerfilContexto` com todos os campos da tabela acima, validação Pydantic.
- [ ] **AC2:** Endpoint `PUT /v1/profile/context` — salva context_data no profiles. Requer auth.
- [ ] **AC3:** Endpoint `GET /v1/profile/context` — retorna context_data. Requer auth.
- [ ] **AC4:** Migration Supabase: `ALTER TABLE profiles ADD COLUMN context_data jsonb DEFAULT '{}'::jsonb`.
- [ ] **AC5:** Testes para endpoints de contexto (save e retrieve).

### Frontend — Wizard
- [ ] **AC6:** Wizard de 3 passos com progress bar.
- [ ] **AC7:** Passo 1: porte (radio), UFs de atuação (seletor por região), experiência (radio).
- [ ] **AC8:** Passo 2: setor (pré-preenchido), faixa de valor (slider), palavras-chave (tag input).
- [ ] **AC9:** Passo 3: resumo + contagem de oportunidades + CTA "Ver minhas oportunidades".
- [ ] **AC10:** Wizard é skippable com "Pular por agora" em todas as etapas.
- [ ] **AC11:** Redirect para `/onboarding` após primeiro login se `context_data` está vazio.

### Frontend — Integração
- [ ] **AC12:** `useSearchFilters` carrega defaults do perfil contextualizado quando disponível.
- [ ] **AC13:** Menu de perfil tem link "Atualizar meu perfil de licitações" → `/onboarding`.

### Regressão
- [ ] **AC14:** Usuários sem context_data continuam usando defaults genéricos (sem erro).
- [ ] **AC15:** Signup flow existente não é afetado.

## Definition of Done
- Todos os ACs checked
- Migration testada
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
