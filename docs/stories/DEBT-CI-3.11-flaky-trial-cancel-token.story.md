# DEBT-CI-3.11-flaky: test_invalid_signature_rejected é flaky

**Sprint:** 2026-Q2
**Effort:** 1-2h
**Priority:** HIGH (bloqueia todos os PRs não-docs-only)
**Agent:** @dev (Dex)
**Status:** Ready
**Owner:** @dev

## Context

`backend/tests/test_cancel_trial_token.py::TestCreateAndVerifyToken::test_invalid_signature_rejected` falha intermitentemente em Python 3.11 CI (mas passa em 3.12). Observado em PRs #447, #452, #453, #455 — todos com diffs totalmente não relacionados ao trial cancel token.

Diagnóstico empírico (sessão prancy-pudding 2026-04-21):

**Root cause matemático:**
- HMAC-SHA256 signature = 32 bytes = 256 bits
- Base64URL encoding usa 6 bits/char → 43 chars × 6 bits = 258 bits (2 bits padding no fim)
- O **último char** da signature usa apenas 4 dos 6 bits efetivamente
- Chars do alfabeto base64url que compartilham os mesmos 4 top-bits decodificam para bytes **idênticos** após padding strip

O teste faz:
```python
tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
```

Quando `token[-1]` ∈ {grupo de 4 chars decode-equivalentes a "A"}, o "flip" produz uma signature com **os mesmos bytes decodificados** → verificação passa → `DID NOT RAISE TrialCancelTokenError` → teste falha.

**Frequência:** ~6.25% (4 chars do alfabeto base64url ~ 64 chars).

Por que 3.12 "passa" consistentemente: provavelmente ordem de testes ou determinismo JWT diferente → token gerado tem último char fora do grupo ambíguo.

## Scope

Corrigir o teste para ser **determinístico**.

## Acceptance Criteria

- [ ] AC1: Teste `test_invalid_signature_rejected` passa 100/100 runs consecutivos em **ambos** Python 3.11 e 3.12
- [ ] AC2: Abordagem escolhida: **flip múltiplos chars** (ex: últimos 5) OU **re-assinar payload com secret errado** — não só 1 char no final
- [ ] AC3: Teste continua cobrindo o cenário "signature tampered → rejection" (não remover teste)
- [ ] AC4: Zero novo ruído em CI (teste passa em ambos matrix entries)

## Proposed Fix

```python
def test_invalid_signature_rejected(self):
    token = create_cancel_trial_token(USER_ID)
    header, payload, signature = token.split(".")
    # Deterministic tamper: completely replace signature with zeros
    # (always invalid because zero signature decodes to zero bytes, which
    # cannot possibly match HMAC-SHA256(secret, "header.payload"))
    tampered = f"{header}.{payload}.{'A' * len(signature)}"

    with pytest.raises(TrialCancelTokenError) as exc:
        verify_cancel_trial_token(tampered)
    assert exc.value.reason == "invalid_signature"
```

Ou alternativa mais robusta:
```python
# Re-sign with a different secret - ALWAYS produces different signature
import jwt as pyjwt
payload_bytes = token.split(".")[1]
header_bytes = token.split(".")[0]
tampered_sig = pyjwt.encode({"test": "test"}, "wrong-secret", algorithm="HS256").split(".")[2]
tampered = f"{header_bytes}.{payload_bytes}.{tampered_sig}"
```

## Dependencies

- **Blocks:** Qualquer PR não-docs-only para ter CI 100% verde (objetivo de baseline zero desta sessão)
- **Unblocks:** PRs #452, #453, #455 passam CI limpo (apenas Lighthouse + storybook como pre-existing)

## Tests Required

- [ ] Test: `pytest backend/tests/test_cancel_trial_token.py -v --count=20` (10 times each Python version)
- [ ] Test: CI matrix 3.11 + 3.12 verde consecutivos em 3 PRs distintos

## Definition of Done

- [ ] Todos os ACs marcados
- [ ] PR mergeado em main
- [ ] CI matrix 3.11 "Backend Tests (3.11)" passa consecutivamente em main por 7+ runs

## Change Log

| Data | Autor | Evento |
|------|-------|--------|
| 2026-04-21 | @sm | Story created (Draft → Ready, user-approved) |
