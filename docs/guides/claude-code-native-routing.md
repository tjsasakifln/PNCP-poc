# Roteamento Automático Nativo do Claude Code (Assinatura Max)

## ✅ CONFIGURADO: Model "opusplan"

Seu Claude Code agora usa **roteamento automático inteligente**:

```json
// ~/.claude/settings.json
{
  "model": "opusplan"
}
```

## Como Funciona "opusplan"

### Automático e Inteligente

| Modo | Modelo | Quando |
|------|--------|--------|
| **Plan Mode** | Opus 4.6 | Decisões arquiteturais, análise complexa |
| **Execution Mode** | Sonnet 4.5 | Implementação de código, debugging |
| **Fallback** | Sonnet 4.5 | Se atingir limites do Opus |

### Exemplos Práticos

```bash
# Planejamento (usa Opus automaticamente)
"Plan the architecture for caching layer"
→ Claude entra em Plan Mode → Usa Opus

# Implementação (usa Sonnet automaticamente)
"Implement the caching layer"
→ Claude está em Execution Mode → Usa Sonnet

# Tasks rápidas (usa Sonnet)
"Format backend/main.py"
→ Task simples → Usa Sonnet
```

## Benefícios para BidIQ/PNCP

### Otimização Automática de Custos ✅

**Antes (tudo Sonnet):**
- Arquitetura complexa: Sonnet (não ideal)
- Implementação: Sonnet ✅
- Tasks simples: Sonnet (desperdício)

**Agora (opusplan):**
- Arquitetura complexa: **Opus** ✅ (melhor qualidade)
- Implementação: **Sonnet** ✅ (balanceado)
- Fallback inteligente: **Sonnet** (evita limites)

### Casos de Uso Específicos

#### Backend (FastAPI)

```
"Design retry strategy for PNCP API"
→ Plan Mode → Opus (decisão crítica)

"Implement the retry logic"
→ Execution → Sonnet (código)

"Add tests for retry logic"
→ Execution → Sonnet (testes)
```

#### Frontend (Next.js)

```
"Plan state management architecture"
→ Plan Mode → Opus (arquitetura)

"Implement UF selector component"
→ Execution → Sonnet (componente)

"Style with Tailwind"
→ Execution → Sonnet (styling)
```

#### Data Pipeline

```
"Analyze filter pipeline performance bottleneck"
→ Plan Mode → Opus (análise profunda)

"Optimize filter logic"
→ Execution → Sonnet (otimização)

"Benchmark improvements"
→ Execution → Sonnet (testes)
```

## Outras Opções de Modelo

### Fixos (não automáticos)

```json
// ~/.claude/settings.json

"model": "haiku"    // Sempre Haiku (rápido/barato)
"model": "sonnet"   // Sempre Sonnet (balanceado)
"model": "opus"     // Sempre Opus (máximo poder)
```

### Trocar Durante Sessão

```bash
/model haiku     # Muda para Haiku
/model sonnet    # Muda para Sonnet
/model opus      # Muda para Opus
/model opusplan  # Volta para automático
```

## Recomendações por Tipo de Trabalho

### Desenvolvimento Normal (Atual)
```json
"model": "opusplan"  ✅ CONFIGURADO
```
- Automático e inteligente
- Otimiza custos automaticamente
- Plan Mode usa Opus quando necessário

### Prototipagem Rápida
```json
"model": "sonnet"
```
- Mais rápido
- Boa qualidade
- Sem overhead do Plan Mode

### Debugging Intenso
```json
"model": "sonnet"
```
- Melhor para iterações rápidas
- Análise de código eficiente

### Decisões Arquiteturais
```bash
/model opus  # Temporariamente
# ... trabalho complexo ...
/model opusplan  # Volta ao automático
```

## Limites e Fallback (Max Plan)

O Claude Code automaticamente gerencia limites:

1. **Opus Usage Cap:** Se você usar muito Opus, fallback automático para Sonnet
2. **Rate Limits:** Gerenciados transparentemente
3. **Sem custos extras:** Incluído na assinatura Max

**Você não precisa se preocupar com billing!** 🎉

## Variáveis de Ambiente (Opcional)

Para projetos específicos:

```bash
# .env ou shell
export ANTHROPIC_MODEL=opusplan

# Ou start com modelo específico
claude --model opusplan
```

## Monitoramento

### Ver modelo atual

```bash
cat ~/.claude/settings.json | grep model
```

### Histórico de uso

Claude Code rastreia qual modelo foi usado em `~/.claude/history.jsonl`

## Comparação: Native vs CCR

| Feature | Native (opusplan) | Claude Code Router |
|---------|-------------------|---------------------|
| Setup | ✅ 1 linha | ❌ Instalação + config |
| Custos | ✅ Incluso Max | ❌ Paga por token |
| Automático | ✅ Sim | ✅ Sim |
| Controle | ⚠️ Plan/Exec only | ✅ Custom rules |
| Assinatura | ✅ Usa Max | ❌ Requer API key |

**Vencedor para você:** Native (opusplan) ✅

## Troubleshooting

### "Stuck" no Opus?

Se Claude ficar muito tempo em Opus:

```bash
/model sonnet  # Força Sonnet
# ... continua trabalho ...
/model opusplan  # Volta ao automático
```

### Quer sempre Sonnet?

```json
"model": "sonnet"
```

### Quer controle total?

Use comandos `/model` durante a sessão conforme necessário.

## Próximos Passos

1. **✅ Já configurado:** `opusplan` está ativo
2. **Teste agora:** Peça algo complexo e veja Claude entrar em Plan Mode
3. **Monitore:** Veja quando usa Opus vs Sonnet
4. **Ajuste:** Se preferir, mude para `sonnet` fixo

## Comandos Quick Reference

```bash
# Ver config atual
cat ~/.claude/settings.json

# Trocar modelo (temporário na sessão)
/model opusplan
/model sonnet
/model opus
/model haiku

# Trocar permanente
# Edite ~/.claude/settings.json → "model": "opusplan"
```

---

**Configurado em:** 2026-02-06
**Modelo ativo:** opusplan (Automático: Opus em Plan Mode, Sonnet em Execution)
**Assinatura:** Claude Max (sem custos extras de API)
**Status:** ✅ PRONTO PARA USO

## Sources

- [Using Claude Code with Max Plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- [Model Configuration - Claude Code Docs](https://code.claude.com/docs/en/model-config)
- [Claude Code Pricing 2026](https://claudelog.com/claude-code-pricing/)
- [Automatic Model Change Issue](https://github.com/anthropics/claude-code/issues/5924)
