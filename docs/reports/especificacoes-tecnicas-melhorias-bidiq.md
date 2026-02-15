# Especificações Técnicas Detalhadas - Melhorias BidIQ

**Documento:** Especificações de Implementação
**Versão:** 1.0
**Data:** 06/02/2026

---

## Índice

1. [Filtro de Status da Licitação](#1-filtro-de-status-da-licitação)
2. [Filtro de Modalidade de Contratação](#2-filtro-de-modalidade-de-contratação)
3. [Filtro de Faixa de Valor](#3-filtro-de-faixa-de-valor)
4. [Filtro de Esfera Governamental](#4-filtro-de-esfera-governamental)
5. [Filtro de Município](#5-filtro-de-município)
6. [Filtro de Órgão](#6-filtro-de-órgão)
7. [Ordenação de Resultados](#7-ordenação-de-resultados)
8. [Paginação Configurável](#8-paginação-configurável)
9. [Melhorias nos Cards de Resultado](#9-melhorias-nos-cards-de-resultado)
10. [Otimização de Performance](#10-otimização-de-performance)

---

## 1. Filtro de Status da Licitação

### 1.1 Descrição Funcional

O filtro de status permite ao usuário selecionar licitações com base no estágio atual do processo licitatório.

**Opções disponíveis:**
| Status | Código API | Descrição |
|--------|------------|-----------|
| Recebendo Propostas | `recebendo_proposta` | Licitações abertas para envio de propostas |
| Em Julgamento | `em_julgamento` | Propostas encerradas, em análise |
| Encerradas | `encerrada` | Processo finalizado (com ou sem vencedor) |
| Todas | `todos` | Sem filtro de status |

### 1.2 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Status da Licitação:                                        │
│                                                             │
│  ┌──────────────────┐ ┌──────────────────┐                 │
│  │ ● Abertas        │ │ ○ Em Julgamento  │                 │
│  └──────────────────┘ └──────────────────┘                 │
│  ┌──────────────────┐ ┌──────────────────┐                 │
│  │ ○ Encerradas     │ │ ○ Todas          │                 │
│  └──────────────────┘ └──────────────────┘                 │
│                                                             │
│  💡 Dica: "Abertas" mostra licitações que ainda aceitam    │
│     propostas                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Especificação do Componente Frontend

**Arquivo:** `frontend/components/StatusFilter.tsx`

```typescript
// frontend/components/StatusFilter.tsx

import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Info } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export type StatusLicitacao =
  | 'recebendo_proposta'
  | 'em_julgamento'
  | 'encerrada'
  | 'todos';

interface StatusFilterProps {
  value: StatusLicitacao;
  onChange: (value: StatusLicitacao) => void;
  disabled?: boolean;
}

const STATUS_OPTIONS: Array<{
  value: StatusLicitacao;
  label: string;
  description: string;
  badge?: { color: string; text: string };
}> = [
  {
    value: 'recebendo_proposta',
    label: 'Abertas',
    description: 'Licitações que ainda aceitam propostas',
    badge: { color: 'bg-green-500', text: 'Recomendado' },
  },
  {
    value: 'em_julgamento',
    label: 'Em Julgamento',
    description: 'Propostas encerradas, em análise pelo órgão',
  },
  {
    value: 'encerrada',
    label: 'Encerradas',
    description: 'Processo finalizado',
  },
  {
    value: 'todos',
    label: 'Todas',
    description: 'Exibir todas independente do status',
  },
];

export function StatusFilter({
  value,
  onChange,
  disabled
}: StatusFilterProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Label className="text-sm font-medium text-gray-200">
          Status da Licitação:
        </Label>
        <Tooltip>
          <TooltipTrigger>
            <Info className="h-4 w-4 text-gray-400" />
          </TooltipTrigger>
          <TooltipContent>
            <p>Filtre por licitações abertas para enviar propostas</p>
          </TooltipContent>
        </Tooltip>
      </div>

      <RadioGroup
        value={value}
        onValueChange={(v) => onChange(v as StatusLicitacao)}
        disabled={disabled}
        className="grid grid-cols-2 gap-3"
      >
        {STATUS_OPTIONS.map((option) => (
          <div key={option.value} className="relative">
            <RadioGroupItem
              value={option.value}
              id={`status-${option.value}`}
              className="peer sr-only"
            />
            <Label
              htmlFor={`status-${option.value}`}
              className={`
                flex items-center justify-center gap-2
                rounded-lg border-2 border-gray-700
                bg-gray-800/50 p-3 cursor-pointer
                transition-all duration-200
                hover:border-gray-600 hover:bg-gray-800
                peer-checked:border-blue-500 peer-checked:bg-blue-500/10
                peer-disabled:cursor-not-allowed peer-disabled:opacity-50
              `}
            >
              <span className="font-medium">{option.label}</span>
              {option.badge && (
                <span className={`
                  text-xs px-2 py-0.5 rounded-full
                  ${option.badge.color} text-white
                `}>
                  {option.badge.text}
                </span>
              )}
            </Label>
          </div>
        ))}
      </RadioGroup>
    </div>
  );
}
```

### 1.4 Especificação do Backend

**Arquivo:** `backend/schemas.py` - Adicionar ao BuscaRequest

```python
# backend/schemas.py

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class StatusLicitacao(str, Enum):
    RECEBENDO_PROPOSTA = "recebendo_proposta"
    EM_JULGAMENTO = "em_julgamento"
    ENCERRADA = "encerrada"
    TODOS = "todos"

class BuscaRequest(BaseModel):
    ufs: list[str] = Field(..., min_length=1, max_length=27)
    data_inicial: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_final: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")

    # NOVO: Filtro de status
    status: StatusLicitacao = Field(
        default=StatusLicitacao.RECEBENDO_PROPOSTA,
        description="Status da licitação para filtrar"
    )

    # Outros campos existentes...
    setor: Optional[str] = None
    termos: Optional[list[str]] = None
```

**Arquivo:** `backend/pncp_client.py` - Modificar query

```python
# backend/pncp_client.py

from schemas import StatusLicitacao

# Mapeamento de status para parâmetro da API PNCP
STATUS_MAP = {
    StatusLicitacao.RECEBENDO_PROPOSTA: "recebendo_proposta",
    StatusLicitacao.EM_JULGAMENTO: "propostas_encerradas",
    StatusLicitacao.ENCERRADA: "encerrada",
    StatusLicitacao.TODOS: None,  # Não envia parâmetro
}

async def buscar_licitacoes(
    uf: str,
    data_inicial: str,
    data_final: str,
    status: StatusLicitacao = StatusLicitacao.RECEBENDO_PROPOSTA,
    **kwargs
) -> list[dict]:
    """
    Busca licitações na API do PNCP com filtro de status.
    """
    params = {
        "dataPublicacaoInicio": data_inicial,
        "dataPublicacaoFim": data_final,
        "uf": uf,
        "pagina": 1,
        "tamanhoPagina": 500,
    }

    # Adiciona status se não for "todos"
    status_param = STATUS_MAP.get(status)
    if status_param:
        params["status"] = status_param

    # ... resto da implementação existente
```

### 1.5 Testes

**Arquivo:** `backend/tests/test_status_filter.py`

```python
# backend/tests/test_status_filter.py

import pytest
from schemas import StatusLicitacao, BuscaRequest

class TestStatusFilter:

    def test_default_status_is_recebendo_proposta(self):
        """Status padrão deve ser 'recebendo_proposta'."""
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-01-01",
            data_final="2026-01-31"
        )
        assert request.status == StatusLicitacao.RECEBENDO_PROPOSTA

    def test_status_enum_values(self):
        """Todos os valores de status devem ser válidos."""
        valid_statuses = [
            "recebendo_proposta",
            "em_julgamento",
            "encerrada",
            "todos"
        ]
        for status in valid_statuses:
            request = BuscaRequest(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                status=status
            )
            assert request.status.value == status

    def test_invalid_status_raises_error(self):
        """Status inválido deve gerar erro de validação."""
        with pytest.raises(ValueError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                status="invalido"
            )

    @pytest.mark.asyncio
    async def test_pncp_query_includes_status(self, mock_pncp_client):
        """Query para PNCP deve incluir parâmetro de status."""
        # Implementar teste de integração
        pass
```

### 1.6 Critérios de Aceite

- [ ] Componente renderiza 4 opções de status
- [ ] "Abertas" é selecionado por padrão
- [ ] Mudança de status dispara nova busca
- [ ] API Backend aceita parâmetro `status`
- [ ] Query PNCP inclui filtro de status correto
- [ ] Testes unitários passam com cobertura > 90%
- [ ] Documentação da API atualizada

---

## 2. Filtro de Modalidade de Contratação

### 2.1 Descrição Funcional

Permite filtrar licitações por tipo de modalidade de contratação.

**Modalidades disponíveis:**
| Código | Modalidade | Descrição |
|--------|------------|-----------|
| 1 | Pregão Eletrônico | Licitação eletrônica para bens e serviços comuns |
| 2 | Pregão Presencial | Licitação presencial para bens e serviços comuns |
| 3 | Concorrência | Para obras, serviços de engenharia e compras de grande valor |
| 4 | Tomada de Preços | Modalidade intermediária (valores médios) |
| 5 | Convite | Para valores menores |
| 6 | Dispensa de Licitação | Contratação direta sem licitação |
| 7 | Inexigibilidade | Quando há inviabilidade de competição |
| 8 | Credenciamento | Cadastro de fornecedores |
| 9 | Leilão | Para venda de bens |
| 10 | Diálogo Competitivo | Para soluções inovadoras |

### 2.2 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Modalidade de Contratação:                    [Expandir ▼]  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ Pregão Eletrônico        ☑ Dispensa              │   │
│  │ ☑ Pregão Presencial        ☐ Inexigibilidade       │   │
│  │ ☐ Concorrência             ☐ Credenciamento        │   │
│  │ ☐ Tomada de Preços         ☐ Leilão                │   │
│  │ ☐ Convite                  ☐ Diálogo Competitivo   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  3 modalidades selecionadas    [Selecionar todas] [Limpar] │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Especificação do Componente Frontend

**Arquivo:** `frontend/components/ModalidadeFilter.tsx`

```typescript
// frontend/components/ModalidadeFilter.tsx

import { useState } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

export interface Modalidade {
  codigo: number;
  nome: string;
  descricao: string;
  popular?: boolean; // Modalidades mais usadas
}

const MODALIDADES: Modalidade[] = [
  {
    codigo: 1,
    nome: 'Pregão Eletrônico',
    descricao: 'Licitação eletrônica para bens e serviços comuns',
    popular: true
  },
  {
    codigo: 2,
    nome: 'Pregão Presencial',
    descricao: 'Licitação presencial para bens e serviços comuns',
    popular: true
  },
  {
    codigo: 6,
    nome: 'Dispensa de Licitação',
    descricao: 'Contratação direta sem processo licitatório',
    popular: true
  },
  {
    codigo: 3,
    nome: 'Concorrência',
    descricao: 'Para obras e serviços de grande valor'
  },
  {
    codigo: 4,
    nome: 'Tomada de Preços',
    descricao: 'Modalidade para valores intermediários'
  },
  {
    codigo: 5,
    nome: 'Convite',
    descricao: 'Para contratações de menor valor'
  },
  {
    codigo: 7,
    nome: 'Inexigibilidade',
    descricao: 'Quando há inviabilidade de competição'
  },
  {
    codigo: 8,
    nome: 'Credenciamento',
    descricao: 'Cadastro de fornecedores interessados'
  },
  {
    codigo: 9,
    nome: 'Leilão',
    descricao: 'Para alienação de bens'
  },
  {
    codigo: 10,
    nome: 'Diálogo Competitivo',
    descricao: 'Para soluções inovadoras'
  },
];

interface ModalidadeFilterProps {
  selected: number[];
  onChange: (modalidades: number[]) => void;
  disabled?: boolean;
}

export function ModalidadeFilter({
  selected,
  onChange,
  disabled
}: ModalidadeFilterProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Modalidades populares sempre visíveis
  const popularModalidades = MODALIDADES.filter(m => m.popular);
  const outrasModalidades = MODALIDADES.filter(m => !m.popular);

  const handleToggle = (codigo: number) => {
    if (selected.includes(codigo)) {
      onChange(selected.filter(c => c !== codigo));
    } else {
      onChange([...selected, codigo]);
    }
  };

  const handleSelectAll = () => {
    onChange(MODALIDADES.map(m => m.codigo));
  };

  const handleClear = () => {
    onChange([]);
  };

  const renderCheckbox = (modalidade: Modalidade) => (
    <div
      key={modalidade.codigo}
      className="flex items-center space-x-2 p-2 rounded hover:bg-gray-800"
    >
      <Checkbox
        id={`modalidade-${modalidade.codigo}`}
        checked={selected.includes(modalidade.codigo)}
        onCheckedChange={() => handleToggle(modalidade.codigo)}
        disabled={disabled}
      />
      <Label
        htmlFor={`modalidade-${modalidade.codigo}`}
        className="text-sm cursor-pointer flex-1"
        title={modalidade.descricao}
      >
        {modalidade.nome}
      </Label>
    </div>
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium text-gray-200">
          Modalidade de Contratação:
        </Label>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSelectAll}
            disabled={disabled}
          >
            Todas
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            disabled={disabled || selected.length === 0}
          >
            Limpar
          </Button>
        </div>
      </div>

      {/* Modalidades populares - sempre visíveis */}
      <div className="grid grid-cols-2 gap-1 p-3 bg-gray-800/30 rounded-lg">
        {popularModalidades.map(renderCheckbox)}
      </div>

      {/* Outras modalidades - colapsável */}
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-between"
          >
            <span>
              {isOpen ? 'Menos opções' : 'Mais opções'}
              {!isOpen && outrasModalidades.some(m =>
                selected.includes(m.codigo)
              ) && (
                <span className="ml-2 text-blue-400">
                  ({outrasModalidades.filter(m =>
                    selected.includes(m.codigo)
                  ).length} selecionadas)
                </span>
              )}
            </span>
            {isOpen ? <ChevronUp /> : <ChevronDown />}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="grid grid-cols-2 gap-1 p-3 bg-gray-800/30 rounded-lg mt-2">
            {outrasModalidades.map(renderCheckbox)}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Contador */}
      {selected.length > 0 && (
        <p className="text-sm text-gray-400">
          {selected.length} {selected.length === 1 ? 'modalidade selecionada' : 'modalidades selecionadas'}
        </p>
      )}
    </div>
  );
}
```

### 2.4 Especificação do Backend

**Arquivo:** `backend/schemas.py`

```python
# backend/schemas.py

from enum import IntEnum

class ModalidadeContratacao(IntEnum):
    PREGAO_ELETRONICO = 1
    PREGAO_PRESENCIAL = 2
    CONCORRENCIA = 3
    TOMADA_PRECOS = 4
    CONVITE = 5
    DISPENSA = 6
    INEXIGIBILIDADE = 7
    CREDENCIAMENTO = 8
    LEILAO = 9
    DIALOGO_COMPETITIVO = 10

class BuscaRequest(BaseModel):
    # ... campos existentes ...

    # NOVO: Filtro de modalidade
    modalidades: Optional[list[int]] = Field(
        default=None,
        description="Lista de códigos de modalidade para filtrar"
    )
```

**Arquivo:** `backend/filter.py` - Adicionar filtro

```python
# backend/filter.py

def filtrar_por_modalidade(
    licitacoes: list[dict],
    modalidades: list[int] | None
) -> list[dict]:
    """
    Filtra licitações por modalidade de contratação.

    Args:
        licitacoes: Lista de licitações
        modalidades: Lista de códigos de modalidade (None = todas)

    Returns:
        Lista filtrada de licitações
    """
    if not modalidades:
        return licitacoes

    return [
        lic for lic in licitacoes
        if lic.get('modalidadeId') in modalidades
        or lic.get('codigoModalidadeContratacao') in modalidades
    ]
```

### 2.5 Critérios de Aceite

- [ ] Exibe modalidades populares por padrão
- [ ] Permite expandir para ver todas as modalidades
- [ ] Multi-select funciona corretamente
- [ ] "Todas" seleciona todas as modalidades
- [ ] "Limpar" desmarca todas
- [ ] Contador mostra quantidade selecionada
- [ ] Backend filtra corretamente por modalidade
- [ ] Testes cobrem todos os cenários

---

## 3. Filtro de Faixa de Valor

### 3.1 Descrição Funcional

Permite filtrar licitações por valor estimado, usando faixas pré-definidas ou valores customizados.

**Faixas sugeridas:**
| Faixa | Valor Mínimo | Valor Máximo |
|-------|--------------|--------------|
| Micro | R$ 0 | R$ 50.000 |
| Pequeno | R$ 50.000 | R$ 200.000 |
| Médio | R$ 200.000 | R$ 1.000.000 |
| Grande | R$ 1.000.000 | R$ 5.000.000 |
| Muito Grande | R$ 5.000.000 | Sem limite |

### 3.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│ Valor Estimado:                                                     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                                                               │ │
│  │  R$ 50.000 ════════════●════════════════●═════ R$ 5.000.000  │ │
│  │                        ▲                ▲                     │ │
│  │                    Mínimo           Máximo                    │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Ou selecione uma faixa rápida:                                    │
│                                                                     │
│  [Até 50k] [50k-200k] [200k-1M] [●1M-5M] [Acima 5M] [Qualquer]    │
│                                                                     │
│  Valores customizados:                                              │
│  Mínimo: R$ [    50.000,00 ]   Máximo: R$ [ 5.000.000,00 ]        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Especificação do Componente Frontend

**Arquivo:** `frontend/components/ValorFilter.tsx`

```typescript
// frontend/components/ValorFilter.tsx

import { useState, useCallback } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

interface FaixaValor {
  id: string;
  label: string;
  min: number;
  max: number | null; // null = sem limite
}

const FAIXAS_VALOR: FaixaValor[] = [
  { id: 'micro', label: 'Até 50k', min: 0, max: 50000 },
  { id: 'pequeno', label: '50k-200k', min: 50000, max: 200000 },
  { id: 'medio', label: '200k-1M', min: 200000, max: 1000000 },
  { id: 'grande', label: '1M-5M', min: 1000000, max: 5000000 },
  { id: 'muito_grande', label: 'Acima 5M', min: 5000000, max: null },
  { id: 'qualquer', label: 'Qualquer', min: 0, max: null },
];

// Limites do slider
const SLIDER_MIN = 0;
const SLIDER_MAX = 10000000; // R$ 10 milhões
const SLIDER_STEP = 10000; // R$ 10 mil

interface ValorFilterProps {
  valorMin: number | null;
  valorMax: number | null;
  onChange: (min: number | null, max: number | null) => void;
  disabled?: boolean;
}

export function ValorFilter({
  valorMin,
  valorMax,
  onChange,
  disabled,
}: ValorFilterProps) {
  const [inputMin, setInputMin] = useState(
    valorMin?.toLocaleString('pt-BR') ?? ''
  );
  const [inputMax, setInputMax] = useState(
    valorMax?.toLocaleString('pt-BR') ?? ''
  );

  // Identifica qual faixa está selecionada
  const faixaSelecionada = FAIXAS_VALOR.find(
    f => f.min === valorMin && f.max === valorMax
  )?.id ?? 'custom';

  const handleFaixaClick = (faixa: FaixaValor) => {
    onChange(faixa.min, faixa.max);
    setInputMin(faixa.min.toLocaleString('pt-BR'));
    setInputMax(faixa.max?.toLocaleString('pt-BR') ?? '');
  };

  const handleSliderChange = (values: number[]) => {
    const [min, max] = values;
    onChange(min, max === SLIDER_MAX ? null : max);
    setInputMin(min.toLocaleString('pt-BR'));
    setInputMax(max === SLIDER_MAX ? '' : max.toLocaleString('pt-BR'));
  };

  const parseInputValue = (value: string): number | null => {
    const cleaned = value.replace(/\D/g, '');
    return cleaned ? parseInt(cleaned, 10) : null;
  };

  const handleInputMinBlur = () => {
    const parsed = parseInputValue(inputMin);
    if (parsed !== null) {
      onChange(parsed, valorMax);
      setInputMin(parsed.toLocaleString('pt-BR'));
    }
  };

  const handleInputMaxBlur = () => {
    const parsed = parseInputValue(inputMax);
    onChange(valorMin, parsed);
    setInputMax(parsed?.toLocaleString('pt-BR') ?? '');
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="space-y-4">
      <Label className="text-sm font-medium text-gray-200">
        Valor Estimado:
      </Label>

      {/* Slider */}
      <div className="px-2 py-4">
        <Slider
          min={SLIDER_MIN}
          max={SLIDER_MAX}
          step={SLIDER_STEP}
          value={[
            valorMin ?? SLIDER_MIN,
            valorMax ?? SLIDER_MAX,
          ]}
          onValueChange={handleSliderChange}
          disabled={disabled}
          className="w-full"
        />
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>{formatCurrency(valorMin ?? 0)}</span>
          <span>{valorMax ? formatCurrency(valorMax) : 'Sem limite'}</span>
        </div>
      </div>

      {/* Faixas rápidas */}
      <div className="flex flex-wrap gap-2">
        {FAIXAS_VALOR.map((faixa) => (
          <Button
            key={faixa.id}
            variant={faixaSelecionada === faixa.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleFaixaClick(faixa)}
            disabled={disabled}
            className="text-xs"
          >
            {faixa.label}
          </Button>
        ))}
      </div>

      {/* Inputs customizados */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor="valor-min" className="text-xs text-gray-400">
            Mínimo:
          </Label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              R$
            </span>
            <Input
              id="valor-min"
              value={inputMin}
              onChange={(e) => setInputMin(e.target.value)}
              onBlur={handleInputMinBlur}
              placeholder="0"
              className="pl-10"
              disabled={disabled}
            />
          </div>
        </div>
        <div className="space-y-1">
          <Label htmlFor="valor-max" className="text-xs text-gray-400">
            Máximo:
          </Label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              R$
            </span>
            <Input
              id="valor-max"
              value={inputMax}
              onChange={(e) => setInputMax(e.target.value)}
              onBlur={handleInputMaxBlur}
              placeholder="Sem limite"
              className="pl-10"
              disabled={disabled}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 3.4 Especificação do Backend

**Arquivo:** `backend/schemas.py`

```python
# backend/schemas.py

class BuscaRequest(BaseModel):
    # ... campos existentes ...

    # NOVO: Filtro de valor
    valor_minimo: Optional[float] = Field(
        default=None,
        ge=0,
        description="Valor mínimo estimado da licitação"
    )
    valor_maximo: Optional[float] = Field(
        default=None,
        ge=0,
        description="Valor máximo estimado da licitação"
    )

    @validator('valor_maximo')
    def valor_maximo_maior_que_minimo(cls, v, values):
        if v is not None and values.get('valor_minimo') is not None:
            if v < values['valor_minimo']:
                raise ValueError(
                    'valor_maximo deve ser maior ou igual a valor_minimo'
                )
        return v
```

**Arquivo:** `backend/filter.py` - Já existe parcialmente

```python
# backend/filter.py

def filtrar_por_valor(
    licitacoes: list[dict],
    valor_minimo: float | None = None,
    valor_maximo: float | None = None
) -> list[dict]:
    """
    Filtra licitações por faixa de valor estimado.

    Args:
        licitacoes: Lista de licitações
        valor_minimo: Valor mínimo (None = sem limite inferior)
        valor_maximo: Valor máximo (None = sem limite superior)

    Returns:
        Lista filtrada de licitações
    """
    resultado = []

    for lic in licitacoes:
        valor = lic.get('valorTotalEstimado') or lic.get('valorEstimado', 0)

        # Tenta converter para float se for string
        if isinstance(valor, str):
            try:
                valor = float(valor.replace('.', '').replace(',', '.'))
            except ValueError:
                valor = 0

        # Aplica filtros
        if valor_minimo is not None and valor < valor_minimo:
            continue
        if valor_maximo is not None and valor > valor_maximo:
            continue

        resultado.append(lic)

    return resultado
```

### 3.5 Critérios de Aceite

- [ ] Slider funciona com valores de 0 a 10M
- [ ] Faixas rápidas aplicam valores corretos
- [ ] Inputs aceitam formatação brasileira (1.000,00)
- [ ] Validação: máximo >= mínimo
- [ ] "Qualquer" ou campo vazio = sem limite
- [ ] Backend filtra corretamente por valor
- [ ] Performance não é impactada significativamente

---

## 4. Filtro de Esfera Governamental

### 4.1 Descrição Funcional

Permite filtrar licitações por nível de governo.

**Esferas:**
| Código | Esfera | Descrição |
|--------|--------|-----------|
| F | Federal | União, autarquias federais, empresas públicas federais |
| E | Estadual | Estados, DF, autarquias estaduais |
| M | Municipal | Prefeituras, câmaras municipais, autarquias municipais |

### 4.2 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Esfera Governamental:                                       │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐                │
│  │ Federal │  │Estadual │  │ ●Municipal  │                │
│  │   🏛️    │  │   🏢    │  │    🏠       │                │
│  └─────────┘  └─────────┘  └─────────────┘                │
│                                                             │
│  1 esfera selecionada                                       │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Especificação do Componente Frontend

**Arquivo:** `frontend/components/EsferaFilter.tsx`

```typescript
// frontend/components/EsferaFilter.tsx

import { Label } from '@/components/ui/label';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Building, Building2, Home } from 'lucide-react';

export type Esfera = 'F' | 'E' | 'M';

interface EsferaOption {
  value: Esfera;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const ESFERAS: EsferaOption[] = [
  {
    value: 'F',
    label: 'Federal',
    icon: Building,
    description: 'União, ministérios, autarquias federais'
  },
  {
    value: 'E',
    label: 'Estadual',
    icon: Building2,
    description: 'Estados, secretarias estaduais'
  },
  {
    value: 'M',
    label: 'Municipal',
    icon: Home,
    description: 'Prefeituras, câmaras municipais'
  },
];

interface EsferaFilterProps {
  selected: Esfera[];
  onChange: (esferas: Esfera[]) => void;
  disabled?: boolean;
}

export function EsferaFilter({
  selected,
  onChange,
  disabled
}: EsferaFilterProps) {
  return (
    <div className="space-y-3">
      <Label className="text-sm font-medium text-gray-200">
        Esfera Governamental:
      </Label>

      <ToggleGroup
        type="multiple"
        value={selected}
        onValueChange={(value) => onChange(value as Esfera[])}
        disabled={disabled}
        className="justify-start gap-3"
      >
        {ESFERAS.map((esfera) => {
          const Icon = esfera.icon;
          const isSelected = selected.includes(esfera.value);

          return (
            <ToggleGroupItem
              key={esfera.value}
              value={esfera.value}
              aria-label={esfera.label}
              title={esfera.description}
              className={`
                flex flex-col items-center gap-1 p-3 min-w-[80px]
                border-2 rounded-lg transition-all
                ${isSelected
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-700 hover:border-gray-600'
                }
              `}
            >
              <Icon className={`h-5 w-5 ${
                isSelected ? 'text-blue-400' : 'text-gray-400'
              }`} />
              <span className="text-sm font-medium">{esfera.label}</span>
            </ToggleGroupItem>
          );
        })}
      </ToggleGroup>

      {selected.length > 0 && (
        <p className="text-sm text-gray-400">
          {selected.length} {selected.length === 1 ? 'esfera selecionada' : 'esferas selecionadas'}
        </p>
      )}
    </div>
  );
}
```

### 4.4 Especificação do Backend

**Arquivo:** `backend/schemas.py`

```python
# backend/schemas.py

from enum import Enum

class EsferaGovernamental(str, Enum):
    FEDERAL = "F"
    ESTADUAL = "E"
    MUNICIPAL = "M"

class BuscaRequest(BaseModel):
    # ... campos existentes ...

    # NOVO: Filtro de esfera
    esferas: Optional[list[EsferaGovernamental]] = Field(
        default=None,
        description="Lista de esferas governamentais para filtrar"
    )
```

**Arquivo:** `backend/filter.py`

```python
# backend/filter.py

def filtrar_por_esfera(
    licitacoes: list[dict],
    esferas: list[str] | None
) -> list[dict]:
    """
    Filtra licitações por esfera governamental.

    Args:
        licitacoes: Lista de licitações
        esferas: Lista de códigos de esfera ('F', 'E', 'M')

    Returns:
        Lista filtrada de licitações
    """
    if not esferas:
        return licitacoes

    esfera_map = {
        'F': ['federal', 'união', 'autarquia federal'],
        'E': ['estadual', 'estado', 'autarquia estadual'],
        'M': ['municipal', 'prefeitura', 'câmara municipal'],
    }

    resultado = []
    for lic in licitacoes:
        esfera_lic = lic.get('esferaId', '').upper()
        tipo_orgao = lic.get('tipoOrgao', '').lower()

        for esfera in esferas:
            if esfera_lic == esfera:
                resultado.append(lic)
                break
            # Fallback: verificar pelo tipo de órgão
            if any(termo in tipo_orgao for termo in esfera_map.get(esfera, [])):
                resultado.append(lic)
                break

    return resultado
```

### 4.5 Critérios de Aceite

- [ ] Permite multi-select de esferas
- [ ] Ícones representam cada esfera
- [ ] Tooltip mostra descrição
- [ ] Contador mostra quantidade selecionada
- [ ] Backend filtra corretamente por esfera
- [ ] Testes cobrem todos os cenários

---

## 5. Filtro de Município

### 5.1 Descrição Funcional

Permite filtrar licitações por município específico, disponível quando pelo menos uma UF está selecionada.

### 5.2 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Município: (opcional)                                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔍 Digite para buscar município...                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Municípios selecionados:                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ São Paulo  ✕ │ │ Campinas  ✕  │ │ Santos    ✕  │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
│                                                             │
│  💡 Deixe vazio para buscar em todos os municípios das UFs │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Especificação do Componente Frontend

**Arquivo:** `frontend/components/MunicipioFilter.tsx`

```typescript
// frontend/components/MunicipioFilter.tsx

import { useState, useEffect, useCallback } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { X, Search, Loader2 } from 'lucide-react';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useDebouncedCallback } from 'use-debounce';

interface Municipio {
  codigo: string; // Código IBGE
  nome: string;
  uf: string;
}

interface MunicipioFilterProps {
  ufs: string[]; // UFs selecionadas
  selected: Municipio[];
  onChange: (municipios: Municipio[]) => void;
  disabled?: boolean;
}

export function MunicipioFilter({
  ufs,
  selected,
  onChange,
  disabled,
}: MunicipioFilterProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState<Municipio[]>([]);
  const [loading, setLoading] = useState(false);

  // Busca municípios na API do IBGE
  const searchMunicipios = useDebouncedCallback(async (term: string) => {
    if (term.length < 2 || ufs.length === 0) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      // Busca em paralelo para todas as UFs selecionadas
      const promises = ufs.map(async (uf) => {
        const response = await fetch(
          `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios`
        );
        const data = await response.json();
        return data
          .filter((m: any) =>
            m.nome.toLowerCase().includes(term.toLowerCase())
          )
          .map((m: any) => ({
            codigo: m.id.toString(),
            nome: m.nome,
            uf: uf,
          }));
      });

      const results = await Promise.all(promises);
      const flattened = results.flat();

      // Remove duplicatas e ordena
      const unique = flattened.filter(
        (m, i, arr) => arr.findIndex(x => x.codigo === m.codigo) === i
      );
      unique.sort((a, b) => a.nome.localeCompare(b.nome));

      setSuggestions(unique.slice(0, 20)); // Limita a 20 resultados
    } catch (error) {
      console.error('Erro ao buscar municípios:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, 300);

  useEffect(() => {
    searchMunicipios(search);
  }, [search, ufs, searchMunicipios]);

  const handleSelect = (municipio: Municipio) => {
    if (!selected.find(m => m.codigo === municipio.codigo)) {
      onChange([...selected, municipio]);
    }
    setSearch('');
    setOpen(false);
  };

  const handleRemove = (codigo: string) => {
    onChange(selected.filter(m => m.codigo !== codigo));
  };

  const isDisabled = disabled || ufs.length === 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium text-gray-200">
          Município: <span className="text-gray-400">(opcional)</span>
        </Label>
        {selected.length > 0 && (
          <button
            onClick={() => onChange([])}
            className="text-xs text-gray-400 hover:text-gray-200"
          >
            Limpar todos
          </button>
        )}
      </div>

      {/* Campo de busca */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder={
                isDisabled
                  ? "Selecione uma UF primeiro"
                  : "Digite para buscar município..."
              }
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onFocus={() => setOpen(true)}
              disabled={isDisabled}
              className="pl-10"
            />
            {loading && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 animate-spin" />
            )}
          </div>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0" align="start">
          <Command>
            <CommandList>
              {suggestions.length === 0 ? (
                <CommandEmpty>
                  {search.length < 2
                    ? 'Digite pelo menos 2 caracteres'
                    : 'Nenhum município encontrado'
                  }
                </CommandEmpty>
              ) : (
                <CommandGroup heading="Municípios">
                  {suggestions.map((municipio) => (
                    <CommandItem
                      key={municipio.codigo}
                      value={municipio.codigo}
                      onSelect={() => handleSelect(municipio)}
                      className="cursor-pointer"
                    >
                      <span>{municipio.nome}</span>
                      <span className="ml-2 text-xs text-gray-400">
                        {municipio.uf}
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      {/* Municípios selecionados */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selected.map((municipio) => (
            <Badge
              key={municipio.codigo}
              variant="secondary"
              className="flex items-center gap-1 pr-1"
            >
              <span>{municipio.nome}/{municipio.uf}</span>
              <button
                onClick={() => handleRemove(municipio.codigo)}
                className="ml-1 rounded-full p-0.5 hover:bg-gray-600"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Dica */}
      <p className="text-xs text-gray-500">
        💡 Deixe vazio para buscar em todos os municípios das UFs selecionadas
      </p>
    </div>
  );
}
```

### 5.4 Especificação do Backend

**Arquivo:** `backend/schemas.py`

```python
# backend/schemas.py

class BuscaRequest(BaseModel):
    # ... campos existentes ...

    # NOVO: Filtro de município
    municipios: Optional[list[str]] = Field(
        default=None,
        description="Lista de códigos IBGE de municípios para filtrar"
    )
```

**Arquivo:** `backend/filter.py`

```python
# backend/filter.py

def filtrar_por_municipio(
    licitacoes: list[dict],
    municipios: list[str] | None
) -> list[dict]:
    """
    Filtra licitações por código de município IBGE.

    Args:
        licitacoes: Lista de licitações
        municipios: Lista de códigos IBGE de municípios

    Returns:
        Lista filtrada de licitações
    """
    if not municipios:
        return licitacoes

    return [
        lic for lic in licitacoes
        if str(lic.get('codigoMunicipioIbge', '')) in municipios
        or str(lic.get('municipioId', '')) in municipios
    ]
```

### 5.5 Critérios de Aceite

- [ ] Campo desabilitado quando nenhuma UF selecionada
- [ ] Busca com debounce de 300ms
- [ ] Busca inicia com 2+ caracteres
- [ ] Resultados limitados a 20 itens
- [ ] Multi-select com badges
- [ ] Botão de remover em cada badge
- [ ] "Limpar todos" funciona
- [ ] Backend filtra por código IBGE

---

## 6. Filtro de Órgão

### 6.1 Descrição Funcional

Permite filtrar licitações por órgão/entidade contratante específico.

### 6.2 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Órgão/Entidade: (opcional)                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔍 Buscar órgão...                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Órgãos frequentes:                                         │
│  • Ministério da Saúde                                      │
│  • Ministério da Educação                                   │
│  • INSS                                                     │
│  • Petrobras                                                │
│                                                             │
│  Órgãos selecionados:                                       │
│  ┌──────────────────────────────┐                          │
│  │ Prefeitura de São Paulo   ✕  │                          │
│  └──────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Especificação - Similar ao MunicipioFilter

A implementação segue o mesmo padrão do filtro de município, com busca por API e multi-select.

---

## 7. Ordenação de Resultados

### 7.1 Descrição Funcional

Permite ordenar os resultados da busca por diferentes critérios.

**Opções de ordenação:**
| Opção | Descrição |
|-------|-----------|
| Mais recente | Data de publicação decrescente (padrão) |
| Mais antigo | Data de publicação crescente |
| Maior valor | Valor estimado decrescente |
| Menor valor | Valor estimado crescente |
| Prazo mais próximo | Data de abertura crescente |
| Relevância | Score de matching com termos de busca |

### 7.2 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ 688 resultados encontrados        Ordenar por: [Recente ▼] │
│                                                             │
│                                   ┌──────────────────────┐ │
│                                   │ ● Mais recente       │ │
│                                   │ ○ Mais antigo        │ │
│                                   │ ○ Maior valor        │ │
│                                   │ ○ Menor valor        │ │
│                                   │ ○ Prazo mais próximo │ │
│                                   │ ○ Relevância         │ │
│                                   └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Especificação do Componente Frontend

**Arquivo:** `frontend/components/OrdenacaoSelect.tsx`

```typescript
// frontend/components/OrdenacaoSelect.tsx

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowDown,
  ArrowUp,
  Calendar,
  DollarSign,
  Sparkles
} from 'lucide-react';

export type OrdenacaoOption =
  | 'data_desc'
  | 'data_asc'
  | 'valor_desc'
  | 'valor_asc'
  | 'prazo_asc'
  | 'relevancia';

interface OrdenacaoItem {
  value: OrdenacaoOption;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const ORDENACAO_OPTIONS: OrdenacaoItem[] = [
  { value: 'data_desc', label: 'Mais recente', icon: ArrowDown },
  { value: 'data_asc', label: 'Mais antigo', icon: ArrowUp },
  { value: 'valor_desc', label: 'Maior valor', icon: DollarSign },
  { value: 'valor_asc', label: 'Menor valor', icon: DollarSign },
  { value: 'prazo_asc', label: 'Prazo mais próximo', icon: Calendar },
  { value: 'relevancia', label: 'Relevância', icon: Sparkles },
];

interface OrdenacaoSelectProps {
  value: OrdenacaoOption;
  onChange: (value: OrdenacaoOption) => void;
  disabled?: boolean;
}

export function OrdenacaoSelect({
  value,
  onChange,
  disabled
}: OrdenacaoSelectProps) {
  return (
    <Select
      value={value}
      onValueChange={(v) => onChange(v as OrdenacaoOption)}
      disabled={disabled}
    >
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Ordenar por..." />
      </SelectTrigger>
      <SelectContent>
        {ORDENACAO_OPTIONS.map((option) => {
          const Icon = option.icon;
          return (
            <SelectItem key={option.value} value={option.value}>
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-gray-400" />
                <span>{option.label}</span>
              </div>
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
```

### 7.4 Especificação do Backend

**Arquivo:** `backend/utils/ordenacao.py`

```python
# backend/utils/ordenacao.py

from typing import Callable
from datetime import datetime

def parse_date(date_str: str | None) -> datetime:
    """Parse date string to datetime, with fallback."""
    if not date_str:
        return datetime.min
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return datetime.min

def parse_valor(valor: any) -> float:
    """Parse valor to float, with fallback."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        try:
            return float(valor.replace('.', '').replace(',', '.'))
        except ValueError:
            return 0.0
    return 0.0

def ordenar_licitacoes(
    licitacoes: list[dict],
    ordenacao: str = 'data_desc',
    termos_busca: list[str] | None = None
) -> list[dict]:
    """
    Ordena lista de licitações pelo critério especificado.

    Args:
        licitacoes: Lista de licitações
        ordenacao: Critério de ordenação
        termos_busca: Termos para cálculo de relevância

    Returns:
        Lista ordenada de licitações
    """

    sort_functions: dict[str, tuple[Callable, bool]] = {
        'data_desc': (
            lambda x: parse_date(x.get('dataPublicacao')),
            True  # reverse=True
        ),
        'data_asc': (
            lambda x: parse_date(x.get('dataPublicacao')),
            False
        ),
        'valor_desc': (
            lambda x: parse_valor(x.get('valorTotalEstimado')),
            True
        ),
        'valor_asc': (
            lambda x: parse_valor(x.get('valorTotalEstimado')),
            False
        ),
        'prazo_asc': (
            lambda x: parse_date(x.get('dataAberturaProposta')),
            False
        ),
        'relevancia': (
            lambda x: calcular_relevancia(x, termos_busca or []),
            True
        ),
    }

    key_func, reverse = sort_functions.get(
        ordenacao,
        sort_functions['data_desc']
    )

    return sorted(licitacoes, key=key_func, reverse=reverse)

def calcular_relevancia(
    licitacao: dict,
    termos: list[str]
) -> float:
    """
    Calcula score de relevância baseado nos termos de busca.

    Returns:
        Score de 0.0 a 1.0
    """
    if not termos:
        return 0.0

    texto = ' '.join([
        str(licitacao.get('objetoCompra', '')),
        str(licitacao.get('descricao', '')),
        str(licitacao.get('nomeOrgao', '')),
    ]).lower()

    matches = sum(1 for termo in termos if termo.lower() in texto)

    return matches / len(termos)
```

---

## 8. Paginação Configurável

### 8.1 Descrição Funcional

Permite ao usuário escolher quantos resultados exibir por página.

**Opções:**
- 10 por página (padrão)
- 20 por página
- 50 por página
- 100 por página

### 8.2 Implementação

Integrar com componente de paginação existente, adicionando seletor de quantidade.

---

## 9. Melhorias nos Cards de Resultado

### 9.1 Card Atual vs Proposto

**ANTES:**
```
┌─────────────────────────────────────────────────────────────┐
│ Edital nº 002/2026                                          │
│ Id: 13694658000192-1-000008/2026                            │
│ Modalidade: Pregão - Eletrônico                             │
│ Última Atualização: 05/02/2026                              │
│ Órgão: MUNICIPIO DE PIRIPA                                  │
│ Local: Piripá/BA                                            │
│ Objeto: [LICITANET] - Registro de preços para futura        │
│ eventual aquisição de fardamento (uniformes)...             │
└─────────────────────────────────────────────────────────────┘
```

**DEPOIS:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🟢 ABERTA    Pregão Eletrônico           ⏱️ 5 dias restantes │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📋 Aquisição de Uniformes Escolares                         │
│    Prefeitura Municipal de Piripá/BA                        │
│                                                             │
│ 💰 R$ 250.000,00                   📅 Abertura: 12/02/2026  │
│                                                             │
│ Registro de preços para futura eventual aquisição de        │
│ fardamento (uniformes), compreendendo peças de vestuário    │
│ padronizadas, destinadas aos servidores públicos...         │
│                                                             │
│ 🏷️ uniforme | vestuário | fardamento                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [📄 Ver Edital] [📥 Documentos] [⭐ Favoritar] [📤 Compartilhar] │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Melhorias Propostas

1. **Badge de Status Visual**
   - 🟢 Verde = Aberta/Recebendo propostas
   - 🟡 Amarelo = Em julgamento
   - 🔴 Vermelho = Encerrada
   - ⚪ Cinza = Suspensa/Cancelada

2. **Countdown para Abertura**
   - "⏱️ 5 dias" / "⏱️ 2h 30min" / "⏱️ Encerra hoje!"

3. **Título Semântico Gerado por IA**
   - Em vez de "Edital nº X", mostrar descrição curta do objeto

4. **Valor em Destaque**
   - Formatação grande e colorida

5. **Tags de Keywords**
   - Mostrar termos que matcharam com a busca

6. **Ações Rápidas**
   - Ver edital (abre no PNCP)
   - Baixar documentos
   - Favoritar
   - Compartilhar

---

## 10. Otimização de Performance

### 10.1 Problemas Identificados

| Problema | Impacto | Solução |
|----------|---------|---------|
| Busca sequencial por UF | ~4min para 27 UFs | Paralelização |
| Sem cache | Rebusca dados iguais | Redis cache |
| Excel gerado em memória | Alto uso de RAM | Streaming |
| Sem progress real | UX ruim | WebSocket |

### 10.2 Soluções Propostas

#### 10.2.1 Paralelização de Requests

```python
# backend/pncp_client.py

import asyncio
from aiohttp import ClientSession

async def buscar_todas_ufs_paralelo(
    ufs: list[str],
    params: dict,
    max_concurrent: int = 10
) -> list[dict]:
    """
    Busca licitações em múltiplas UFs em paralelo.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def buscar_com_limite(uf: str):
        async with semaphore:
            return await buscar_licitacoes_uf(uf, params)

    tasks = [buscar_com_limite(uf) for uf in ufs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten e filtrar erros
    licitacoes = []
    for result in results:
        if isinstance(result, list):
            licitacoes.extend(result)
        else:
            logger.warning(f"Erro na busca: {result}")

    return licitacoes
```

#### 10.2.2 Cache Redis

```python
# backend/cache.py

import redis
import json
from hashlib import md5

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_key(params: dict) -> str:
    """Gera chave de cache baseada nos parâmetros."""
    param_str = json.dumps(params, sort_keys=True)
    return f"busca:{md5(param_str.encode()).hexdigest()}"

def get_cached(params: dict) -> list[dict] | None:
    """Busca resultado em cache."""
    key = cache_key(params)
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_cache(params: dict, data: list[dict], ttl: int = 300):
    """Salva resultado em cache (5min TTL)."""
    key = cache_key(params)
    redis_client.setex(key, ttl, json.dumps(data))
```

---

## Conclusão

Este documento detalha todas as melhorias identificadas na análise comparativa entre PNCP e BidIQ. A implementação deve seguir a ordem de prioridade:

1. **P0 (Crítico):** Status, Modalidade, Valor
2. **P1 (Alta):** Esfera, Município, Performance
3. **P2 (Média):** Órgão, Ordenação, Paginação
4. **P3 (Baixa):** Cards, Filtros avançados

A estimativa de esforço total é de **4-6 sprints** para implementação completa.

---

**Documento gerado em:** 06/02/2026
**Versão:** 1.0
