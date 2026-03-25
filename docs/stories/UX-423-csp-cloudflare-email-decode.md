# UX-423 — CSP Bloqueia Cloudflare Email Decode na Página de Planos

**Status:** Done
**Severity:** MEDIUM
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Console error na página /planos: "Loading the script 'cloudflare-static/email-decode.min.js' violates Content Security Policy directive: script-src". O email exibido na página (contato@smartlic.tech) não existe — precisa ser corrigido ou removido.

## Acceptance Criteria

- [x] AC1: Adicionar domínio Cloudflare ao CSP script-src OU desabilitar email obfuscation no Cloudflare dashboard
- [x] AC2: Zero erros CSP no console da página /planos
- [x] AC3: Substituir email inexistente contato@smartlic.tech por email válido (ex: tiago.sasaki@confenge.com.br) ou remover link mailto
- [x] AC4: Se email for mantido, configurar caixa de entrada no domínio smartlic.tech
