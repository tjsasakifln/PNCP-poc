---
task: Analisa o fluxo completo de autenticação da aplicação
responsavel: "@auth-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - application_logs: application logs
  - endpoint_docs: endpoint docs
  - auth_architecture_diagram: auth architecture diagram
Saida: |
  - flow_map: flow map
  - identified_issues: identified issues
  - token_lifecycle_report: token lifecycle report
Checklist:
  - "[ ] Mapear todos endpoints de autenticação"
  - "[ ] Identificar pontos de validação de token"
  - "[ ] Documentar fluxo esperado vs. real"
  - "[ ] Identificar inconsistências"
---

# *analyze-auth-flow

Analisa o fluxo completo de autenticação da aplicação

## Usage

```
@auth-analyst
*analyze-auth-flow
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `application_logs` | string | Yes | application logs |
| `endpoint_docs` | string | Yes | endpoint docs |
| `auth_architecture_diagram` | string | Yes | auth architecture diagram |

## Output

- **flow_map**: flow map
- **identified_issues**: identified issues
- **token_lifecycle_report**: token lifecycle report

## Process

1. Mapear todos endpoints de autenticação
2. Identificar pontos de validação de token
3. Documentar fluxo esperado vs. real
4. Identificar inconsistências
