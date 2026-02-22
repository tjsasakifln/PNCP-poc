# CRIT-FLT-001 — EPI Context Gate Excessivamente Restritiva (Falso Negativo)

**Prioridade:** P0 — Falso Negativo Confirmado
**Estimativa:** 2h
**Origem:** Auditoria de Pipeline 2026-02-22
**Track:** Backend

## Problema

A keyword "epi" no setor `vestuario` exige context_required com termos como:
```
["vestuario", "vestimenta", "uniforme", "fardamento", "roupa", "calca", "camisa", "bota", "botina"]
```

Porém, a formulação padrão em licitações públicas é:
> "EPI — Equipamento de Proteção Individual"

O termo "proteção" / "protecao" / "segurança" / "seguranca" **NÃO está na lista de contexto**. Resultado: licitações legítimas de EPIs de vestuário (calçados de segurança, luvas, etc.) são **rejeitadas silenciosamente**.

### Exemplo Real
```
Objeto: "Aquisição de EPI — equipamento de proteção individual para servidores"
Keyword match: "epi" ✓
Context found: NENHUM ✗
Decisão: REJECTED → FALSO NEGATIVO
```

## Acceptance Criteria

- [x] **AC1:** Adicionar `"proteção"`, `"protecao"`, `"segurança"`, `"seguranca"`, `"proteção individual"`, `"protecao individual"`, `"segurança do trabalho"`, `"seguranca do trabalho"` ao context_required de "epi" e "epis" no `sectors_data.yaml` (setor vestuario)
- [x] **AC2:** Verificar se outros setores têm keywords com context gates igualmente restritivos:
  - `informatica`: "servidor" — já tinha "virtualização"/"virtualizacao", adicionado "virtual"
  - `informatica`: "monitor" — já tinha "polegadas", adicionado "polegada" (singular)
  - `informatica`: "switch" — já tinha "porta" e "gbps" ✓ (nenhuma mudança necessária)
- [x] **AC3:** Adicionar testes unitários para cada context gate expandido (16 testes em TestCRITFLT001EpiContextGate)
- [x] **AC4:** Rodar `audit_all_sectors.py` antes e depois da mudança e comparar falsos negativos (400 itens PNCP, vestuario: 23 aprovados)

## Impacto

- **Setor mais afetado:** vestuario (EPIs são ~15% do mercado de uniformes)
- **Risco de regressão:** BAIXO (apenas expande contextos, não remove)
- **Zero LLM cost:** Mudança é puramente determinística

## Arquivos

- `backend/sectors_data.yaml` (context_required para epi/epis)
- `backend/tests/test_filter.py` (novos testes de contexto)
