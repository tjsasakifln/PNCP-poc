# Claude Code Router - Guia de Otimização para BidIQ/PNCP

## Visão Geral

O **Claude Code Router** foi configurado para otimizar automaticamente a seleção de modelos Claude baseado no tipo de tarefa, reduzindo custos e melhorando performance.

## Estratégia de Roteamento

### Modelos Disponíveis

| Modelo | Capacidade | Custo | Uso Ideal |
|--------|-----------|-------|-----------|
| **Haiku** (claude-3-5-haiku-20241022) | Rápido, eficiente | Baixo | Tarefas simples, formatação, linting |
| **Sonnet** (claude-sonnet-4-5-20250929) | Balanceado | Médio | Desenvolvimento geral, padrão |
| **Opus** (claude-opus-4-5-20251101) | Máximo poder | Alto | Arquitetura, decisões críticas |

### Regras de Roteamento Configuradas

```json
{
  "Router": {
    "default": "sonnet",           // Desenvolvimento geral
    "background": "haiku",          // Tarefas em background
    "think": "opus",                // Modo de planejamento
    "longContext": "opus",          // Contextos > 150k tokens
    "webSearch": "sonnet"           // Buscas web
  }
}
```

## Quando Cada Modelo é Usado

### 🟢 Haiku - Background Tasks (Rápido e Econômico)

**Ativado automaticamente para:**
- Tarefas de linting e formatação
- Validação de sintaxe
- Atualizações de documentação simples
- Verificações de código automatizadas
- Testes unitários básicos

**Exemplos de uso:**
```bash
ccr code "Run linting on backend/pncp_client.py"
ccr code "Format all Python files with black"
ccr code "Update simple docstrings"
```

**Especificidades do projeto:**
- Validar schemas Pydantic
- Verificar imports e exports
- Formatar código Python/TypeScript
- Executar testes rápidos (pytest -k)

### 🟡 Sonnet - Default (Desenvolvimento Geral)

**Ativado automaticamente para:**
- Implementação de features
- Code reviews
- Debugging e troubleshooting
- Refatoração moderada
- Criação de testes (pytest, jest)
- Integração com APIs externas

**Exemplos de uso:**
```bash
ccr code "Implement retry logic in PNCP client"
ccr code "Add filter for keyword matching"
ccr code "Create tests for Excel generation"
ccr code "Debug rate limiting issue"
```

**Especificidades do projeto:**
- Desenvolvimento FastAPI endpoints
- Implementação React/Next.js components
- Filtros e transformações de dados PNCP
- Integração OpenAI LLM summaries
- Geração de relatórios Excel (openpyxl)
- Testes E2E com Playwright

### 🔴 Opus - Think Mode (Raciocínio Profundo)

**Ativado automaticamente para:**
- Decisões arquiteturais
- Planejamento de features complexas
- Análise de impacto de mudanças grandes
- Refatoração de arquitetura
- Resolução de problemas complexos
- Otimização de performance crítica

**Exemplos de uso:**
```bash
ccr code "Plan architecture for caching layer"
ccr code "Analyze impact of changing PNCP pagination strategy"
ccr code "Design optimal database schema for bid tracking"
ccr code "Optimize filter.py for 100k+ bid processing"
```

**Especificidades do projeto:**
- Arquitetura de retry logic e circuit breaker
- Design de pipeline de filtros (UF → Value → Keywords → Status)
- Estratégia de rate limiting (PNCP API)
- Otimização de processamento em lote
- Decisões sobre caching (Redis vs in-memory)
- Análise de performance (100k+ licitações)

## Configuração e Ativação

### 1. Verificar Instalação

```bash
ccr --version
ccr status
```

### 2. Configurar API Key

Adicione ao `.env` (raiz do projeto):

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Iniciar Servidor

```bash
ccr start
```

### 4. Ativar Shell Integration (Opcional)

Para usar `claude` diretamente com roteamento:

```bash
eval "$(ccr activate)"
claude "Your task here"
```

### 5. Verificar Status

```bash
ccr status
ccr statusline  # Integração com statusline
```

## Uso Avançado

### Forçar Modelo Específico

Se precisar usar um modelo específico manualmente:

