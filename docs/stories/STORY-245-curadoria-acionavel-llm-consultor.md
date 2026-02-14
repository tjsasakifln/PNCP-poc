# STORY-245: Curadoria Acionável — LLM como Consultor Estratégico

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-245 |
| **Priority** | P1 |
| **Sprint** | Sprint 3 |
| **Estimate** | 12h |
| **Depends on** | STORY-240 (dados de "licitações abertas" com dias_restantes) |
| **Blocks** | Nenhuma |

## Problema
O resumo executivo atual (`llm.py:110-142`) é genérico: "Você é um analista de licitações. Analise e gere um resumo." O LLM devolve um parágrafo descritivo que NÃO ajuda o usuário a DECIDIR. Falta:
- Recomendação de ação ("candidate-se a ESTA licitação porque...")
- Score de relevância por oportunidade
- Alertas de urgência acionáveis
- Contexto setorial (o que avaliar antes de licitar)

## Solução
Transformar o prompt do LLM de "gerador de resumo" para "consultor de licitações". O output será acionável com recomendações priorizadas. Modelo: GPT-4.1-nano (conforme diretriz do usuário).

## Investigação Técnica

### Estado Atual do LLM

- **Arquivo:** `backend/llm.py`
- **Modelo:** `gpt-4.1-nano` (line 160)
- **Temperature:** 0.3 (line 166)
- **Max tokens:** 500 (line 167) — INSUFICIENTE para curadoria detalhada
- **System prompt:** Genérico (lines 110-142)
- **Output schema:** `ResumoLicitacoes` em `schemas.py:545-583` — campos limitados: resumo_executivo, total_oportunidades, valor_total, destaques, alerta_urgencia

### Schema Atual vs Necessário

```
ATUAL (ResumoLicitacoes):
- resumo_executivo: str
- total_oportunidades: int
- valor_total: float
- destaques: list[str]
- alerta_urgencia: Optional[str]

NECESSÁRIO (ResumoEstrategico):
- resumo_executivo: str (agora com tom consultivo)
- total_oportunidades: int
- valor_total: float
- recomendacoes: list[Recomendacao]
  - oportunidade: str (nome/orgão)
  - valor: float
  - urgencia: "alta" | "media" | "baixa"
  - acao_sugerida: str ("Prepare documentação até X" / "Avalie requisitos técnicos")
  - justificativa: str ("Valor compatível com seu porte, órgão com bom histórico de pagamento")
- alertas_urgencia: list[str] (múltiplos, não apenas 1)
- insight_setorial: str (contexto do setor: "Este mês há 20% mais oportunidades que o anterior")
```

### Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `backend/schemas.py` | Novo schema `Recomendacao` e `ResumoEstrategico` (extends ResumoLicitacoes para backward compat) |
| `backend/llm.py:110-142` | System prompt completo com persona de consultor, regras de recomendação, formato de output |
| `backend/llm.py:160-168` | `max_tokens=1200` (curadoria precisa mais espaço) |
| `backend/llm.py:271-377` | `gerar_resumo_fallback()` — atualizar para retornar `ResumoEstrategico` |
| `backend/main.py` | Endpoint `/buscar` — passar `sector_name` corretamente ao `gerar_resumo()` |
| `frontend/app/buscar/components/ResultPanel.tsx` (ou equivalente) | Renderizar recomendações com cards de ação |

### Custos
- GPT-4.1-nano com max_tokens=1200: ~$0.001 por chamada
- Impacto mensal estimado: ~R$ 2-5/mês para 1000 buscas

## Acceptance Criteria

### Backend — Schema
- [x] **AC1:** Schema `Recomendacao` com campos: oportunidade, valor, urgencia (enum), acao_sugerida, justificativa.
- [x] **AC2:** Schema `ResumoEstrategico` extends `ResumoLicitacoes` com campos adicionais: recomendacoes (list), alertas_urgencia (list), insight_setorial (str).
- [x] **AC3:** `ResumoEstrategico` é backward compatible — campos antigos (resumo_executivo, destaques, etc.) continuam presentes.

### Backend — LLM
- [x] **AC4:** System prompt inclui persona de consultor com experiência no setor específico.
- [x] **AC5:** System prompt instrui: "Para cada oportunidade relevante, forneça ação concreta e justificativa".
- [x] **AC6:** System prompt inclui regras de urgência: alta (<3 dias), media (3-7 dias), baixa (>7 dias).
- [x] **AC7:** `max_tokens` aumentado para 1200.
- [x] **AC8:** Forbidden terms validation mantida (lines 209-227).
- [x] **AC9:** Fallback (`gerar_resumo_fallback`) retorna `ResumoEstrategico` com recomendações baseadas em heurísticas (top 5 por valor + urgência).

### Frontend
- [x] **AC10:** Recomendações renderizadas como cards com: badge de urgência (cor), ação sugerida em destaque, valor formatado.
- [x] **AC11:** Insight setorial exibido como banner informativo acima das recomendações.
- [x] **AC12:** Alertas de urgência (múltiplos) exibidos como lista com ícones de alerta.

### Regressão
- [x] **AC13:** Endpoint `/buscar` retorna `ResumoEstrategico` sem quebrar clientes que consomem apenas campos de `ResumoLicitacoes`.
- [x] **AC14:** Testes existentes de LLM atualizados para novo schema.

## Definition of Done
- Todos os ACs checked
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
- Testado com chamada real ao GPT-4.1-nano (resultado coerente)
