---
task: Correlaciona logs 200/401 por IP, timestamp e user_id para identificar padrões
responsavel: "@auth-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - production_logs: production logs
  - user_session_id: user session id
  - time_range: time range
Saida: |
  - correlation_report: correlation report
  - request_timeline: request timeline
  - anomaly_patterns: anomaly patterns
Checklist:
  - "[ ] Filtrar logs de auth por IP/session"
  - "[ ] Agrupar requisições por timestamp"
  - "[ ] Identificar sequência 200 OK → 401 Unauthorized"
  - "[ ] Detectar uso de múltiplos tokens"
---

# *correlate-auth-logs

Correlaciona logs 200/401 por IP, timestamp e user_id para identificar padrões

## Usage

```
@auth-analyst
*correlate-auth-logs
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `production_logs` | string | Yes | production logs |
| `user_session_id` | string | Yes | user session id |
| `time_range` | string | Yes | time range |

## Output

- **correlation_report**: correlation report
- **request_timeline**: request timeline
- **anomaly_patterns**: anomaly patterns

## Process

1. Filtrar logs de auth por IP/session
2. Agrupar requisições por timestamp
3. Identificar sequência 200 OK → 401 Unauthorized
4. Detectar uso de múltiplos tokens