```bash
# Via comando model
ccr model

# Via código (custom router)
# Ver ~/.claude-code-router/custom-router.example.js
```

### Ajustar Threshold de Long Context

Modifique `config.json`:

```json
{
  "contextSize": {
    "longContextThreshold": 200000  // Aumentar para 200k tokens
  }
}
```

### Criar Presets Personalizados

```bash
# Exportar configuração atual
ccr preset export pncp-dev

# Instalar preset
ccr preset install /path/to/preset
```

## Otimizações Específicas para BidIQ/PNCP

### 1. Background Tasks (Haiku)

```bash
# Validação de dados
ccr code "Validate PNCP response schema"

# Formatação
ccr code "Format filter.py with black"

# Testes rápidos
ccr code "Run pytest -k test_uf_filter"
```

### 2. Feature Development (Sonnet)

```bash
# Implementação de filtros
ccr code "Add exclusion keywords for false positives"

# Integração API
ccr code "Implement PNCP pagination with generator pattern"

# Frontend
ccr code "Add UF multi-select component with Tailwind"
```

### 3. Arquitetura e Planejamento (Opus)

```bash
# Análise arquitetural
ccr code "Design resilient retry strategy for PNCP API"

# Otimização
ccr code "Analyze performance bottleneck in filter pipeline"

# Decisões críticas
ccr code "Evaluate Redis vs in-memory cache for download tokens"
```

## Monitoramento e Ajustes

### Logs

```bash
# Ver logs do servidor
tail -f ~/.claude-code-router/logs/server.log

# Ajustar nível de log
# Editar config.json: "LOG_LEVEL": "debug"
```

### Métricas

- **Custo por requisição:**
  - Haiku: ~$0.001/1K tokens
  - Sonnet: ~$0.015/1K tokens
  - Opus: ~$0.075/1K tokens

- **Latência esperada:**
  - Haiku: 1-3s
  - Sonnet: 3-8s
  - Opus: 8-20s

### Ajustes de Performance

```json
{
  "API_TIMEOUT_MS": 300000,  // 5 min (reduzir para tarefas rápidas)
  "LOG_LEVEL": "info"        // "debug" para troubleshooting
}
```

## Troubleshooting

### Problema: "401 Unauthorized"

**Solução:**
1. Verificar `ANTHROPIC_API_KEY` no `.env`
2. Exportar variável: `export ANTHROPIC_API_KEY=sk-ant-...`
3. Reiniciar servidor: `ccr restart`

### Problema: "Model not found"

**Solução:**
1. Verificar nomes dos modelos em `config.json`
2. Usar IDs corretos:
   - `claude-opus-4-5-20251101`
   - `claude-sonnet-4-5-20250929`
   - `claude-3-5-haiku-20241022`

### Problema: Timeout em requisições longas

**Solução:**
1. Aumentar timeout: `"API_TIMEOUT_MS": 600000` (10 min)
2. Usar `longContext` route para grandes contextos
3. Considerar usar `background` para processamento assíncrono

### Problema: Servidor não inicia

**Solução:**
```bash
ccr stop
rm -rf ~/.claude-code-router/*.pid
ccr start
```

## Integração com AIOS Framework

O Claude Code Router funciona transparentemente com os agentes AIOS:

```bash
# Ativar squad BidIQ (usa Sonnet por padrão)
/bidiq backend

# Agentes usarão roteamento automático:
# - @dev → Sonnet (implementação)
# - @architect → Opus (decisões)
# - @qa → Haiku (testes rápidos)
```

## Próximos Passos

1. **Monitorar uso:** Track custos e performance por 1 semana
2. **Ajustar thresholds:** Refinar regras baseado em padrões reais
3. **Criar presets:** Configurações para backend/frontend/testing
4. **Custom router:** JavaScript customizado para regras avançadas

## Recursos

- **Documentação oficial:** https://musistudio.github.io/claude-code-router/
- **GitHub:** https://github.com/musistudio/claude-code-router
- **Config location:** `~/.claude-code-router/config.json`
- **Logs location:** `~/.claude-code-router/logs/`

---

**Última atualização:** 2026-02-06
**Configurado por:** AIOS Framework + Claude Code
