---
name: Frontend Error Boundaries
about: Implementar error.tsx para tratamento de erros no frontend
title: 'Frontend Error Boundaries'
labels: 'frontend, feature, error-handling'
assignees: ''

---

## 📋 Descrição

Implementar error boundary React conforme estrutura definida no PRD Seção 7.2.

**EPIC:** #20 (Frontend - Next.js)
**Prioridade:** P1 (Alta)
**Estimativa:** 2 horas

## 🎯 Objetivo

Criar componente error boundary para capturar e tratar erros no frontend de forma amigável, melhorando UX.

## 📚 Referência PRD

- **PRD Seção 7.2 linha 1187:** Estrutura de arquivos inclui `error.tsx`

## ✅ Acceptance Criteria

- [ ] Arquivo `frontend/app/error.tsx` criado
- [ ] Error boundary component implementado seguindo Next.js 14 conventions
- [ ] Fallback UI amigável e claro para o usuário
- [ ] Botão "Tentar novamente" funcional (reset)
- [ ] Mensagem de erro exibida (sem stack trace em produção)
- [ ] Erros logados no console (development mode)
- [ ] Erros reportados para serviço de monitoramento (produção - opcional)
- [ ] Testes para error boundary (componente renderiza corretamente)
- [ ] Documentação inline (JSDoc)

## 🛠️ Implementação

### Criar `frontend/app/error.tsx`

```tsx
'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error boundary caught:', error)
    }

    // TODO: Log to error reporting service in production
    // e.g., Sentry, LogRocket, etc.
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
        <div className="flex items-center justify-center w-16 h-16 mx-auto bg-red-100 rounded-full mb-4">
          <svg
            className="w-8 h-8 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          Ops! Algo deu errado
        </h2>

        <p className="text-gray-600 text-center mb-6">
          {error.message || 'Ocorreu um erro inesperado. Por favor, tente novamente.'}
        </p>

        {process.env.NODE_ENV === 'development' && error.digest && (
          <p className="text-xs text-gray-400 text-center mb-4">
            Error ID: {error.digest}
          </p>
        )}

        <button
          onClick={reset}
          className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Tentar novamente
        </button>

        <button
          onClick={() => window.location.href = '/'}
          className="w-full mt-3 px-4 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
        >
          Voltar à página inicial
        </button>
      </div>
    </div>
  )
}
```

### Teste Exemplo

Criar `frontend/__tests__/error.test.tsx`:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import Error from '@/app/error'

describe('Error Boundary', () => {
  const mockReset = jest.fn()
  const mockError = new Error('Test error message')

  it('renders error message', () => {
    render(<Error error={mockError} reset={mockReset} />)

    expect(screen.getByText('Ops! Algo deu errado')).toBeInTheDocument()
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('calls reset when button clicked', () => {
    render(<Error error={mockError} reset={mockReset} />)

    const resetButton = screen.getByText('Tentar novamente')
    fireEvent.click(resetButton)

    expect(mockReset).toHaveBeenCalled()
  })
})
```

## 🧪 Testando Manualmente

Para testar o error boundary, você pode simular um erro adicionando temporariamente em `page.tsx`:

```tsx
// Adicionar temporariamente para testar
if (typeof window !== 'undefined') {
  throw new Error('Teste de error boundary')
}
```

## 🔗 Dependências

**Bloqueado por:** #21 (Setup Next.js)
**Bloqueia:** Nenhum

## 📝 Notas

- Error boundaries em Next.js 14 App Router funcionam automaticamente
- `error.tsx` deve ser Client Component ('use client')
- Em produção, evitar expor stack traces completos
- Considerar integração com Sentry ou similar para produção

## ✨ Definição de Pronto

- [ ] Todos os acceptance criteria cumpridos
- [ ] Error boundary funciona quando erro é lançado
- [ ] Botão reset funciona corretamente
- [ ] UI é amigável e clara
- [ ] Testes passando
- [ ] PR criado e merged
