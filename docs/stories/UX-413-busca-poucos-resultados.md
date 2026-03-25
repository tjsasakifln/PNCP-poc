# UX-413 — Busca Retorna Pouquíssimos Resultados

**Status:** Draft
**Severity:** CRITICAL
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Busca por "Engenharia, Projetos e Obras" em SC retornou apenas **2 resultados** de 15 analisadas. Histórico mostra padrão ainda pior:
- "Todo o Brasil" para Engenharia → **0 resultados** em 3 tentativas consecutivas
- Múltiplas buscas falharam com "Tempo esgotado" ou "O servidor reiniciou"
- Fonte LICITAJA falhou com erro JSON parse
- Banner "Resultados truncados" + "2/3 fontes"

## Impacto

Invalida a proposta de valor do produto. Usuário que busca Engenharia em todo o Brasil e recebe 0 resultados não vai pagar R$297/mês.

## Evidências

- Screenshot: `ux-audit-results.png`, `ux-audit-historico.png`
- Histórico: Das ~20 buscas recentes, maioria falhou (timeout, crash, 0 resultados)
- Busca com 4 UFs (ES, MG, RJ, SP) que funcionou retornou 66 resultados — indica que o problema é intermitente

## Causas Prováveis

1. **Período padrão de 10 dias** muito curto — reduzido de 15 que já era reduzido de 180
2. **LICITAJA como fonte** falha consistentemente (JSON parse error)
3. **Timeouts frequentes** — cadeia de timeout pode estar matando requests legítimas
4. **"Todo o Brasil" (27 UFs)** ultrapassa timeout com batching de 5 UFs por vez
5. **Filtro "Abertas" muito restritivo** — muitas licitações já encerraram proposta dentro dos 10 dias

## Acceptance Criteria

- [ ] AC1: Busca "Engenharia" em SC retorna >= 10 resultados (comparar com PNCP direto)
- [ ] AC2: Busca "Todo o Brasil" para qualquer setor não retorna 0 resultados (a menos que realmente não haja)
- [ ] AC3: Taxa de falha de buscas < 10% (hoje está > 50% pelo histórico)
- [ ] AC4: Fontes que falham não reduzem contagem a ponto de parecer vazio — mostrar resultados parciais com aviso
- [ ] AC5: Considerar período padrão de 15-30 dias para setores com menor volume (Engenharia)
- [ ] AC6: LICITAJA: resolver JSON parse error ou remover/desabilitar fonte se não é confiável

## Investigação

1. Comparar resultado SmartLic vs busca direta no PNCP para mesmo período/UF/setor
2. Analisar logs do backend para entender causa raiz dos timeouts em 24/03
3. Verificar se LICITAJA está descontinuado ou com API alterada
4. Avaliar se período default deveria variar por setor (construção tem ciclos mais longos)
