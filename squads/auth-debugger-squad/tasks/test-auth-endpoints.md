---
task: Testa todos endpoints auth com o mesmo token para identificar inconsistências
responsavel: "@qa-reproducer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - auth_token: auth token
  - endpoint_list: endpoint list
  - test_scenarios: test scenarios
Saida: |
  - test_results: test results
  - inconsistent_endpoints: inconsistent endpoints
  - reproduction_steps: reproduction steps
Checklist:
  - "[ ] Gerar token de teste válido"
  - "[ ] Testar /me endpoint"
  - "[ ] Testar /api/messages/unread-count endpoint"
  - "[ ] Testar outros endpoints protegidos"
  - "[ ] Documentar comportamento inconsistente"
---

# *test-auth-endpoints

Testa todos endpoints auth com o mesmo token para identificar inconsistências

## Usage

```
@qa-reproducer
*test-auth-endpoints
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `auth_token` | string | Yes | auth token |
| `endpoint_list` | string | Yes | endpoint list |
| `test_scenarios` | string | Yes | test scenarios |

## Output

- **test_results**: test results
- **inconsistent_endpoints**: inconsistent endpoints
- **reproduction_steps**: reproduction steps

## Process

1. Gerar token de teste válido
2. Testar /me endpoint
3. Testar /api/messages/unread-count endpoint
4. Testar outros endpoints protegidos
5. Documentar comportamento inconsistente
