# STORY-TD-006: Mensagens de Erro e UX de Navegacao

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 1: Seguranca e Correcoes

## Prioridade
P1

## Estimativa
8h

## Descricao

Esta story melhora a experiencia do usuario em dois pontos de alta friccao: mensagens de erro em ingles tecnico fora da pagina de login, e perda de resultados de busca ao navegar sem aviso.

1. **Dicionario centralizado de mensagens de erro (IC-06, MEDIUM, 4h)** -- Atualmente, a pagina de login traduz erros para portugues amigavel ("E-mail ou senha incorretos"), mas a pagina de busca mostra "502 Bad Gateway" raw. A inconsistencia e jarring e transmite falta de profissionalismo. Criar `lib/error-messages.ts` com mapeamento de codigos HTTP e mensagens de erro comuns para portugues amigavel. Usar em todos os catch blocks do frontend.

2. **Confirmacao de saida com resultados ativos (MF-01, MEDIUM, 4h)** -- Uma busca leva 15-60 segundos. Perder o resultado ao navegar acidentalmente (clicar em link, usar o botao voltar) sem aviso e frustrante. Implementar `beforeunload` event e/ou Next.js route change listener para perguntar ao usuario se quer mesmo sair quando houver resultados de busca ativos na pagina.

## Itens de Debito Relacionados
- IC-06 (MEDIUM): Traducao de mensagens de erro apenas na pagina de login
- MF-01 (MEDIUM): Sem confirmacao ao sair de `/buscar` com resultados

## Criterios de Aceite

### Dicionario de Erros
- [ ] Arquivo `lib/error-messages.ts` criado com mapeamento de erros
- [ ] Mapeamento inclui: 400, 401, 403, 404, 408, 429, 500, 502, 503, 504
- [ ] Mensagens em portugues amigavel (ex: "Servico temporariamente indisponivel" para 503)
- [ ] Funcao utilitaria `getErrorMessage(error)` que aceita Error, AxiosError, ou string
- [ ] Pagina `/buscar` usa mensagens traduzidas (nao mostra raw HTTP errors)
- [ ] Pagina `/pipeline` usa mensagens traduzidas
- [ ] Nenhum catch block no frontend mostra erro raw ao usuario
- [ ] Mensagem generica para erros desconhecidos: "Ocorreu um erro inesperado. Tente novamente."

### Confirmacao de Navegacao
- [ ] Ao navegar fora de `/buscar` COM resultados ativos, usuario ve dialogo de confirmacao
- [ ] Ao navegar fora de `/buscar` SEM resultados, navegacao ocorre normalmente (sem dialogo)
- [ ] `beforeunload` event previne fechamento acidental da aba com resultados
- [ ] Route change listener previne navegacao interna com resultados
- [ ] Dialogo usa linguagem clara: "Voce tem resultados de busca que serao perdidos. Deseja sair?"
- [ ] Opcoes: "Sair" e "Continuar na pagina"
- [ ] Se usuario salvar os resultados (download Excel), confirmacao nao aparece mais

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| REG-T14 | Navegacao com resultados ativos mostra confirmacao | E2E | P2 |
| -- | Erro 502 na busca mostra mensagem em portugues | Unitario | P1 |
| -- | Erro 429 na busca mostra "Muitas requisicoes" | Unitario | P1 |
| -- | Navegacao sem resultados nao mostra confirmacao | E2E | P2 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (independente)

## Riscos
- `beforeunload` event tem limitacoes de customizacao em browsers modernos (texto fixo do browser).
- Route change listener do Next.js pode variar entre versoes. Testar com App Router.
- Mensagens de erro precisam cobrir edge cases (timeout, CORS, network offline).

## Rollback Plan
- Desabilitar confirmacao de navegacao se causar problemas (ex: popup indesejado em cenarios legitimos).
- Manter dicionario de erros mesmo se confirmacao for revertida.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + E2E)
- [ ] CI/CD green
- [ ] Documentacao atualizada
- [ ] Deploy em staging verificado
- [ ] Verificacao manual: erro 500 mostra mensagem amigavel em portugues
- [ ] Verificacao manual: sair de `/buscar` com resultados mostra confirmacao
