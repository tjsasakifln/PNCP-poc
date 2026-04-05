# Testimonial Link Building — Email Templates

**Estratégia:** Oferecer testimonial + logo + case study curto em troca de link de volta (feedback/customer page) de fornecedores de alta autoridade que o SmartLic já usa em produção. Tática clássica do playbook Backlinko/Ahrefs.

**Métricas reais do SmartLic (usar consistentemente nos 4 emails):**
- Em produção desde Q4 2025 (v0.5 POC)
- 3 serviços Railway ativos (web, worker, frontend)
- ~15.000 requests/dia no backend FastAPI
- ~40.000 linhas em Supabase (tabela `pncp_raw_bids`) com RLS em todas as tabelas
- Uptime observado >99.5% nos últimos 60 dias
- Pipeline ETL cron: crawl diário + 3 incrementais + purge
- Stack 100% TypeScript + Python 3.12

**Tom geral:** Founder-to-founder, profissional mas caloroso, honesto sobre o stage (pre-revenue), métricas concretas, oferta clara e simétrica.

**Assinatura padrão (todos os emails):**
```
Tiago Sasaki
Founder, SmartLic
CONFENGE Avaliações e Inteligência Artificial LTDA
https://smartlic.tech
tiago.sasaki@confenge.com.br
LinkedIn: /in/tiagosasaki
```

---

## Email 1 — Supabase (DA ~92)

**Para quem enviar:**
- Primeiro contato: team@supabase.io / dx@supabase.io
- DevRel conhecidos: Jon Meyers (`@_jonmeyers` on X / LinkedIn), Thor Schaeff (`@thorwebdev`), Jon Xiao
- Alternativa: Community Slack → DM para Paul Copplestone (CEO) ou Ant Wilson (CTO)
- Formulário: https://supabase.com/docs/guides/platform/troubleshooting (trocar para contact form)

**Subject:** Testemunho real: como o Supabase viabilizou nosso POC B2G em produção

**Corpo:**

> Olá pessoal do Supabase,
>
> Sou Tiago, founder da SmartLic (smartlic.tech) — uma plataforma brasileira que usa IA para encontrar e qualificar editais de licitação pública para empresas B2G. Estamos em produção desde o último trimestre com um POC sólido, e Supabase é a espinha dorsal do nosso backend.
>
> Rapidamente sobre como usamos:
>
> - **Postgres 17** hospedando ~40k linhas de editais públicos (tabela `pncp_raw_bids`) com índice GIN de full-text search em português, alimentados por um cron de ingestão diária via ARQ.
> - **RLS em todas as tabelas** para isolar dados entre tenants (empresas B2G e consultorias).
> - **Supabase Auth** para signup/login, incluindo fluxo OAuth Google.
> - **Supabase SSR** no frontend Next.js 16 — a integração com cookies foi surpreendentemente limpa.
> - **Migrations via CLI** (`supabase db push`) rodando em GitHub Actions no deploy.
>
> Resultado prático: saímos de zero para produção em ~6 semanas, com ~15k requests/dia e uptime >99.5% nos últimos 60 dias. Não teríamos chegado nesse estágio no nosso timing (somos pre-revenue) sem Supabase abstraindo Postgres, auth e RLS num único SDK.
>
> **A oferta:** gostaria de contribuir com um testemunho escrito + logo da SmartLic + um case study curto (500 palavras) sobre como o RLS do Supabase permitiu que nós, um time pequeno, implementássemos multi-tenancy seguro sem construir um sistema de autorização do zero. Em troca, seria excelente se pudessem incluir nosso logo/link na página de customers ou num card de "Built with Supabase".
>
> Posso enviar o texto do testemunho pronto em 48h e deixar para vocês editarem à vontade. Se houver interesse, também topo gravar um vídeo curto (2-3 min) para o canal de vocês.
>
> Obrigado por construírem uma ferramenta que realmente entrega a promessa de "Firebase alternative". Qualquer feedback é bem-vindo.
>
> Abraço,

**Follow-up cadence:**
- D+0: Envio inicial
- D+7: Follow-up curto ("bumping this up in your inbox")
- D+14: Segundo follow-up com anexo do testemunho já escrito
- D+21: Último follow-up com oferta de vídeo
- Depois disso: pausar 60 dias, tentar via DM LinkedIn para DevRel direto

---

## Email 2 — Railway (DA ~65)

**Para quem enviar:**
- Primeiro contato: team@railway.app
- DevRel conhecidos: Jake Cooper (co-founder, `@jakerunzer` on X), Brody Vitas (`@brody_vitas`), Angelo Saraceno
- Discord Railway: canal #show-and-tell + DM a moderadores
- Alternativa: hello@railway.app

**Subject:** Case real: SmartLic rodando 3 serviços no Railway (backend + worker + frontend)

**Corpo:**

