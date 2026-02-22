# TFIX-006: Atualizar testes InstitutionalSidebar para benefícios atuais

**Status:** Pending
**Prioridade:** Média
**Estimativa:** 30min
**Arquivos afetados:** 1 test file

## Problema

5 testes em `InstitutionalSidebar.test.tsx` falham porque os textos esperados não correspondem ao conteúdo atual do componente.

## Causa Raiz

O componente `InstitutionalSidebar.tsx` foi atualizado (provavelmente em UX-341 ou UX-343) com novos textos de benefícios e estrutura, mas o teste ficou desatualizado.

### Divergências identificadas:

| Teste espera | Componente tem |
|---|---|
| `"Monitoramento em tempo real de licitações"` | `"Cobertura nacional de fontes oficiais"` |
| Login statistics (textos antigos) | Estatísticas atualizadas |
| Official data badge (`"Dados oficiais"` text) | Badge com texto/estrutura diferente |

## Testes que serão corrigidos

- `InstitutionalSidebar.test.tsx`: 5 falhas
  - `renders correct login benefits`
  - `renders login statistics`
  - `renders official data badge`
  - `badge has check icon`
  - `badge has proper styling`

## Critérios de Aceitação

- [ ] AC1: Testes atualizados para refletir textos atuais do componente
- [ ] AC2: 19/19 testes passam
- [ ] AC3: Variante signup continua passando (já passa hoje)

## Solução

1. Ler o conteúdo atual de `InstitutionalSidebar.tsx` (login benefits, statistics, badge)
2. Atualizar as expectativas no teste para corresponder exatamente ao que o componente renderiza
3. Verificar se a estrutura HTML do badge mudou (check icon, styling classes)

## Arquivos

- `frontend/__tests__/components/InstitutionalSidebar.test.tsx` — atualizar expectativas
