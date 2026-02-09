---
task: Investiga geração, armazenamento e validação de tokens JWT/Supabase
responsavel: "@backend-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - backend_code: backend code
  - auth_middleware: auth middleware
  - supabase_config: supabase config
Saida: |
  - token_flow_diagram: token flow diagram
  - validation_logic: validation logic
  - identified_bugs: identified bugs
Checklist:
  - "[ ] Verificar geração de tokens no login"
  - "[ ] Inspecionar storage de tokens (cookies, localStorage)"
  - "[ ] Analisar middleware de validação"
  - "[ ] Verificar refresh token logic"
---

# *inspect-token-lifecycle

Investiga geração, armazenamento e validação de tokens JWT/Supabase

## Usage

```
@backend-investigator
*inspect-token-lifecycle
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `backend_code` | string | Yes | backend code |
| `auth_middleware` | string | Yes | auth middleware |
| `supabase_config` | string | Yes | supabase config |

## Output

- **token_flow_diagram**: token flow diagram
- **validation_logic**: validation logic
- **identified_bugs**: identified bugs

## Process

1. Verificar geração de tokens no login
2. Inspecionar storage de tokens (cookies, localStorage)
3. Analisar middleware de validação
4. Verificar refresh token logic