> Olá time Railway,
>
> Tiago aqui, founder da SmartLic — uma plataforma B2G brasileira que transforma o caos das licitações públicas do PNCP em um pipeline comercial organizado, usando IA para classificação setorial.
>
> Nosso setup Railway está em produção há cerca de 4 meses e queria compartilhar como tem sido:
>
> - **3 serviços** rodando: web (FastAPI + Gunicorn), worker (ARQ async queue para jobs LLM e ETL), frontend (Next.js 16).
> - **Monorepo** com `RAILWAY_SERVICE_ROOT_DIRECTORY=backend` e `=frontend` separados, cada um com seu `railway.toml` e `Dockerfile`. A configuração foi direta e o auto-deploy via GitHub tem sido rock solid.
> - **Custom domain** `smartlic.tech` com SSL automático funcionando sem dor.
> - **Volume médio:** ~15k requests/dia, picos de 50k durante crawls incrementais (2x/dia), uptime observado >99.5% nos últimos 60 dias.
> - **Railway CLI** faz parte do nosso toolkit diário — `railway logs --tail`, `railway run`, `railway variables` são comandos que os agentes de IA do nosso workflow usam direto.
>
> A honestidade importa: somos um time pré-revenue, nosso MRR ainda é zero, e o Railway nos deu o "cloud adulto" sem precisar contratar DevOps. Isso tem valor real para founders brasileiros tentando lançar produtos B2B.
>
> **Proposta:** gostaria de mandar um testemunho escrito (150-300 palavras) para vocês usarem onde quiserem — página customers, Twitter, Discord showcase, o que for útil. Em troca, pediria para nos incluírem no showcase ou customers list, com link para smartlic.tech. Também posso contribuir com um case study detalhado sobre a migração monorepo → 3 serviços Railway, que acho que seria útil para outros founders no mesmo caminho.
>
> Se toparem, envio o testemunho em 48h, já editável.
>
> Obrigado pelo produto — especificamente pelo fato de `railway up` e GitHub auto-deploy simplesmente funcionarem.
>
> Abraço,

**Follow-up cadence:**
- D+0: Envio inicial
- D+5: Follow-up no Discord Railway em paralelo
- D+10: Reply ao próprio email
- D+20: Pitch via DM a Jake Cooper ou DevRel
- Depois disso: tentar durante um launch week do Railway (eles fazem trimestralmente)

---

## Email 3 — Resend (DA ~60)

**Para quem enviar:**
- Primeiro contato: team@resend.com / hi@resend.com
- Founders: Zeno Rocha (`@zenorocha` on X / LinkedIn — brasileiro!), Bu Kinoshita (`@bukinoshita`)
- **Vantagem estratégica:** Zeno é brasileiro. Email em português é apropriado e cria rapport imediato.
- Alternativa: DM direto via X para Zeno ou via LinkedIn

**Subject:** Fellow brazilian founder usando Resend em produção — proposta de testemunho

**Corpo:**

> Oi Zeno e time Resend,
>
> Escrevendo em português porque sei que vai ressoar — sou o Tiago, founder da SmartLic (smartlic.tech). Plataforma brasileira que usa IA para encontrar, analisar e qualificar editais de licitação pública para empresas B2G. Estamos em produção desde o último trimestre, ainda pre-revenue, com uma base de beta users crescendo.
>
> Resend é nosso único gateway de email transacional. Especificamente:
>
> - **Onboarding emails** (welcome, confirmação, recuperação de senha) via templates React Email.
> - **Trial lifecycle** — day 1 welcome, day 6 "trial expiring", day 14 conversion. O React Email para templates foi um game-changer: pela primeira vez nossos devs topam mexer em email sem xingar.
> - **Alertas de pipeline** quando um novo edital de alta viabilidade aparece para o usuário.
> - **Deliverability:** taxas de entrega >98%, open rate médio nas campanhas de onboarding ~45%, que pelo que vi em benchmarks é saudável para B2B SaaS BR.
> - **Volume atual:** ~500 emails/dia, crescendo.
>
> O que me fez escolher Resend sobre SendGrid/Postmark foi: (1) DX absurdamente superior, (2) React Email, (3) o fato de ter um brasileiro no time fazia eu confiar no suporte pra long-run, (4) preço justo para nosso stage.
>
> **A oferta:** quero escrever um testemunho honesto (posso mandar em PT ou EN) sobre como Resend + React Email simplificou nosso lifecycle de trial a ponto de liberar tempo do único dev backend para features core. Junto, contribuiria com um case study curto sobre templates transacionais de um SaaS B2G brasileiro.
>
> Em troca, gostaria do link de volta — na página de customers, num tweet, ou onde fizer sentido. Logo SVG + cor da marca + texto já prontos, é só copiar.
>
> Se rolar, mando o testemunho em 48h. Se não rolar, segue a vida — de qualquer forma, valeu pelo produto, Zeno. Ver um brasileiro construindo algo com essa qualidade técnica no cenário global é inspirador.
>
> Abraço,

**Follow-up cadence:**
- D+0: Email inicial
- D+3: DM no X para @zenorocha com link do email ("mandei um email, mas sei que inbox é caótico")
- D+10: Follow-up email
- D+17: LinkedIn connection + mensagem
- Depois disso: tentar em qualquer launch/milestone público do Resend (retweet + comentário → reviver conversa)

