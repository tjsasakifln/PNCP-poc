# STORY-410: Tema light como padrão e auditoria WCAG do dark mode

**Prioridade:** P1
**Esforço:** M
**Squad:** team-bidiq-frontend

## Contexto
O tema light já é o padrão (`useState<ThemeId>("light")` em `ThemeProvider.tsx:96`), mas há dois problemas: (1) flash de tema incorreto no primeiro render, e (2) os tokens de cor do dark mode não foram auditados para conformidade WCAG. Cores intermediárias como `--ink-muted: #6b7a8a` sobre `#121212` têm contraste 4.3:1 (abaixo do mínimo 4.5:1 para texto normal). Plataformas B2G devem ter light mode como padrão — 82.7% dos consumidores usam dark mode pessoalmente, mas B2B/govtech prioriza trust e legibilidade com light mode.

## Problema (Causa Raiz)
- `frontend/app/components/ThemeProvider.tsx:17`: Dark canvas `#121212` com `ink: #e0e0e0` (OK), mas `--ink-muted: #6b7a8a` tem contraste insuficiente contra `#121212`.
- `--ink-faint: #3a4555` tem contraste ~2.5:1 contra `#121212` (falha WCAG AA para qualquer tamanho).
- Nenhum script de validação de contraste existe no pipeline de CI.
- Flash de tema: `useState("light")` inicializa no servidor, mas `useEffect` pode trocar para valor do localStorage causando flash.

## Critérios de Aceitação
- [x] AC1: Manter "light" como tema padrão para novos usuários (confirmar).
- [x] AC2: Adicionar script inline no `<head>` (antes do React) que lê localStorage e aplica classe `dark` imediatamente, evitando flash de tema:
  ```html
  <script>
    (function() {
      var t = localStorage.getItem('smartlic-theme');
      if (t === 'dark' || (t === 'system' && matchMedia('(prefers-color-scheme:dark)').matches)) {
        document.documentElement.classList.add('dark');
      }
    })();
  </script>
  ```
- [x] AC3: Auditar TODOS os pares de cor do dark mode e garantir WCAG AA (4.5:1 texto normal, 3:1 texto grande/UI):
  - `--ink` / `--canvas`: mínimo 4.5:1
  - `--ink-secondary` / `--canvas`: mínimo 4.5:1
  - `--ink-muted` / `--canvas`: mínimo 4.5:1
  - `--ink-muted` / `--surface-1`: mínimo 4.5:1
  - `--ink-faint` / `--canvas`: mínimo 3:1 (uso apenas em texto grande/decorativo)
  - `--success`, `--error`, `--warning` / respectivos `--*-subtle`: mínimo 4.5:1
- [x] AC4: Ajustar `--ink-muted` dark de `#6b7a8a` para `#8b9bb0` (contraste 5.3:1 contra `#121212`).
- [x] AC5: Ajustar `--ink-faint` dark de `#3a4555` para `#5a6a7a` (contraste 3.4:1, uso apenas decorativo).
- [x] AC6: Nunca usar `#000000` puro como background em dark mode (manter `#121212` ou similar).
- [x] AC7: Nunca usar `#ffffff` puro como texto em dark mode (manter `#e0e0e0` ou similar).
- [x] AC8: Adicionar teste automatizado que valida razão de contraste para todos os pares de cor do ThemeProvider.

## Arquivos Impactados
- `frontend/app/components/ThemeProvider.tsx` — Ajustar tokens de cor do dark mode.
- `frontend/app/layout.tsx` — Adicionar script inline de anti-flash.
- `frontend/tailwind.config.js` — Verificar se tokens custom são usados consistentemente.

## Testes Necessários
- [x] Teste automatizado de contraste WCAG para todos os pares de cor (light + dark).
- [x] Teste que tema padrão é "light" quando nada no localStorage.
- [x] Teste que script anti-flash aplica classe `dark` antes do primeiro paint.
- [x] Teste visual (snapshot) do LicitacaoCard em dark mode.
- [x] Teste que `ink-muted` tem contraste >= 4.5:1 no dark mode.

## Notas Técnicas
- Ferramenta de cálculo de contraste: `(L1 + 0.05) / (L2 + 0.05)` onde L1 e L2 são luminâncias relativas.
- Cores ajustadas foram calculadas para maximizar contraste mantendo a paleta coerente.
- Referências: WCAG 2.2 SC 1.4.3, Digital.gov USWDS dark mode guidelines.
