# STORY-250: Gestão de Pipeline de Oportunidades

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-250 |
| **Priority** | P2 |
| **Sprint** | Sprint 5 (backlog) |
| **Estimate** | 12h |
| **Depends on** | STORY-240 (dados de licitações abertas), STORY-245 (curadoria com recomendações), STORY-247 (perfil contextualizado) |
| **Blocks** | Nenhuma |

## Problema
Hoje o SmartLic é stateless: o usuário busca, vê resultados, baixa Excel. Não há como:
- Marcar uma licitação como "interessante" ou "em análise"
- Acompanhar prazos de licitações salvas
- Receber alerta quando uma licitação salva está perto de encerrar
- Ver histórico de licitações que participou

Sem pipeline, o usuário precisa manter controle externo (planilha, CRM). Isso reduz a aderência à plataforma.

## Solução
Adicionar gestão de pipeline com estágios: Descoberta → Em Análise → Preparando Proposta → Enviada → Resultado. Cada licitação pode ser movida entre estágios. Alertas automáticos para prazos.

## Investigação Técnica

### Modelo de Dados

```sql
CREATE TABLE pipeline_items (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  -- Dados da licitação (snapshot no momento de salvar)
  pncp_id text NOT NULL,
  objeto text NOT NULL,
  orgao text,
  uf text,
  valor_estimado numeric,
  data_encerramento timestamptz,
  link_pncp text,
  -- Pipeline
  stage text NOT NULL DEFAULT 'descoberta'
    CHECK (stage IN ('descoberta', 'analise', 'preparando', 'enviada', 'resultado')),
  notes text,
  -- Metadata
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  -- Prevenir duplicatas
  UNIQUE(user_id, pncp_id)
);

CREATE INDEX idx_pipeline_user_stage ON pipeline_items(user_id, stage);
CREATE INDEX idx_pipeline_encerramento ON pipeline_items(data_encerramento) WHERE stage NOT IN ('enviada', 'resultado');
```

### Endpoints API

| Method | Path | Descrição |
|--------|------|-----------|
| POST | `/v1/pipeline` | Adicionar licitação ao pipeline |
| GET | `/v1/pipeline` | Listar pipeline do usuário (com filtro por stage) |
| PATCH | `/v1/pipeline/{id}` | Atualizar stage ou notas |
| DELETE | `/v1/pipeline/{id}` | Remover do pipeline |
| GET | `/v1/pipeline/alerts` | Licitações com prazo < 3 dias |

### Frontend — Componentes

| Componente | Descrição |
|-----------|-----------|
| `PipelineBoard` | Kanban board com 5 colunas (stages) |
| `PipelineCard` | Card com dados da licitação + badge de urgência |
| `AddToPipelineButton` | Botão nos resultados de busca "Salvar no pipeline" |
| `PipelineAlerts` | Banner no topo com alertas de prazo |

### Dependências
- Supabase RLS: user pode ver/editar apenas seu próprio pipeline
- Requer autenticação (pipeline é feature de usuário logado)
- Tier: disponível a partir do plano "Profissional" (feature gating via ENABLE_NEW_PRICING)

## Acceptance Criteria

### Backend
- [x] **AC1:** Migration Supabase cria tabela `pipeline_items` com schema acima. RLS habilitado.
- [x] **AC2:** POST `/v1/pipeline` — adiciona item. Retorna 409 se já existe (UNIQUE constraint).
- [x] **AC3:** GET `/v1/pipeline?stage=analise` — lista com filtro por stage. Paginação: limit/offset.
- [x] **AC4:** PATCH `/v1/pipeline/{id}` — atualiza stage e/ou notes. Valida que stage é enum válido.
- [x] **AC5:** DELETE `/v1/pipeline/{id}` — remove. Retorna 404 se não existe ou não pertence ao user.
- [x] **AC6:** GET `/v1/pipeline/alerts` — retorna items com data_encerramento < now() + 3 dias e stage não em (enviada, resultado).
- [x] **AC7:** Todos os endpoints protegidos por auth. RLS garante isolamento por user_id.

### Frontend
- [x] **AC8:** Botão "Salvar no pipeline" nos cards de resultado de busca. Feedback visual ao salvar.
- [x] **AC9:** Página `/pipeline` com Kanban board. Drag-and-drop entre stages.
- [x] **AC10:** Pipeline alerts no header/sidebar quando há licitações com prazo < 3 dias.
- [x] **AC11:** Counter de items por stage visível no menu lateral.

### Feature Gating
- [x] **AC12:** Pipeline disponível apenas para planos Profissional e Empresarial (quota.py gating).
- [x] **AC13:** Plano Free Trial vê o botão "Salvar" mas recebe modal de upgrade.

### Regressão
- [x] **AC14:** Busca funciona normalmente sem pipeline (feature é additive).
- [x] **AC15:** Testes existentes passam.

## Definition of Done
- Todos os ACs checked
- Migration aplicada
- RLS testado
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
