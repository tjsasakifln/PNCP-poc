---
name: Frontend Form Validations
about: Implementar validações client-side para formulário de busca
title: 'Frontend Form Validations'
labels: 'frontend, feature, validation'
assignees: ''

---

## 📋 Descrição

Implementar validações client-side para formulário de busca de licitações conforme PRD Seção 7.3 linhas 1259-1262.

**EPIC:** #20 (Frontend - Next.js)
**Prioridade:** P1 (Alta)
**Estimativa:** 1 hora

## 🎯 Objetivo

Prevenir submissões inválidas ao backend e melhorar feedback ao usuário com validações client-side.

## 📚 Referência PRD

- **PRD Seção 7.3 linhas 1258-1292:** Função `buscar()` com validação de UFs
- **PRD Seção 1.2:** Limite de 30 dias para busca
- **PRD linha 1259-1262:** Validação "Selecione pelo menos um estado"

## ✅ Acceptance Criteria

### Validações Implementadas
- [ ] **UFs:** Mínimo 1 UF selecionada
- [ ] **Data Inicial:** Campo não pode estar vazio
- [ ] **Data Final:** Campo não pode estar vazio
- [ ] **Range de Datas:** data_final >= data_inicial
- [ ] **Limite de Período:** Máximo 30 dias entre datas (PRD Seção 1.2)

### UX/UI
- [ ] Mensagens de erro inline e claras
- [ ] Feedback visual em campos inválidos (borda vermelha)
- [ ] Botão "Buscar" desabilitado se validação falhar
- [ ] Estados de erro limpos ao corrigir campos
- [ ] Erros exibidos antes de tentar submeter ao backend

### Testes
- [ ] Teste unitário para cada validação
- [ ] Teste de integração do formulário completo

## 🛠️ Implementação

### 1. Adicionar Estado de Validação

Em `frontend/app/page.tsx`, adicionar:

```tsx
const [validationError, setValidationError] = useState<string | null>(null)

const validar = (): string | null => {
  // Validação 1: Mínimo 1 UF
  if (ufsSelecionadas.size === 0) {
    return "Selecione pelo menos um estado"
  }

  // Validação 2: Datas não vazias
  if (!dataInicial || !dataFinal) {
    return "Preencha as datas inicial e final"
  }

  // Validação 3: Data final >= inicial
  const inicio = new Date(dataInicial)
  const fim = new Date(dataFinal)

  if (fim < inicio) {
    return "Data final deve ser maior ou igual à data inicial"
  }

  // Validação 4: Máximo 30 dias (PRD Seção 1.2)
  const diffMs = fim.getTime() - inicio.getTime()
  const diffDias = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

  if (diffDias > 30) {
    return "Período máximo de busca é 30 dias"
  }

  return null // Sem erros
}
```

### 2. Atualizar Função buscar()

```tsx
const buscar = async () => {
  // Validar antes de submeter
  const erro = validar()
  if (erro) {
    setValidationError(erro)
    return
  }

  setValidationError(null)
  setLoading(true)
  setError(null)
  setResult(null)

  try {
    // ... resto da implementação
  } catch (e) {
    setError(e instanceof Error ? e.message : "Erro desconhecido")
  } finally {
    setLoading(false)
  }
}
```

### 3. Componente de Erro Inline

```tsx
{validationError && (
  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
    <svg
      className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
    <div>
      <h3 className="font-medium text-red-800">Erro de validação</h3>
      <p className="text-sm text-red-700 mt-1">{validationError}</p>
    </div>
  </div>
)}
```

### 4. Estilizar Campos Inválidos

```tsx
// Adicionar estado para rastrear campos tocados
const [touched, setTouched] = useState({ ufs: false, datas: false })

// Classe condicional para inputs
const inputClassName = (isInvalid: boolean) =>
  `px-3 py-2 border rounded-md ${
    isInvalid && touched.datas
      ? 'border-red-500 focus:ring-red-500'
      : 'border-gray-300 focus:ring-blue-500'
  }`
```

### 5. Desabilitar Botão se Inválido

```tsx
<button
  onClick={buscar}
  disabled={loading || ufsSelecionadas.size === 0}
  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
    loading || ufsSelecionadas.size === 0
      ? 'bg-gray-400 cursor-not-allowed'
      : 'bg-green-600 hover:bg-green-700 text-white'
  }`}
>
  {loading ? (
    <>
      <span className="animate-spin mr-2">⏳</span>
      Buscando...
    </>
  ) : (
    '🔍 Buscar Licitações'
  )}
</button>
```

### 6. Limpar Erros ao Corrigir

```tsx
// Limpar erro ao modificar UFs
const toggleUf = (uf: string) => {
  const newSet = new Set(ufsSelecionadas)
  if (newSet.has(uf)) {
    newSet.delete(uf)
  } else {
    newSet.add(uf)
  }
  setUfsSelecionadas(newSet)
  setValidationError(null) // Limpar erro
}

// Limpar erro ao modificar datas
const handleDataChange = (setter: any) => (e: React.ChangeEvent<HTMLInputElement>) => {
  setter(e.target.value)
  setValidationError(null) // Limpar erro
}
```

## 🧪 Testes Unitários

Criar `frontend/__tests__/validations.test.ts`:

```typescript
import { validar } from '@/app/page' // Exportar função

describe('Form Validations', () => {
  it('rejects empty UF selection', () => {
    const error = validar(new Set(), '2024-01-01', '2024-01-10')
    expect(error).toBe('Selecione pelo menos um estado')
  })

  it('rejects date final < inicial', () => {
    const error = validar(new Set(['SC']), '2024-01-10', '2024-01-01')
    expect(error).toBe('Data final deve ser maior ou igual à data inicial')
  })

  it('rejects range > 30 dias', () => {
    const error = validar(new Set(['SC']), '2024-01-01', '2024-02-15')
    expect(error).toBe('Período máximo de busca é 30 dias')
  })

  it('accepts valid input', () => {
    const error = validar(new Set(['SC', 'PR']), '2024-01-01', '2024-01-10')
    expect(error).toBeNull()
  })
})
```

## 🔗 Dependências

**Bloqueado por:** #22 (Interface seleção UFs) - pode ser implementado junto
**Bloqueia:** Nenhum

## 📝 Notas

- PRD linha 1259 já mostra validação de UFs vazia implementada
- Esta issue formaliza e expande todas as validações client-side
- Validações client-side não substituem validações server-side (backend deve validar também)
- UX é melhorada com feedback imediato

## ✨ Definição de Pronto

- [ ] Todos os acceptance criteria cumpridos
- [ ] Validações funcionando corretamente
- [ ] Mensagens de erro claras e úteis
- [ ] Testes unitários passando
- [ ] UI responsiva e acessível
- [ ] PR criado e merged
