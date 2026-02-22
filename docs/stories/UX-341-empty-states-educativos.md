# UX-341 — Empty States Educativos (Pipeline, Historico, Dashboard)

**Tipo:** Feature / UX Medio
**Prioridade:** Media (M2 + M3 da auditoria UX 2026-02-22)
**Criada:** 2026-02-22
**Status:** Concluida
**Origem:** Auditoria UX — Persona "Seu Carlos" (gestor PME 60 anos, interior BR)

---

## Problema

Paginas internas sem dados exibem estados vazios genericos ou confusos:

### Pipeline (`/pipeline`)
- Mostra 5 colunas Kanban com "Arraste itens aqui"
- Usuario nao sabe de onde arrastar nem como adicionar itens
- Nenhuma explicacao do que e o pipeline

### Historico (`/historico`)
- Mostra "Nenhuma busca realizada ainda" + link "Fazer primeira busca"
- Funcional, mas sem contexto do valor do historico

### Dashboard (`/dashboard`)
- Ficou em loading infinito (ver UX-338), mas mesmo corrigido precisara de empty state

### Conta (`/conta`)
- Secao "Gerenciar SmartLic Pro" mostra apenas "Cancelar SmartLic Pro"
- Nao mostra: plano atual, valor, data de renovacao, dias restantes do trial

### Evidencias

- Screenshot `ux-audit-08-pipeline.png` — colunas vazias sem orientacao
- Screenshot `ux-audit-09-historico.png` — mensagem minimalista
- Screenshot `ux-audit-11-conta.png` — secao de plano so com botao cancelar

---

## Solucao: Empty States Educativos

### Pipeline Vazio

```
┌────────────────────────────────────────────────────┐
│          📋                                         │
│   Seu Pipeline de Oportunidades                     │
│                                                     │
│   Aqui voce acompanha licitacoes do inicio ao fim: │
│                                                     │
│   1. Busque licitacoes em "Buscar"                  │
│   2. Clique em "Acompanhar" numa oportunidade       │
│   3. Arraste entre as colunas conforme avanca       │
│                                                     │
│   [Buscar oportunidades →]                          │
└────────────────────────────────────────────────────┘
```

### Historico Vazio

```
┌────────────────────────────────────────────────────┐
│          📜                                         │
│   Historico de Buscas                               │
│                                                     │
│   Cada busca que voce faz fica salva aqui.          │
│   Voce pode revisitar resultados anteriores          │
│   sem gastar uma nova analise.                       │
│                                                     │
│   [Fazer primeira busca →]                           │
└────────────────────────────────────────────────────┘
```

### Dashboard Vazio (apos fix do UX-338)

```
┌────────────────────────────────────────────────────┐
│          📊                                         │
│   Seu Painel de Inteligencia                        │
│                                                     │
│   Apos suas primeiras buscas, voce vera aqui:       │
│   • Resumo de oportunidades encontradas             │
│   • Tendencias do seu setor                          │
│   • Valor total de oportunidades analisadas          │
│                                                     │
│   [Fazer primeira busca →]                           │
└────────────────────────────────────────────────────┘
```

### Conta — Secao Plano Melhorada

```
┌──────────────────────────────────────────┐
│  Seu Acesso ao SmartLic                   │
│                                           │
│  Status: Periodo de avaliacao             │
│  Dias restantes: 5 de 7                   │
│  Analises usadas: 1 de 3                  │
│  ████████░░░░░░░░  33%                    │
│                                           │
│  [Assinar SmartLic Pro →]                 │
│                                           │
│  ─────────────────────────                │
│  Cancelar acesso (texto discreto)         │
└──────────────────────────────────────────┘
```

---

## Criterios de Aceitacao

### Pipeline

- [x] AC1: Pipeline vazio exibe empty state educativo com 3 passos
- [x] AC2: CTA "Buscar oportunidades" leva a /buscar
- [x] AC3: Empty state desaparece quando ha >= 1 item no pipeline

### Historico

- [x] AC4: Historico vazio exibe empty state educativo
- [x] AC5: Menciona que revisitar nao gasta analise (se aplicavel)
- [x] AC6: CTA "Fazer primeira busca" leva a /buscar

### Dashboard

- [x] AC7: Dashboard vazio (apos fix UX-338) exibe empty state com preview do que vera
- [x] AC8: CTA "Fazer primeira busca" leva a /buscar

### Conta — Secao Plano

- [x] AC9: Mostrar status do plano (trial / ativo / expirado)
- [x] AC10: Se trial: mostrar dias restantes + analises usadas/total
- [x] AC11: Se assinante: mostrar plano, valor, proxima cobranca
- [x] AC12: CTA primario = "Assinar" (trial) ou "Gerenciar" (assinante)
- [x] AC13: Botao "Cancelar" e secundario/discreto (texto, nao botao vermelho proeminente)

### Nao-Regressao

- [x] AC14: Nenhum teste existente quebra
- [x] AC15: Paginas com dados continuam funcionando normalmente

---

## Arquivos Envolvidos (Estimativa)

### Criar
- `frontend/components/EmptyState.tsx` — componente reutilizavel de empty state

### Modificar
- `frontend/app/pipeline/page.tsx` — adicionar empty state
- `frontend/app/historico/page.tsx` — melhorar empty state existente
- `frontend/app/dashboard/page.tsx` — adicionar empty state (apos UX-338)
- `frontend/app/conta/page.tsx` — redesenhar secao de plano

### Testes
- `frontend/__tests__/empty-states.test.tsx` — novo

---

## Estimativa

- **Complexidade:** Media-Baixa (componentes de UI, sem logica complexa)
- **Risco:** Baixo
- **Depende de:** UX-338 (para dashboard empty state)
