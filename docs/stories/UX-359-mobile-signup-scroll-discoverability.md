# UX-359 — Tela de Cadastro Mobile Esconde Formulario Abaixo do Fold

**Status:** Done
**Priority:** P1 — Critical (bloqueio de conversao)
**Severity:** UX — formulario invisivel no primeiro carregamento mobile
**Created:** 2026-02-24
**Sprint:** Next
**Relates to:** STORY-258 (Account Uniqueness Verification), UX-358 (Mobile Menu)

---

## Problema

Na tela de cadastro (`/signup`) no mobile, o formulario e **invisivel no primeiro carregamento**:

1. **InstitutionalSidebar ocupa 100vh** — O componente `InstitutionalSidebar` usa `min-h-screen` no mobile (InstitutionalSidebar.tsx:180), forçando o sidebar a ocupar a tela inteira. O formulario de cadastro fica **inteiramente abaixo do fold**.

2. **Nenhuma indicacao visual de scroll** — Nao existe:
   - Gradiente fade na parte inferior indicando mais conteudo
   - Seta ou chevron apontando para baixo
   - Texto "Role para baixo" ou equivalente
   - Scroll snap para guiar o usuario ao formulario
   - Bounce animation ou indicador pulsante

3. **Usuario pensa que a pagina esta quebrada** — Ao acessar `/signup` no mobile, o usuario ve apenas o sidebar institucional (headline + beneficios + stats) e nao percebe que precisa rolar para encontrar o formulario. Muitos abandonam achando que a pagina nao carregou.

4. **Conteudo do formulario e extenso** — O formulario tem ~750-850px de altura (nome + email com validacao + telefone + senha com policy hints + botoes), tornando impossivel ver tudo sem scroll significativo.

### Impacto

- **Drop-off direto na etapa mais critica do funnel** — usuario que clicou "Cadastrar" e redirecionado para uma pagina que aparenta nao ter formulario
- Tela de login tem o mesmo problema (menos critico pois tem menos campos)
- Problema invisivel em analytics — aparece como "bounce" mas causa real e UX

### Causa Raiz

```
Viewport mobile (ex: iPhone 13 — 390x844):
┌─────────────────────────────┐
│   InstitutionalSidebar      │ ← min-h-screen (844px)
│   "Inteligencia em          │
│    Licitacoes Publicas"     │
│   - beneficio 1             │
│   - beneficio 2             │
│   - beneficio 3             │
│   stats: 15 setores, etc    │
│                             │
│                             │
│                             │
└─────────────────────────────┘ ← FOLD (usuario ve ate aqui)
┌─────────────────────────────┐
│   FORMULARIO DE CADASTRO    │ ← INVISIVEL sem scroll
│   Nome, Email, Telefone,    │
│   Senha, Submit             │
│                             │
└─────────────────────────────┘
```

Arquivos envolvidos:
- `frontend/app/components/InstitutionalSidebar.tsx:180` — `min-h-screen` no mobile
- `frontend/app/signup/page.tsx:309-314` — layout `flex flex-col md:flex-row`

---

## Acceptance Criteria

### AC1 — Sidebar com altura reduzida no mobile
- [x] No mobile (<768px), `InstitutionalSidebar` usa `min-h-[50vh]` em vez de `min-h-screen`
- [x] Isso garante que ~50% do formulario ja esteja visivel no primeiro carregamento
- [x] No desktop (md+), layout side-by-side mantem-se identico ao atual
- [x] Conteudo do sidebar (headline, beneficios, stats) continua visivel e legivel

### AC2 — Indicador visual de scroll
- [x] Adicionar **chevron animado** na parte inferior do sidebar (mobile only) indicando "tem mais conteudo abaixo"
- [x] Chevron usa animação sutil de bounce (CSS keyframe, nao Framer Motion — leve)
- [x] Chevron desaparece automaticamente apos o usuario rolar >50px
- [x] Cor do chevron: `text-white/60` (contraste com o fundo escuro do sidebar)

### AC3 — Auto-scroll para o formulario
- [x] Adicionar `scroll-mt-4` no container do formulario para compensar padding
- [x] Chevron ao ser clicado faz smooth scroll ate o formulario
- [x] Se usuario chegar via CTA ("Comece Gratis" da landing), auto-scroll para o formulario com delay de 300ms
- [x] Parametro `?scroll=form` na URL ativa o auto-scroll (para links diretos)

