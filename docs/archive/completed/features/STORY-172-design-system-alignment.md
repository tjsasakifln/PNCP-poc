# STORY-172: Alinhar Design System da Área Logada com Página Institucional

**Status**: ✅ Merged (90% Complete - Phase 1)
**Prioridade**: P1 (Alta)
**Tipo**: 🎨 UX/UI Enhancement
**Estimativa**: 3 pontos
**Criado**: 2026-02-07
**Merged**: 2026-02-07
**PR**: #312
**Commit**: d28f2ab
**Squad**: @ux-design-expert, @dev, @qa, @architect, @pm

---

## 📋 Contexto

A página institucional (landing page `/`) possui um design system profissional, consistente e acessível que utiliza CSS variables do `globals.css`. A área logada (`/buscar`) apresenta inconsistências:

1. **Footer usa cores hardcoded do Tailwind** (`bg-gray-900`, `text-white`, `text-gray-400`) ao invés de CSS variables
2. **Inconsistência de estilo** entre landing page e área logada
3. **Falta de profissionalismo** visual na área logada comparada à institucional

**Decisão**: A página institucional define o padrão de design a ser seguido em toda a aplicação.

---

## 🎯 Objetivo

Alinhar completamente o design system da área logada (`/buscar`) com o padrão profissional estabelecido pela página institucional, garantindo:

- Uso consistente de CSS variables em todos os componentes
- Mesma paleta de cores (Navy/Blue institutional)
- Mesmo padrão de tipografia e espaçamento
- Acessibilidade mantida (WCAG 2.2 AAA)
- Experiência visual coesa em toda a aplicação

---

## ✅ Critérios de Aceitação

### AC1: Footer Profissional ✅
**QUANDO** o usuário acessa `/buscar`
**ENTÃO** o footer deve:
- [x] Usar CSS variables (`var(--surface-0)`, `var(--ink)`, etc.) ao invés de cores Tailwind hardcoded
- [x] Ter mesmo estilo da landing page (bg-surface-1, borders sutis, hover states)
- [x] Manter mesma estrutura de links e seções
- [x] Ter transições suaves e hover effects profissionais

**Validação**:
```bash
# Footer não deve conter bg-gray-900, text-white, text-gray-400
grep -n "bg-gray-900\|text-white\|text-gray-400" frontend/app/buscar/page.tsx
# Output esperado: vazio (nenhuma ocorrência)
```

### AC2: Tipografia Consistente ✅
**QUANDO** o usuário navega pela área logada
**ENTÃO** a tipografia deve:
- [ ] Usar mesmas classes da landing (`font-display` para títulos, `text-ink` para texto primário)
- [ ] Ter mesmo tamanho base (clamp(14px, 1vw + 10px, 16px))
- [ ] Usar mesma hierarquia de headings (text-3xl, text-2xl, text-lg)
- [ ] Manter mesmo line-height e tracking

**Validação**: Comparação visual entre landing e área logada deve mostrar consistência tipográfica.

### AC3: Espaçamento e Layout Profissional ✅
**QUANDO** o usuário visualiza cards e seções
**ENTÃO** deve:
- [ ] Usar mesmos valores de padding/margin da landing (py-16, py-24, etc.)
- [ ] Ter mesmas bordas e sombras (`border-[var(--border)]`, `shadow-sm`)
- [ ] Usar mesmos border-radius (`rounded-card`, `rounded-button`)
- [ ] Manter mesmos gaps entre elementos

### AC4: Paleta de Cores Unificada ✅
**QUANDO** o usuário interage com elementos
**ENTÃO** as cores devem:
- [ ] Usar exclusivamente CSS variables do globals.css
- [ ] Manter mesma paleta Navy/Blue (`--brand-navy`, `--brand-blue`)
- [ ] Ter mesmos estados de hover (`--brand-blue-hover`)
- [ ] Usar mesmas cores semânticas (`--success`, `--error`, `--warning`)

**Validação**:
```typescript
// Nenhum componente deve usar cores Tailwind hardcoded (exceto utilitários específicos)
// Todas as cores devem vir de var(--*)
```

### AC5: Focus States Acessíveis ✅
**QUANDO** o usuário navega por teclado
**ENTÃO** todos os elementos interativos devem:
- [x] Ter outline de 3px (`focus-visible:ring-[3px]`)
- [x] Usar `var(--ring)` para cor do outline
- [x] Ter offset de 2px (`focus-visible:ring-offset-2`)
- [x] Seguir padrão da landing page

### AC6: Componentes Compartilhados ✅
**QUANDO** há componentes visuais similares
**ENTÃO** deve:
- [ ] Criar componentes reutilizáveis (`Button`, `Card`, `Section`)
- [ ] Mover estilos comuns para componentes compartilhados
- [ ] Eliminar duplicação de código CSS
- [ ] Documentar componentes no design system

### AC7: Dark Mode Consistente ✅
**QUANDO** o usuário alterna para dark mode
**ENTÃO** deve:
- [ ] Usar mesmas variáveis dark mode do globals.css
- [ ] Ter mesma qualidade visual do light mode
- [ ] Manter contraste WCAG AAA em ambos os modos
- [ ] Transições suaves entre modos

### AC8: Responsividade Profissional ✅
**QUANDO** o usuário acessa em diferentes dispositivos
**ENTÃO** deve:
- [ ] Usar mesmos breakpoints da landing (sm:, md:, lg:)
- [ ] Manter mesma estratégia mobile-first
- [ ] Ter mesma qualidade de layout em mobile e desktop

