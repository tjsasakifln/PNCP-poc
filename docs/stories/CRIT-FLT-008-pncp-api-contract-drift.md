# CRIT-FLT-008 — PNCP API Contract Drift (Breaking Changes)

**Prioridade:** P1 — Resiliência da Fonte Primária
**Estimativa:** 3h
**Origem:** Auditoria de Pipeline 2026-02-22
**Track:** Backend

## Problema

A auditoria direta da API PNCP revelou mudanças no contrato da API que podem impactar nosso pipeline:

### 1. `codigoModalidadeContratacao` Agora Obrigatório

**Antes:** Parâmetro opcional — podíamos buscar "todas as modalidades" em uma chamada
**Agora:** Parâmetro **obrigatório** — chamada sem ele retorna HTTP 400:
```json
{
  "status": 400,
  "message": "Required parameter 'codigoModalidadeContratacao' is not present."
}
```

**Status do nosso código:** `pncp_client.py` já passa modalidade por chamada (uma chamada por UF+modalidade), então **funciona**. Mas:
- O health canary (`_health_canary()`) pode estar enviando request sem modalidade
- Testes que mockam a API podem não validar este requisito
- Se alguém modificar o código para omitir modalidade, não há guard

### 2. `linkProcessoEletronico` Sempre Vazio

**Achado:** `linkProcessoEletronico` presente em **0% dos 200 itens** analisados.
**Impacto:** Se o frontend exibe um link "Ver processo eletrônico" baseado neste campo, ele nunca funciona.
**Alternativa:** `linkSistemaOrigem` presente em **86% dos itens** — usar como fallback.

### 3. 99.5% Status = "Divulgada no PNCP"

**Achado:** Quase todos os itens retornados têm `situacaoCompraNome = "Divulgada no PNCP"`.
**Impacto:** Nosso `status_inference.py` precisa inferir status real a partir de datas (dataAberturaProposta, dataEncerramentoProposta) porque o campo da API é inútil.
**Status:** Já implementado e funcionando via `enriquecer_com_status_inferido()`.

### 4. `valorTotalHomologado` Presente em Apenas 2%

**Achado:** Apenas 4 de 200 itens (2%) têm `valorTotalHomologado`.
**Impacto:** Não podemos usar esse campo como fallback confiável para valor estimado.

## Acceptance Criteria

### Guard contra API Drift

- [x] **AC1:** Adicionar validação no `pncp_client.py` que garante `codigoModalidadeContratacao` SEMPRE presente nos params antes de fazer request. Se ausente, raise `ValueError` com mensagem clara (não enviar request que vai dar 400)
- [x] **AC2:** Verificar que `_health_canary()` envia `codigoModalidadeContratacao` no request
- [x] **AC3:** Criar teste `test_pncp_client_requires_modalidade.py` que valida que requests sem modalidade são bloqueados antes de sair

### Campo de Link

- [x] **AC4:** No `LicitacaoItem` (schemas.py), priorizar `linkSistemaOrigem` sobre `linkProcessoEletronico` como link primário
- [x] **AC5:** No frontend, usar `linkSistemaOrigem` como "Ver no portal" quando disponível (86% dos casos)
- [x] **AC6:** Remover referências a `linkProcessoEletronico` que nunca funcionam

### Monitoramento de Contract Drift

- [x] **AC7:** Criar smoke test semanal (`scripts/pncp_api_smoke_test.py`) que:
  - Faz 1 chamada real à API PNCP com params mínimos válidos
  - Verifica que os campos esperados existem na resposta
  - Verifica que novos campos required não foram adicionados
  - Alerta se a response structure mudou significativamente
- [x] **AC8:** Documentar campos "mortos" (nunca populados) vs "vivos" no `docs/api/pncp-field-audit.md`

## Campos Auditados

| Campo | Presença | Observação |
|-------|----------|------------|
| objetoCompra | 100% | Sempre presente |
| valorTotalEstimado | 100% | Presente mas 25% = R$ 0 |
| valorTotalHomologado | 2% | Quase inexistente |
| dataPublicacaoPncp | 100% | Sempre presente |
| dataAberturaProposta | 100% | Sempre presente |
| dataEncerramentoProposta | 100% | Sempre presente |
| linkProcessoEletronico | **0%** | **MORTO** |
| linkSistemaOrigem | 86% | Melhor alternativa |
| informacaoComplementar | 59% | Útil como texto adicional |
| situacaoCompraNome | 100% | Mas 99.5% = "Divulgada no PNCP" (inútil) |
| srp | 100% | 38% true, 62% false |

## Impacto

- **Resiliência:** Protege contra futuras mudanças na API PNCP
- **UX:** Links que realmente funcionam (linkSistemaOrigem vs linkProcessoEletronico)
- **Observabilidade:** Smoke test detecta drift antes de impactar produção

## Arquivos

- `backend/pncp_client.py` (validação de params)
- `backend/schemas.py` (prioridade de campos de link)
- `backend/scripts/pncp_api_smoke_test.py` (NOVO)
- `frontend/app/buscar/components/SearchResults.tsx` (link do portal)
- `docs/api/pncp-field-audit.md` (NOVO)