### AC4 — Layout responsivo otimizado
- [x] Padding do sidebar no mobile reduzido de `p-6` para `p-4 py-6` (menos espaco desperdicado)
- [x] Stats row no sidebar usa `flex-wrap` para nao quebrar layout em telas estreitas
- [x] Formulario container muda de `py-8` para `py-4` no mobile (menos padding vertical)
- [x] Total de scroll necessario reduzido em pelo menos 40% comparado ao estado atual

### AC5 — Tela de login com mesma correcao
- [x] Aplicar AC1 e AC2 tambem na tela de login (`/login`)
- [x] Login tem menos campos, entao formulario deve ficar quase 100% visivel no primeiro load

### AC6 — Testes
- [x] Adicionar teste: sidebar height no mobile e `50vh`, nao `100vh`
- [x] Adicionar teste: chevron scroll indicator renderiza no mobile
- [x] Adicionar teste: chevron desaparece apos scroll
- [x] Adicionar teste: `?scroll=form` ativa auto-scroll
- [x] Adicionar teste: layout nao regride no desktop (side-by-side mantido)
- [x] Testes existentes do signup e login continuam passando (0 failures)

---

## Solucao Tecnica Proposta

### 1. InstitutionalSidebar — altura responsiva

```tsx
// InstitutionalSidebar.tsx — linha 178-185
<div
  className={`
    min-h-[50vh] md:min-h-0 md:h-auto
    bg-gradient-to-br from-[var(--brand-navy)] to-[var(--brand-blue)]
    flex items-center justify-center
    p-4 py-6 md:p-12 lg:p-16
    relative
    ${className}
  `.trim()}
>
  {/* ... conteudo existente ... */}

  {/* Scroll indicator — mobile only */}
  <div className="absolute bottom-4 left-1/2 -translate-x-1/2 md:hidden animate-bounce-gentle">
    <svg className="w-6 h-6 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  </div>
</div>
```

### 2. Signup page — auto-scroll via URL param

```tsx
// signup/page.tsx — apos o return
const formRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('scroll') === 'form' || params.get('source')?.includes('cta')) {
    setTimeout(() => {
      formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
  }
}, []);
```

### 3. Tailwind animation (nao precisa de Framer Motion)

```css
/* globals.css */
@keyframes bounce-gentle {
  0%, 100% { transform: translateY(0) translateX(-50%); }
  50% { transform: translateY(6px) translateX(-50%); }
}
.animate-bounce-gentle {
  animation: bounce-gentle 2s ease-in-out infinite;
}
```

---

## Arquivos a Modificar

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/components/InstitutionalSidebar.tsx` | `min-h-[50vh]`, padding mobile, scroll indicator |
| `frontend/app/signup/page.tsx` | Auto-scroll, formRef, padding mobile |
| `frontend/app/login/page.tsx` | Mesmas correcoes de AC1/AC2 |
| `frontend/app/globals.css` | Keyframe `bounce-gentle` |
| `frontend/tailwind.config.ts` | Animation `bounce-gentle` (ou direto no CSS) |
| `frontend/__tests__/` | Novos testes para sidebar height + scroll indicator |

---

## Wireframe Mobile Corrigido

```
Viewport mobile (iPhone 13 — 390x844):
┌─────────────────────────────┐
│   InstitutionalSidebar      │ ← min-h-[50vh] (~422px)
│   "Inteligencia em          │
│    Licitacoes Publicas"     │
│   - beneficio 1             │
│   - beneficio 2             │
│         ↓ (chevron)         │
├─────────────────────────────┤ ← FOLD (~422px)
│   ┌─────────────────────┐   │
│   │  Criar conta         │   │ ← Formulario VISIVEL!
│   │  [Google OAuth]      │   │
│   │  ─── ou ───          │   │
│   │  Nome: [________]    │   │
│   └─────────────────────┘   │
└─────────────────────────────┘
    (scroll para ver resto)
```

---

## Validacao

- [x] Testar em iPhone SE (320px) — formulario parcialmente visivel no load
- [x] Testar em iPhone 13/14 (390px) — pelo menos titulo + Google OAuth visiveis
- [x] Testar em Android (360px) — sidebar nao trunca conteudo
- [x] Clicar chevron > smooth scroll ate formulario
- [x] URL com `?scroll=form` > auto-scroll com 300ms delay
- [x] Login page > sidebar reduzido, formulario mais visivel
- [x] Desktop > nenhuma mudanca visual (side-by-side mantido)

## Definition of Done

- [x] Todos os AC passando
- [x] 0 falhas nos testes existentes + novos testes adicionados
- [x] Testado manualmente em 3 viewports mobile
- [x] Sem regressao no desktop
- [x] Sidebar continua legivel com 50vh
- [x] Code review aprovado