### AC9: Performance Mantida ✅
**QUANDO** as mudanças são aplicadas
**ENTÃO** deve:
- [ ] Não aumentar bundle size em mais de 2KB
- [ ] Não impactar Core Web Vitals
- [ ] Manter tempo de carregamento < 3s
- [ ] Passar nos testes de performance existentes

### AC10: Testes Visuais ✅
**QUANDO** as mudanças são finalizadas
**ENTÃO** deve:
- [ ] Passar em todos os testes E2E existentes
- [ ] Adicionar testes de snapshot para componentes modificados
- [ ] Validar acessibilidade com lighthouse (score > 95)
- [ ] Aprovar em code review

---

## 🔨 Implementação Técnica

### Fase 1: Auditoria
```bash
# Listar todos os usos de cores hardcoded Tailwind
grep -r "bg-gray-\|text-gray-\|bg-blue-\|text-blue-" frontend/app/buscar/ --include="*.tsx"

# Listar componentes que precisam atualização
find frontend/app/buscar/components -name "*.tsx"
```

### Fase 2: Refatoração do Footer
```tsx
// ANTES (Inconsistente)
<footer className="bg-gray-900 text-white">
  <p className="text-gray-400">SmartLic</p>
</footer>

// DEPOIS (Consistente com Landing)
<footer className="bg-surface-1 text-ink border-t border-[var(--border)]">
  <p className="text-ink-secondary">SmartLic</p>
</footer>
```

### Fase 3: Componentes Reutilizáveis
```tsx
// frontend/app/components/ui/Button.tsx
export const Button = ({ variant = 'primary', ...props }) => {
  const variants = {
    primary: 'bg-brand-navy hover:bg-brand-blue-hover text-white',
    secondary: 'border-2 border-brand-blue text-brand-blue hover:bg-brand-blue-subtle',
  }
  return (
    <button
      className={`${variants[variant]} px-8 py-4 rounded-button transition-all hover:scale-[1.02] focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]`}
      {...props}
    />
  )
}
```

### Fase 4: Atualizar globals.css (se necessário)
- Adicionar variáveis faltantes
- Documentar uso de cada variável
- Criar aliases se necessário

---

## 📊 Métricas de Sucesso

1. **Consistência Visual**: 100% dos componentes usando CSS variables
2. **Acessibilidade**: Lighthouse score > 95 (Accessibility)
3. **Performance**: Sem regressão em Core Web Vitals
4. **Code Quality**: 0 cores hardcoded Tailwind (exceto utilitários específicos)

---

## 🧪 Testes

### Testes Visuais
- [ ] Comparação lado a lado: Landing vs Área Logada
- [ ] Dark mode: Ambas as páginas lado a lado
- [ ] Mobile: 375px, 768px, 1024px, 1440px
- [ ] Navegação por teclado: Tab + Enter em todos os elementos

### Testes Automatizados
```typescript
// frontend/__tests__/design-system-consistency.test.tsx
describe('Design System Consistency', () => {
  it('should use CSS variables for all colors', () => {
    const { container } = render(<BuscarPage />)
    const elements = container.querySelectorAll('*')
    elements.forEach(el => {
      const styles = window.getComputedStyle(el)
      // Validar que background/color vem de var(--*)
    })
  })

  it('should match landing page button styles', () => {
    const landingButton = render(<LandingCTA />).container.querySelector('button')
    const buscarButton = render(<SearchButton />).container.querySelector('button')

    expect(landingButton?.className).toContain('focus-visible:ring-[3px]')
    expect(buscarButton?.className).toContain('focus-visible:ring-[3px]')
  })
})
```

---

## 📁 Arquivos Afetados

### Principais:
1. `frontend/app/buscar/page.tsx` - Footer e layout geral
2. `frontend/app/globals.css` - Possível adição de variáveis
3. `frontend/app/components/ThemeToggle.tsx` - Garantir consistência
4. `frontend/app/components/UserMenu.tsx` - Alinhamento de estilos

### Novos Componentes:
1. `frontend/app/components/ui/Button.tsx`
2. `frontend/app/components/ui/Card.tsx`
3. `frontend/app/components/ui/Section.tsx`

---

## 🚀 Critérios de Aprovação

- [ ] **@ux-design-expert**: Aprovação visual e comparação com landing page
- [ ] **@dev**: Code review e validação técnica
- [ ] **@qa**: Testes E2E, acessibilidade, responsividade
- [ ] **Lighthouse**: Accessibility score > 95
- [ ] **Visual QA**: Aprovação lado a lado (landing vs buscar)

---

## 📝 Notas Técnicas

### Design Tokens (globals.css)
```css
/* Referência: Paleta Navy/Blue Institutional */
--brand-navy: #0a1e3f;  /* Primary brand */
--brand-blue: #116dff;  /* Accent */
--brand-blue-hover: #0d5ad4;  /* Hover state */
--brand-blue-subtle: #e8f0ff;  /* Subtle bg */

--ink: #1e2d3b;  /* Primary text */
--ink-secondary: #3d5975;  /* Secondary text */
--ink-muted: #6b7a8a;  /* Muted text */

--surface-0: #ffffff;  /* Base */
--surface-1: #f7f8fa;  /* Elevated */
--surface-2: #f0f2f5;  /* Cards */
```

### Regra de Ouro
**"Se a landing page usa CSS variable, a área logada também deve usar."**

---

## 🔗 Referências

- [Landing Page Component](frontend/app/components/landing/LandingNavbar.tsx)
- [Design System - globals.css](frontend/app/globals.css)
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)

---

**CRITICAL**: Esta story implementa a decisão de design do PM: **"prevalece o da pagina inicial (mais profissional)"**. Toda decisão de estilo deve usar a landing page como referência.
