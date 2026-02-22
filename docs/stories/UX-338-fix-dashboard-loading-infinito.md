# UX-338 — Fix Dashboard Loading Infinito (Skeleton Eterno)

**Tipo:** Bug / UX Critico
**Prioridade:** Critica (C1 da auditoria UX 2026-02-22)
**Criada:** 2026-02-22
**Status:** Pendente
**Origem:** Auditoria UX — Persona "Seu Carlos" (gestor PME 60 anos, interior BR)

---

## Problema

A pagina `/dashboard` exibe skeletons de loading indefinidamente. O conteudo nunca renderiza. O DOM mostra apenas `<link>Pular para conteudo principal` + `<alert>` + `<region>Notifications` — nenhum conteudo real do dashboard.

### Evidencias

- Screenshot `ux-audit-07-dashboard.png` — retangulos cinza (skeletons) apos 3s
- Screenshot `ux-audit-07b-dashboard-loaded.png` — mesmos skeletons apos 8s
- Snapshot DOM: `<alert>` vazio, nenhum heading, nenhum dado
- Console: 0 erros, 0 warnings (erro silencioso)

### Impacto

- Dashboard e a 2a pagina que um usuario espera usar apos buscar
- Tela vazia = "o sistema nao funciona"
- Para o Seu Carlos: fecha a aba e nao volta

---

## Investigacao Necessaria

1. Verificar se `/dashboard/page.tsx` faz fetch a alguma API que esta falhando silenciosamente
2. Verificar se existe dependencia de dados que nunca resolve (Promise pendente)
3. Checar se ha condicional de autenticacao que impede render
4. Testar com usuario nao-admin (pode ser especifico do role)

---

## Criterios de Aceitacao

- [ ] AC1: Dashboard carrega e exibe conteudo em ate 3 segundos
- [ ] AC2: Se nao ha dados (usuario novo), exibir empty state educativo:
  - Titulo: "Seu painel de inteligencia"
  - Subtitulo: "Aqui voce vera resumos das suas buscas, tendencias e oportunidades."
  - CTA: "Fazer primeira busca" → /buscar
  - Ilustracao/icone contextual
- [ ] AC3: Se ha dados, exibir metricas reais (buscas realizadas, oportunidades encontradas, etc.)
- [ ] AC4: Se API falha, exibir mensagem de erro com retry:
  - "Nao foi possivel carregar o painel. [Tentar novamente]"
- [ ] AC5: Loading state mostra skeletons por no maximo 10s, apos isso mostra erro/empty state
- [ ] AC6: Console nao mostra erros silenciosos (unhandled promise rejection)

### Nao-Regressao

- [ ] AC7: Nenhum teste existente quebra
- [ ] AC8: Outras paginas nao sao afetadas

---

## Arquivos Envolvidos (Estimativa)

### Investigar
- `frontend/app/dashboard/page.tsx` — pagina principal
- `frontend/app/api/analytics/route.ts` — proxy de analytics (se usado)
- `backend/routes/analytics.py` — endpoints de analytics

### Modificar
- `frontend/app/dashboard/page.tsx` — fix loading + empty state + error handling

### Testes
- `frontend/__tests__/dashboard.test.tsx` — novo ou atualizar

---

## Estimativa

- **Complexidade:** Media (investigacao + fix + empty state)
- **Risco:** Baixo (pagina isolada)
