# Reativação 2 trials expirados — enviados via Resend

**Status: ENVIADOS** em 2026-04-26 (sessão enchanted-allen).

| Para | Resend ID | From | Reply-To |
|------|-----------|------|----------|
| paulo.souza@adeque-t.com.br | `92e691a0-76e8-4b7d-9d72-d2e1d4225b8a` | Tiago Sasaki <tiago@smartlic.tech> | tiago.sasaki@gmail.com |
| dslicitacoesthe@gmail.com | `36dbfada-b85e-4679-901f-1130a48da9f4` | Tiago Sasaki <tiago@smartlic.tech> | tiago.sasaki@gmail.com |

**Tracking delivery:** check Resend dashboard `https://resend.com/emails/{id}` ou query `trial_email_log` se webhook gravou.

Tom humano, sem template visual. CTA único: responder o email. Respostas caem em `tiago.sasaki@gmail.com`.

---

## Email 1 — paulo.souza@adeque-t.com.br

**Contexto:** PAULO EMILIO CUNHA SOUZA. Empresa adeque-t (engenharia elétrica). Buscou 1 vez (10/abr) em SP setor engenharia: **282 licitações de R$1.27 BILHÕES**. Não voltou. Trial expirou 24/abr (-3d).

**Hipótese de fricção:** achou volume demais, não soube priorizar, ou faltou follow-up consultivo.

```
Para: paulo.souza@adeque-t.com.br
Assunto: Vi que você encontrou R$1.27B em licitações de engenharia em SP

Paulo, tudo bem?

Sou o Tiago, fundador do SmartLic.

Vi que sua única busca em abril retornou 282 licitações de
engenharia em SP — R$1.27 bilhões. Imagino que você não
voltou porque o volume veio muito grande pra digerir sozinho.

Se quiser, te dou mais 14 dias de trial e sento 30min com
você no Meet pra te ajudar a:
- Filtrar as 282 pra 10 com chance real (NR10, SPDA, projetos
  elétricos — vi suas keywords)
- Configurar alerta diário só do que importa
- Mostrar como calcular margem por edital

Sem custo, sem cartão. Só responde esse email com 2-3 horários
que funcionam pra você.

Abraço,
Tiago
```

**Justificativa do draft:**
- Quote número específico (R$1.27B) → mostra que olhei o uso real, não é template
- Reconhece a fricção provável (volume não-digerível)
- Oferece valor concreto: extensão + sessão consultiva 30min
- CTA mínimo: responder com horários
- Sem link, sem cupom, sem pressão temporal
- Assina pessoal (fundador), não empresa

---

## Email 2 — dslicitacoesthe@gmail.com

**Contexto:** "ds licitações" — provavelmente assessoria de licitação. Buscou ativamente até 20/abr (12 dias após signup). Setor informática, UFs Nordeste (9 estados). Última busca achou só 1 licitação de R$2.290 em Teresina-PI. Penúltima achou 47 (R$1.13M). Trial expirou 22/abr (-5d).

**Hipótese de fricção:** assessor de licitação testando. Pode ter avaliado que volume nordeste informática não justifica plano R$397/mês, ou ficou esperando resultados maiores.

```
Para: dslicitacoesthe@gmail.com
Assunto: Você buscou informática NE 4 vezes — vi onde tá o problema

Olá,

Sou o Tiago, fundador do SmartLic.

Você usou o trial bem (4 buscas em 12 dias, parabéns), mas vi
que a última busca em PI só achou 1 licitação de R$2.290.
Imagino que ficou frustrante.

A questão é que sua janela de busca foi só 10 dias e suas
keywords ficaram amplas demais ("informatica" geral). Quando
filtramos por:
- 30 dias retroativos
- Sub-categorias específicas (servidores, switches, manutenção)
- Modalidade Pregão Eletrônico

Os mesmos 9 estados retornam tipicamente 80-150 oportunidades
por mês.

Se você é assessoria/consultoria, posso te dar 14 dias extras
de trial + 20min no Meet pra te mostrar a configuração que
extrai isso. Sem cartão, sem compromisso.

Responde esse email com 2-3 horários. Só isso.

Abraço,
Tiago
```

**Justificativa do draft:**
- Acknowledge esforço real (4 buscas em 12 dias)
- Diagnóstico técnico específico (janela 10d + keyword genérica) — mostra produto-fit
- Promessa quantificada (80-150 oportunidades/mês, ranged)
- Identifica audience como assessoria → assessoria revende valor → upsell potencial maior
- Oferta valor concreto + extensão
- CTA mínimo

---

## Próximos passos pós-envio (você)

1. Envie os 2 emails **hoje** ou amanhã cedo (terça/quarta = melhores open rates B2B BR).
2. Se responderem, cale a venda. Foque em ENTENDER por que pararam (1 minuto perguntando, 2 minutos ouvindo). Anote em qualquer texto:
   - Por que parou de usar?
   - Qual decisão final foi tomada (avaliando outro produto / desistiu / resolveu de outra forma)?
   - O que precisaria pra reconsiderar?
3. **Decisão de extensão de trial via Supabase:** se quiser ativar 14 dias extras imediatamente após resposta deles, posso te dar comando SQL.
4. Documenta resposta (mesmo que seja "não responder") em `docs/leads/` para consolidar aprendizado.

## Não-óbvios

- **welcome_email_sent_at = null em ambos.** Lifecycle email completo nunca disparou. Engineering bug, mas não vale fixar agora — sequência de 6 emails (story310/321) só faz sentido com volume.
- **trial_conversion_emails_enabled = true em ambos** — opted-in. Você pode mandar do Resend transacional sem problema legal/spam.
- **dslicitacoesthe** assinou via Google OAuth (avatar Google). Pode ter outra conta principal de trabalho — primeiro contato pode chegar em caixa de spam pessoal.
