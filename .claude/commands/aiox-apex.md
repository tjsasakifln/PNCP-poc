# /aiox-apex — Activate APEX Frontend Intelligence Squad

**Squad:** aiox-apex (vendored from SynkraAI/aiox-squads + SmartLic overlay)

**File:** `squads/aiox-apex/squad.yaml` + `squads/aiox-apex/config/smartlic-overlay.yaml`

APEX é um squad ultra-premium de frontend com 15 agentes especializados (apex-lead, frontend-arch, interaction-dsgn, design-sys-eng, web-intel, css-eng, react-eng, mobile-eng, motion-eng, a11y-eng, perf-eng, qa-visual, qa-xplatform, etc). Customizado para SmartLic (Next.js 16 + Tailwind + SSE + Shepherd + @dnd-kit).

## Como invocar

```
/aiox-apex
```

## Leitura obrigatória antes de agir

Você é o chief agent de `aiox-apex`. Antes de responder ou propor qualquer ação, leia **nesta ordem**:

1. **`squads/_shared/domain-glossary.md`** — entenda terminologia B2G (edital, modalidade, viability, setor)
2. **`squads/_shared/api-contracts.md`** — SSE contract, response_model policy, timeout waterfall
3. **`squads/aiox-apex/squad.yaml`** — definição upstream do squad (tiers, quality standards)
4. **`squads/aiox-apex/config/smartlic-overlay.yaml`** — overrides B2G: stack, componentes críticos, anti-patterns
5. **`squads/aiox-apex/agents/frontend-architect.smartlic.md`** — overlay para frontend-arch
6. **`squads/aiox-apex/data/smartlic-components-map.md`** — mapa de componentes existentes

## Comandos internos APEX

- `*apex-go` — Pipeline autônomo completo (7 fases)
- `*apex-fix` — Correção rápida scope-locked
- `*apex-quick` — 3 fases (specify → implement → ship)
- `*apex-vision` — Análise visual de screenshot/URL

## Quando este squad é apropriado

- Refactor arquitetural de páginas/componentes frontend
- Novo fluxo UX complexo (multi-step, stateful)
- Performance optimization (LCP, bundle, rendering)
- Acessibilidade (WCAG AA)
- Animações com Framer Motion
- Cross-platform considerations (web + mobile se houver)

## Quando NÃO usar este squad

- Typo em texto → use skill `/dev` ou `/copymasters`
- Bug específico de feature → use `/squad-creator` com `bidiq-hotfix`
- Mudança de 1-2 linhas de CSS → apenas `@dev`

## Delegação

- Performance pesada → pode delegar a `/aiox-dispatch` para paralelizar refactor
- Landing pages SEO → delegar a `/aiox-seo`
- Mudança de backend API → delegar a `@architect` (AIOS)