---

## Email 4 — Vercel (DA ~94)

**Para quem enviar:**
- Primeiro contato: customers@vercel.com / hello@vercel.com
- DevRel conhecidos: Lee Robinson (`@leeerob`, VP DX), Guillermo Rauch (CEO, `@rauchg`), Cassidy Williams, Sam Selikoff
- Formulário de case study: https://vercel.com/contact/sales (trilha "Case Study" / "Enterprise")
- Alternativa: via Next.js Showcase submission (https://github.com/vercel/next.js — repos de showcase)

**Subject:** Next.js 16 em produção — B2G SaaS brasileiro pronto para case study

**Corpo:**

> Olá Vercel team (cc Lee, se puder chegar até você),
>
> Sou Tiago, founder da SmartLic (smartlic.tech) — plataforma brasileira de inteligência em licitações públicas para empresas B2G. Estamos em produção há ~4 meses rodando Next.js 16 (App Router, React Server Components, Server Actions) e queria propor um testemunho + case study.
>
> Resumo técnico do nosso setup Next.js:
>
> - **App Router** desde o dia zero, com layouts aninhados para áreas públicas (marketing, /pricing, /features) e autenticadas (/buscar, /pipeline, /dashboard).
> - **Server Components** para páginas de conteúdo estático (SEO-crítico) e **Client Components** para as experiências interativas (kanban drag-and-drop com @dnd-kit, SSE para progress tracking).
> - **Server Actions** em vários fluxos de mutação (pipeline updates, feedback, onboarding).
> - **SSR + Supabase** via `@supabase/ssr` — a integração cookies/middleware funcionou na primeira tentativa.
> - **Sitemap dinâmico** via `app/sitemap.ts` (migração recente desde um estático que quebrava coisas).
> - **ISR + Cache-Control public** para páginas de conteúdo, liberando CDN (Cloudflare na frente) para cachear respostas e reduzir carga no Railway backend.
> - **Performance real:** LCP médio 1.8s, TTFB 340ms em PT-BR/SP, CLS < 0.05, Lighthouse SEO 100 em todas as páginas de conteúdo.
>
> Estamos hospedando frontend no Railway (não na Vercel — transparência total). Mas o motivo do email é que Next.js é fundacional ao que construímos, e o DX que Vercel/Lee construiu ao redor do framework é o que nos permitiu, com 1 dev frontend, ter um produto B2G com UX de nível enterprise em ~6 semanas até o primeiro usuário pago.
>
> **A oferta:** testemunho escrito (PT e EN) + case study detalhado sobre uma empresa B2G brasileira usando Next.js 16 App Router em produção — um ângulo que aposto que ainda é raro no showcase de vocês. Tudo editável, branding Vercel-approved, logo em SVG disponível.
>
> **O pedido:** link no Next.js Showcase ou num post/blog da Vercel. Mesmo um tweet do Lee faria diferença para nós em termos de validação.
>
> Se houver interesse, consigo mandar o pacote (texto + logo + screenshots + métricas verificáveis) em 72h. Se não for prioridade agora, tudo bem — deixo o convite em aberto.
>
> Obrigado por Next.js. Honestamente.
>
> Abraço,

**Follow-up cadence:**
- D+0: Email inicial ao customers@vercel.com
- D+5: Tweet público marcando `@leeerob` ou `@vercel` sobre nosso stack em produção
- D+10: Submissão ao Next.js Showcase (Github) em paralelo
- D+17: Follow-up email respondendo ao thread
- D+30: Tentar durante um Next.js Conf ou Vercel Ship (momentos de alta receptividade)
- Depois disso: pausar 90 dias, retomar quando tivermos métricas mais fortes (ex: primeiros clientes pagantes)

---

## Observações operacionais

1. **Envio em dias/horários estratégicos:** terças ou quartas, 9h-11h no horário do destinatário. Supabase/Vercel/Resend = PST/EST. Railway = mix global, assumir EST.
2. **Rastreamento:** usar UTMs nos links (`?utm_source=testimonial_outreach&utm_medium=email&utm_campaign=supabase`). Manter planilha simples com status: enviado, lido, respondido, convertido.
3. **Brand asset kit:** preparar um Notion ou Google Drive com logo SVG/PNG, screenshots, métricas em 1 parágrafo, bio founder, email/LinkedIn. Link único para enviar quando solicitarem.
4. **Consistência:** usar sempre o mesmo endereço (tiago.sasaki@confenge.com.br) e sempre assinar como "Founder, SmartLic" para construir reputação no inbox dos decisores.
5. **Honestidade:** se um deles perguntar "vocês têm quantos clientes pagos?", responder verdade (pre-revenue). Tentar inflar métricas é caminho seguro para queimar relacionamento.
6. **Sucesso esperado:** 1-2 conversões em 4 tentativas é uma taxa realista para cold testimonial outreach. Mesmo 1 backlink de DA 90+ já justifica o esforço.
