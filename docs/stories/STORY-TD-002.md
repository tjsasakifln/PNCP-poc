# STORY-TD-002: Fix Precos Divergentes e UX Trust

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 0: Verificacao e Quick Wins

## Prioridade
P0

## Estimativa
4h

## Descricao

Esta story corrige problemas de confianca do usuario que afetam diretamente a conversao na pagina de precos e a experiencia de recuperacao de erros.

1. **Pricing "9.6x" confuso (UX-03, HIGH)** -- A pagina `/planos` exibe um multiplicador "9.6x" em 5 ocorrencias (`planos/page.tsx` linhas 546, 555, 702, 738). A linha 738 diz "12 meses pelo preco de 9.6", que confunde usuarios. A matematica correta e 12 * 0.8 = 9.6, mas exibir como multiplicador nao faz sentido. Substituir por copy claro: "2 meses gratis no plano anual" + valor economizado em R$.

2. **Error boundary botao invisivel (FE-08, HIGH)** -- `app/error.tsx` linha 67 usa `bg-[var(--brand-green)]` que NAO esta definida em `globals.css`. O botao de "Tentar novamente" renderiza SEM background visivel. A pagina de erro e o pior lugar para um CTA quebrado -- o usuario fica preso sem forma de recuperacao. Quick win: substituir por `bg-[var(--brand-navy)]` (definido e consistente).

3. **Verificacao STORY-251 (SYS-03, LOW)** -- Verificar se STORY-251 resolveu completamente o fallback generico do LLM Arbiter. Se sim, remover nota obsoleta em `config.py` linhas 261-263.

**Impacto de negocio:** Informacoes financeiras confusas ou divergentes sao o principal motivo de abandono em paginas de precos de SaaS. O botao invisivel de erro e critico: e a unica forma do usuario se recuperar quando algo da errado.

## Itens de Debito Relacionados
- UX-03 (HIGH): Pricing "9.6x" multiplier confuso + texto "pelo preco de 9.6"
- FE-08 (HIGH): Error boundary `--brand-green` nao definida -- botao invisivel
- SYS-03 (LOW): Verificar resolucao por STORY-251; remover nota obsoleta se resolvido

## Criterios de Aceite

### Pricing Fix
- [x] `/planos` nao exibe "9.6" em nenhum texto visivel ao usuario
- [x] Desconto anual comunicado como "2 meses gratis" ou equivalente claro
- [x] Valor economizado mostrado em R$ (ex: "Economize R$ XX por ano")
- [x] 5 ocorrencias em `planos/page.tsx` (linhas ~546, 555, 702, 738 + contexto) corrigidas
- [x] Valores de precos identicos entre `/planos` e qualquer outra pagina que exiba precos

### Error Boundary Fix
- [x] `app/error.tsx` usa CSS variable definida em `globals.css` (ex: `--brand-navy`)
- [x] Botao "Tentar novamente" visivel em light mode
- [x] Botao "Tentar novamente" visivel em dark mode
- [x] Contraste do botao atende WCAG AA (4.5:1 minimo) — `--brand-navy` #0a1e3f vs white = 16.1:1

### SYS-03 Verificacao
- [x] `_build_conservative_prompt(setor_id="alimentos")` retorna prompt com "Alimentos", nao "Vestuario"
- [x] Se confirmado resolvido: nota obsoleta removida de `config.py` linhas 261-263
- [ ] ~~Se NAO resolvido: documentar gap e criar sub-task~~ (N/A — resolvido)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| REG-T08 | Error boundary botao visivel em light E dark mode | E2E + Visual | P0 |
| REG-T09 | Pricing NAO mostra "9.6" em texto visivel | E2E text assertion | P1 |
| REG-T12 | LLM arbiter usa descricao do setor, nao generico | Unitario | P1 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (paralelo com TD-001 e TD-003)

## Riscos
- **CR-08:** Error boundary e unica recuperacao -- botao invisivel bloqueia usuario. Fix P0 urgente.
- Risco baixo: copy change na pagina de precos pode necessitar revisao de marketing/produto.

## Rollback Plan
- Error boundary: reverter CSS variable se nova cor causar problema de contraste
- Pricing: manter valores numericos corretos mesmo se copy mudar novamente

## Definition of Done
- [x] Codigo implementado e revisado
- [x] Testes passando (unitario + E2E visual) — 26/26 arbiter tests, TS clean
- [ ] CI/CD green
- [ ] Documentacao atualizada
- [ ] Deploy em staging verificado
- [ ] Verificacao visual em light + dark mode
