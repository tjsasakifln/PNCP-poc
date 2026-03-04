# STORY-400: Corrigir link "Ver Edital" quebrado e enriquecer detalhes do card de licitação

**Prioridade:** P0
**Esforço:** M
**Squad:** team-bidiq-feature

## Contexto
O botão "Ver Edital" é a principal call-to-action do card de licitação — e está quebrado para uma parcela significativa dos resultados PNCP. Quando o PNCP não retorna o campo `linkSistemaOrigem`, o backend envia `link_edital=""` (string vazia), e o frontend renderiza `<a href="">`, que recarrega a página atual. Além disso, o card mostra informações escassas: apenas Órgão, Modalidade e datas. Faltam dados como CNPJ do órgão, número do edital, esfera governamental e fonte dos dados — informações que o backend já retorna mas o frontend ignora.

## Problema (Causa Raiz)

**Link quebrado:**
- `backend/pncp_client.py:2458`: `link_edital=item.get("linkSistemaOrigem", "")` — fallback para string vazia quando campo ausente.
- `frontend/app/components/LicitacaoCard.tsx:634`: `href={licitacao.link}` renderizado incondicionalmente sem validação de URL vazia.
- Não há construção de link fallback usando o `pncp_id` (que permite montar URL: `https://pncp.gov.br/app/editais/{orgaoCnpj}/{ano}/{sequencial}`).

**Detalhes esparsos:**
- `frontend/app/components/LicitacaoCard.tsx:459-630`: Card mostra Objeto, Órgão, Modalidade, Datas e Valor, mas não mostra número do edital, CNPJ, esfera, fonte (PNCP/PCP/ComprasGov) ou link alternativo ao PNCP.

## Critérios de Aceitação
- [ ] AC1: Backend (`pncp_client.py`): Quando `linkSistemaOrigem` estiver vazio/null, construir link fallback usando template `https://pncp.gov.br/app/editais/{orgaoCnpj}/{ano}/{sequencialCompra}` (campos já presentes na resposta PNCP).
- [ ] AC2: Backend: Garantir que `link_edital` nunca seja string vazia — deve ser URL válida ou `null`.
- [ ] AC3: Frontend (`LicitacaoCard.tsx`): Quando `licitacao.link` for `null`/vazio, desabilitar botão "Ver Edital" com tooltip "Link indisponível na fonte" e estilo visual `opacity-50 cursor-not-allowed`.
- [ ] AC4: Frontend (`LicitacaoCard.tsx`): Adicionar badge de fonte de dados (PNCP/PCP/ComprasGov) usando campo `_source` já retornado pelo backend. Badge compacto com ícone.
- [ ] AC5: Frontend (`LicitacaoCard.tsx`): Mostrar número do edital (`numeroCompra` ou `pncp_id`) quando disponível, abaixo do título.
- [ ] AC6: Frontend (`LicitacaoCard.tsx`): Mostrar CNPJ do órgão formatado quando disponível, ao lado do nome do órgão.
- [ ] AC7: Nenhum link `<a href="">` deve existir no DOM quando o link do edital não está disponível.

## Arquivos Impactados
- `backend/pncp_client.py` — Construir link fallback a partir de campos PNCP; nunca retornar `""`.
- `frontend/app/components/LicitacaoCard.tsx` — Validar `link` antes de renderizar; adicionar fonte, número, CNPJ.
- `frontend/app/types.ts` — Garantir que tipo `Licitacao` permite `link: string | null`.

## Testes Necessários
- [ ] Backend: Teste unitário para link fallback quando `linkSistemaOrigem` ausente.
- [ ] Backend: Teste unitário confirmando que `link_edital` nunca retorna `""`.
- [ ] Frontend: Teste que card com `link=""` não renderiza `<a href="">`.
- [ ] Frontend: Teste que card com `link=null` mostra botão desabilitado com tooltip.
- [ ] Frontend: Teste que badge de fonte renderiza corretamente para cada source.
- [ ] Frontend: Snapshot visual do card com e sem link.

## Notas Técnicas
- O PNCP popula `linkSistemaOrigem` em ~86% dos registros. Para os 14% restantes, o link fallback com CNPJ+ano+sequencial resolve a maioria.
- Verificar se `orgaoCnpj`, `anoCompra`, `sequencialCompra` estão presentes na resposta. Caso contrário, fallback para `null`.
- Não alterar o campo `link` para PCP — PCP tem seu próprio sistema de links.
