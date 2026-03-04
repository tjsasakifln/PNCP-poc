# STORY-401: Corrigir exibição "R$ 0" para licitações PCP e unificar formatação de moeda

**Prioridade:** P0
**Esforço:** M
**Squad:** team-bidiq-feature

## Contexto
Licitações vindas do Portal de Compras Públicas (PCP v2) exibem "R$ 0" porque a API v2 não retorna dados de valor. Isso confunde usuários que interpretam como licitação sem valor estimado, quando na verdade o dado simplesmente não está disponível. Além disso, existem duas funções `formatCurrency` independentes no frontend, causando inconsistência visual: `lib/format-currency.ts` (com abreviação "R$ 3,5 bi" e normalização de espaço) vs `LicitacaoCard.tsx:323-329` (básica, sem abreviação nem normalização).

## Problema (Causa Raiz)

**"R$ 0" enganoso:**
- `backend/clients/portal_compras_client.py:498`: `valor = 0.0` hardcoded porque API v2 não tem campo de valor.
- Frontend renderiza `formatCurrency(0)` = "R$ 0" sem distinguir "valor é zero" de "valor indisponível".

**Formatação inconsistente:**
- `frontend/lib/format-currency.ts:5-21`: `formatCurrencyBR()` — abreviação inteligente + normalização `\u00A0`.
- `frontend/app/components/LicitacaoCard.tsx:323-329`: `formatCurrency()` local — Intl.NumberFormat básico sem abreviação.
- Outros componentes (PipelineCard, HistoricoPage, Dashboard) usam `formatCurrencyBR`. Apenas LicitacaoCard usa a versão local.

## Critérios de Aceitação
- [x] AC1: Backend (`portal_compras_client.py`): Mudar `valor=0.0` para `valor=None` (ou `valor_estimado=None`) para licitações PCP v2.
- [x] AC2: Backend (`schemas.py`): Garantir que `valor_estimado` aceita `Optional[float]` (já é assim em muitos schemas, verificar BuscaResultItem).
- [x] AC3: Frontend (`LicitacaoCard.tsx`): Quando `valor` for `null`/`undefined`/`0`, exibir "Valor não informado" em texto cinza (`text-ink-muted`) com tooltip "Fonte PCP v2 não disponibiliza valor estimado" em vez de "R$ 0".
- [x] AC4: Frontend (`LicitacaoCard.tsx`): Remover função local `formatCurrency()` e substituir por import de `formatCurrencyBR` de `lib/format-currency.ts`.
- [x] AC5: Verificar e corrigir todos os usos de `formatCurrency` local em outros componentes (LicitacoesPreview, etc.) para usar `formatCurrencyBR`.
- [x] AC6: "R$ 0" nunca deve aparecer para o usuário final em nenhum componente.
- [x] AC7: Valores acima de R$ 1 milhão devem usar abreviação ("R$ 3,5 mi") consistentemente em cards, pipeline e histórico.

## Arquivos Impactados
- `backend/clients/portal_compras_client.py` — `valor = None` em vez de `0.0`.
- `backend/schemas.py` — Confirmar `valor_estimado: Optional[float] = None`.
- `frontend/app/components/LicitacaoCard.tsx` — Remover `formatCurrency` local, importar `formatCurrencyBR`, tratar `null`.
- `frontend/app/components/LicitacoesPreview.tsx` — Verificar uso de formatação.
- `frontend/app/pipeline/PipelineCard.tsx` — Verificar consistência.

## Testes Necessários
- [x] Backend: Teste que licitação PCP retorna `valor=None` (não `0.0`). → `test_ux401_valor_none.py` (16 tests)
- [x] Frontend: Teste que `valor=null` renderiza "Valor não informado". → `LicitacaoCard-ux401.test.tsx`
- [x] Frontend: Teste que `valor=0` renderiza "Valor não informado" (não "R$ 0"). → `LicitacaoCard-ux401.test.tsx`
- [x] Frontend: Teste que `valor=3500000` renderiza "R$ 3,5 mi". → `LicitacaoCard-ux401.test.tsx`
- [x] Frontend: Teste que `valor=45000` renderiza "R$ 45.000". → `LicitacaoCard-ux401.test.tsx`
- [x] Frontend: Snapshot visual do card com valor null vs valor positivo. → `LicitacaoCard-ux401.test.tsx`

## Notas Técnicas
- `valor=0.0` é usado como sentinela em várias partes do filtro de valor (`filter.py`). Ao mudar para `None`, garantir que `filter.py` trata `None` como "sem filtro de valor" (pula o check, não rejeita).
- O backend também precisa ajustar `viability.py` — viabilidade com `valor=None` deve gerar nota neutra no fator valor, não penalizar.
- `formatCurrencyBR` já é testado em `format-currency.test.ts` — não precisa de novos testes para a função em si.
