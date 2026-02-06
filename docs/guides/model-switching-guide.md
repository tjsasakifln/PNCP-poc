# Guia Pragmático: Alternar Modelos Claude de Forma Otimizada

## Objetivo

Alternar automaticamente entre **Haiku**, **Sonnet** e **Opus 4.6** baseado no tipo de tarefa para **reduzir custos** e **maximizar performance**.

## Duas Abordagens

### 1. Native Claude Code (Mais Simples) ⭐ RECOMENDADO

O próprio Claude Code tem suporte nativo para selecionar modelos via comando:

```bash
# Alternar para Haiku (tarefas rápidas/baratas)
/model haiku

# Alternar para Sonnet (padrão, balanceado)
/model sonnet

# Alternar para Opus 4.6 (tarefas complexas)
/model opus
```

**Vantagens:**
- ✅ Zero configuração adicional
- ✅ Funciona imediatamente
- ✅ Integrado com Claude Code
- ✅ Simples e direto

**Desvantagens:**
- ❌ Manual (você precisa trocar o modelo)
- ❌ Sem roteamento automático

### 2. Claude Code Router (Automático)

Roteamento automático baseado no tipo de tarefa.

**Setup rápido:**

```bash
# 1. Já instalado ✅
ccr --version

# 2. Configurar API key no .env
echo "ANTHROPIC_API_KEY=seu-key-aqui" >> .env

# 3. Iniciar servidor
ccr start

# 4. Usar
ccr code "sua tarefa aqui"
```

**Vantagens:**
- ✅ Roteamento automático
- ✅ Otimização de custos
- ✅ Background tasks usam Haiku automaticamente
- ✅ Think mode usa Opus 4.6 automaticamente

**Desvantagens:**
- ❌ Requer configuração inicial
- ❌ Mais uma ferramenta para gerenciar

## Recomendação Pragmática

### Use Native Claude Code se:
- Você prefere controle manual
- Quer simplicidade zero-config
- Não se importa em alternar manualmente

### Use Claude Code Router se:
- Quer automação completa
- Precisa otimizar custos rigorosamente
- Roda muitas tarefas em background

## Configuração Atual (CCR)

Arquivo: `~/.claude-code-router/config.json`

```json
{
  "Router": {
    "default": "sonnet",        // Desenvolvimento geral
    "background": "haiku",       // Tarefas rápidas (formatação, testes)
    "think": "opus-4.6",         // Arquitetura, decisões complexas
    "longContext": "opus-4.6",   // Contextos grandes (>150k tokens)
    "webSearch": "sonnet"        // Buscas web
  }
}
```

## Regras de Ouro para Este Projeto

| Tarefa | Modelo | Por quê? |
|--------|--------|----------|
| Formatação, linting | **Haiku** | Rápido e barato |
| Testes unitários simples | **Haiku** | Suficiente para validação |
| Features normais (CRUD, filtros) | **Sonnet** | Balanceado custo/qualidade |
| Debugging, code review | **Sonnet** | Contexto médio |
| Arquitetura, refatoração grande | **Opus 4.6** | Raciocínio profundo |
| Análise de performance crítica | **Opus 4.6** | Decisões complexas |

## Workflow Prático

### Opção A: Manual (Native)

```bash
# Tarefa simples? Use Haiku
/model haiku
"Format backend/filter.py with black"

# Feature normal? Use Sonnet (padrão)
/model sonnet
"Implement pagination for PNCP results"

# Arquitetura? Use Opus
/model opus
"Design optimal caching strategy for PNCP data"
```

### Opção B: Automático (CCR)

```bash
# Inicie o servidor uma vez
ccr start

# Todas as tarefas usam roteamento automático
ccr code "Format backend/filter.py"           # → Haiku
ccr code "Implement pagination"               # → Sonnet
ccr code "Design caching strategy"            # → Opus (think mode)
```

## Custos Estimados (Referência)

| Modelo | Input | Output | Exemplo (10k tokens) |
|--------|-------|--------|----------------------|
| Haiku | $0.25/M | $1.25/M | ~$0.015 |
| Sonnet | $3/M | $15/M | ~$0.18 |
| Opus 4.6 | $15/M | $75/M | ~$0.90 |

**Economia potencial:** Usar Haiku para 50% das tarefas simples pode reduzir custos em 40-60%.

## Próximos Passos

1. **Decida sua abordagem:**
   - Manual? Use `/model <nome>`
   - Automático? Configure `ANTHROPIC_API_KEY` e rode `ccr start`

2. **Teste ambos por 1 semana**

3. **Meça resultados:**
   - Custo total por semana
   - Tempo médio de resposta
   - Qualidade das respostas

4. **Escolha o vencedor**

## Alternativa: Hybrid Approach

Use **Native Claude Code** como padrão, mas tenha CCR configurado para batches:

```bash
# Desenvolvimento normal (manual)
/model sonnet
"Implement feature X"

# Batch de tarefas background (automático)
ccr code "Run all linters and formatters"  # → Haiku automático
```

---

**Configurado em:** 2026-02-06
**Modelos disponíveis:** Haiku 3.5, Sonnet 4.5, Opus 4.6
**Status CCR:** Instalado ✅ | Config criada ✅ | API key pendente ⚠️
