---
task: Verifica sincronização entre estado de auth backend e UI frontend
responsavel: "@frontend-inspector"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - frontend_code: frontend code
  - auth_hooks: auth hooks
  - ui_components: ui components
Saida: |
  - sync_issues: sync issues
  - state_management_report: state management report
  - fix_recommendations: fix recommendations
Checklist:
  - "[ ] Inspecionar useAuth ou hooks de autenticação"
  - "[ ] Verificar atualização de UI após login"
  - "[ ] Testar persistência de estado após refresh"
  - "[ ] Identificar race conditions"
---

# *validate-ui-state-sync

Verifica sincronização entre estado de auth backend e UI frontend

## Usage

```
@frontend-inspector
*validate-ui-state-sync
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `frontend_code` | string | Yes | frontend code |
| `auth_hooks` | string | Yes | auth hooks |
| `ui_components` | string | Yes | ui components |

## Output

- **sync_issues**: sync issues
- **state_management_report**: state management report
- **fix_recommendations**: fix recommendations

## Process

1. Inspecionar useAuth ou hooks de autenticação
2. Verificar atualização de UI após login
3. Testar persistência de estado após refresh
4. Identificar race conditions
