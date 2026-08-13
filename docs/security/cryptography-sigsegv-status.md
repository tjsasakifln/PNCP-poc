# Cryptography SIGSEGV — Status de Monitoramento

**Débito:** DEBT-SYS-002 (DEBT-206)
**Severidade:** Crítica — SIGSEGV intermitente com C extensions em Gunicorn `--preload`
**Status atual:** PIN MOVIDO PARA 50.x — 47+ publicado; 46.0.7 tinha PYSEC-2026-3552/3553/3554 (CRITICAL). Runner de produção é uvicorn (CRIT-084), não gunicorn prefork. `--preload` continua proibido.
**Última revisão:** 2026-08-13 (pip-audit no PR #2119)
**Próxima revisão:** 2026-11-13 (Q4 2026)

---

## Problema

O SmartLic usa `cryptography` pinada em `<47.0` (`requirements.txt`) devido a SIGSEGV
intermitente ao carregar extensões C com uvloop. O SIGSEGV ocorre em alguns ambientes
durante inicialização do worker quando `cryptography >= 47.0` está instalada.

**Ticket de referência:** CRIT-SIGSEGV (interno)
**Upstream issue:** cryptography#<TBD> — aguardando fix em 47.x (versão 47.x ainda não publicada no PyPI)

---

## Versão Atual Pinada

```
cryptography>=50.0.0,<51.0.0       # PYSEC-2026-3552/3553/3554 + GHSA-537c-gmf6-5ccf
```

**Piso 50.0.0:** PYSEC-2026-3552 (CVE-2026-69247 / GHSA-g6cj-pr64-35w5, Bleichenbacher em PKCS#7) só fecha em 50.0.0. PYSEC-2026-3553/3554 fecham em 49.0.0; GHSA-537c-gmf6-5ccf fecha em 48.0.1.

---

## Histórico de Testes

| Data | Versão Testada | Resultado | Testador | Notas |
|------|---------------|-----------|---------|-------|
| 2026-03-30 | 46.0.6 | STABLE — PASS | @devops | Load test 100 req, 0 erros, 1066 req/s |
| 2026-03-30 | 47.x | NAO EXISTE | — | 47.x ainda não foi publicado no PyPI |

---

## CVEs Ativos na Faixa 46.x

> Auditoria executada em 2026-03-30 via `pip-audit -r backend/requirements.txt`
> Próxima auditoria: 2026-06-30 (Q3 2026)

| CVE | Pacote | Severidade | Versão afetada | Status |
|-----|--------|-----------|----------------|--------|
| — | cryptography | — | 46.0.6 | ZERO CVEs — PIN MANTIVEL |
| CVE-2026-32597 | pyjwt | MEDIUM | <2.12.0 | CORRIGIDO: upgrade para >=2.12.0 em requirements.txt |

### Resultado da Auditoria 2026-03-30

```
pip-audit -r backend/requirements.txt
  cryptography 46.0.6 — 0 vulnerabilidades
  pyjwt 2.11.0 — CVE-2026-32597 (crit header bypass)
  Total: 1 CVE encontrado (nao em cryptography)
```

**Ação tomada:** PyJWT atualizado para `>=2.12.0,<3.0.0` (fix disponível, zero risco de regressão).
**cryptography:** NENHUM CVE encontrado. Pin mantido como medida de estabilidade contra SIGSEGV.

---

## Load Test Results — 2026-03-30

```
Versão:     cryptography 46.0.6
Requests:   100/100 OK (0 erros)
Workers:    4 paralelos
Elapsed:    0.09s
Throughput: 1066.7 req/s
Resultado:  PASS
```

Operações testadas: AES-GCM (encrypt/decrypt), HMAC-SHA256, EC key gen + sign/verify, SHA-256 hash.

---

## Procedimento de Upgrade para 47.x

Quando `cryptography >= 47.0` for publicado no PyPI:

1. Criar branch `fix/cryptography-upgrade`
2. Atualizar `requirements.txt`: mudar `<47.0.0` para `<48.0.0` (ou remover upper bound)
3. Criar venv isolado: `python -m venv /tmp/venv-crypto47 && pip install cryptography>=47.0`
4. Load test no venv isolado:
   ```bash
   /tmp/venv-crypto47/bin/python scripts/security/test_cryptography_load.py --requests 100
   ```
5. Testar com gunicorn (fork-safety crítico):
   ```bash
   gunicorn main:app -k uvicorn.workers.UvicornWorker -w 2 --preload --timeout 30
   # Monitorar: grep -i "sigsegv\|segfault\|crash" nos logs
   ```
6. Deploy em staging (Railway preview branch)
7. Monitorar por 24h: `railway logs --tail | grep -i "sigsegv\|segfault"`
8. Se stable: abrir PR, remover pin, remover workarounds de uvloop

---

## Impacto de NAO Fazer Upgrade

- Exposição a CVEs futuros não corrigidos em 46.x (atualmente nenhum)
- Impossibilidade de atualizar libs que exijam cryptography >=47.0
- Acumulação de débito técnico de segurança

---

## Referências

- [cryptography changelog](https://cryptography.io/en/latest/changelog/)
- [pyup.io safety DB](https://pyup.io/safety/)
- `scripts/security/check_cryptography_cves.py` — auditoria CVE automatizada
- `scripts/security/test_cryptography_load.py` — load test de estabilidade
- `docs/security/quarterly-checklist.md` — procedimento de revisão trimestral
