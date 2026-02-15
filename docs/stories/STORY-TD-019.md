# STORY-TD-019: Backlog -- Polimento e Otimizacao

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 3+ (Backlog, ongoing)

## Prioridade
P3

## Estimativa
~157h (trabalhados incrementalmente)

## Descricao

Esta story umbrella agrupa todos os 51 itens P3 restantes que nao foram incluidos nos Sprints 0-3. Estes itens representam polimento, otimizacoes e melhorias de consistencia que sao valiosas mas nao urgentes. Devem ser trabalhados incrementalmente, priorizados por valor de negocio e agrupados por area.

**Este nao e um sprint unico** -- e um backlog de trabalho continuo que pode ser distribuido ao longo de multiplos sprints futuros, priorizados conforme necessidade.

## Itens de Debito Relacionados

### Backend/Infra (14 itens, ~89h)

| ID | Debito | Horas |
|----|--------|-------|
| SYS-01 | Frontend test coverage abaixo de 60% (parcial, apos TD-013/TD-015) | 40h |
| SYS-12 | Feature flags apenas em env vars (7+ flags requerem restart) | 8h |
| SYS-13 | `dotenv` carregado antes de imports FastAPI em nivel de modulo | 2h |
| SYS-14 | User-Agent hardcoded "BidIQ/1.0" (renomeado para SmartLic) | 2h |
| SYS-15 | Sem connection pooling no Supabase client | 8h |
| SYS-16 | Integration tests job e placeholder (echo skip) | 16h |
| SYS-17 | Sem request timeout para Stripe webhooks | 4h |
| SYS-18 | (parcial se nao completado em TD-003) | -- |
| SYS-19 | (completado em TD-003) | -- |
| SYS-20 | (completado em TD-008) | -- |
| SYS-21 | (completado em TD-008) | -- |
| SYS-22 | (completado em TD-003) | -- |
| SYS-23 | (completado em TD-003) | -- |
| SYS-24 | `email_service.py` usa `time.sleep()` sincrono | 1h |

### Database (4 itens, ~4.5h)

| ID | Debito | Horas |
|----|--------|-------|
| DB-08 | Stripe production price IDs hardcoded em migration 015 | 1h |
| DB-10 | `search_results_cache.results` JSONB pode ser 10-100KB por entry | 2h |
| DB-12 | (completado em TD-003) | -- |
| DB-14 | `search_results_cache` sem INSERT policy para usuarios | 1h |

### Frontend/UX -- Consistencia Visual (15 itens, ~31h)

| ID | Debito | Horas |
|----|--------|-------|
| IC-01 | "SmartLic" hardcoded no header apesar de APP_NAME env var | 1h |
| IC-02 | Mixed color approaches (Tailwind tokens vs inline CSS vars) | 4h |
| IC-03 | Icon sources mixed (lucide-react vs inline SVGs) | 4h |
| IC-04 | Loading spinner styles variam entre componentes | 4h |
| IC-05 | Link vs anchor tag misturados para navegacao interna | 2h |
| IC-07 | Max-width container varia (documentar rationale) | 4h |
| FE-13 | Auth guard duplicado entre middleware.ts e layout.tsx | 4h |
| FE-14 | Console.log statements em AuthProvider (debug OAuth) | 1h |
| FE-15 | `useEffect` com dependencies faltando (4 eslint-disable) | 8h |
| FE-16 | Search state usa `window.location.href` (17+ ocorrencias) | 2h |
| FE-18 | `next.config.js` usa CommonJS enquanto resto e ESM | 2h |
| FE-19 | Pull-to-refresh CSS hack desabilita pointer-events | 4h |

### Frontend/UX -- Acessibilidade (7 itens, ~19h)

| ID | Debito | Horas |
|----|--------|-------|
| A11Y-03 | Custom dropdowns (CustomSelect) sem aria-activedescendant | 4h |
| A11Y-04 | Pull-to-refresh sem alternativa de keyboard | 4h |
| A11Y-05 | Shepherd.js onboarding pode bloquear conteudo sem inert | 4h |
| A11Y-06 | UF buttons usam title mas sem aria-label para nome do estado | 2h |
| A11Y-07 | Keyboard shortcuts sem opcao de desabilitar/customizar | 4h |
| A11Y-08 | Icones SVG com aria-label="Icone" generico | 2h |
| A11Y-09 | Dark mode --ink-muted a 4.9:1 (borderline AA) | 1h |

### Frontend/UX -- UX e Micro-Feedback (11 itens, ~36h)

| ID | Debito | Horas |
|----|--------|-------|
| UX-04 | Pipeline page nao otimizada para mobile (5 colunas) | 16h |
| UX-05 | Admin page table nao responsiva (audience: 1-2 pessoas) | 2h |
| UX-NEW-03 | Admin page usa window.confirm() nativo para delecao | 2h |
| UX-NEW-04 | Sem empty state para pagina de pipeline | 2h |
| UX-NEW-05 | Pipeline column count forca horizontal scroll em tablet | 2h |
| MF-02 | Sem feedback "Copiado para clipboard" (Sonner toast) | 2h |
| MF-03 | Pipeline DnD sem feedback haptico/audio em mobile | 4h |
| MF-04 | Mudanca de setor nao confirma que resultados foram limpos | 2h |

## Criterios de Aceite

Como esta e uma story umbrella, os criterios sao por grupo:

### Ao resolver um item do backlog:
- [ ] Item individual tem PR dedicado com testes
- [ ] CI/CD green apos merge
- [ ] Pontos positivos preservados (Secao 9 do assessment)
- [ ] Item marcado como resolvido neste documento

### Metricas de saude do backlog:
- [ ] Review mensal do backlog (repriorizar conforme necessidade)
- [ ] Items resolvidos documentados no changelog
- [ ] Nenhum item P3 promovido a P0/P1 sem justificativa

## Priorizacao Recomendada (por valor)

1. **Quick wins (< 2h cada):** SYS-14, SYS-24, FE-14, A11Y-09, DB-08, MF-02, UX-NEW-04
2. **Backend scalability:** SYS-15, SYS-17, SYS-12
3. **UX mobile:** UX-04, UX-NEW-05 (pipeline Kanban)
4. **Acessibilidade:** A11Y-03, A11Y-06, A11Y-08 (quick WCAG improvements)
5. **Code hygiene:** FE-13, FE-15, IC-02, IC-04
6. **Advanced testing:** SYS-16 (integration tests)
7. **Polish:** IC-01, IC-03, IC-05, IC-07, MF-03, MF-04

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** STORY-TD-001 a TD-018 (parciais -- alguns items dependem de infra criada nos sprints anteriores)
- UX-NEW-03 depende de TD-005 (Dialog primitive)
- SYS-01 depende de TD-013 e TD-015 (coverage)

## Riscos
- Backlog pode crescer se novas features introduzirem novos debitos.
- Items podem se tornar irrelevantes se funcionalidade mudar.
- Sem prazo fixo, items podem ser indefinidamente adiados.

## Rollback Plan
- Nao aplicavel -- cada item e tratado independentemente com seu proprio PR.

## Definition of Done (por item individual)
- [ ] Codigo implementado e revisado
- [ ] Testes passando
- [ ] CI/CD green
- [ ] Documentacao atualizada se aplicavel
- [ ] Deploy verificado
