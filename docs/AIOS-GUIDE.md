# Guia AIOS - PNCP POC

## O que é AIOS?

AIOS (AI-Orchestrated System) é um framework que utiliza agentes de IA especializados para auxiliar no desenvolvimento de software. Cada agente tem responsabilidades específicas e trabalha de forma coordenada.

## Agentes Disponíveis

### Agentes de Planejamento (Web UI)

- **Analyst** - Análise de requisitos
- **PM** - Product management, criação de stories
- **Architect** - Decisões arquiteturais
- **UX Expert** - Design de experiência

### Agentes de Desenvolvimento (Claude Code)

- **@sm** (Scrum Master) - Coordenação e sprint planning
- **@dev** (Developer) - Implementação de código
- **@qa** (Quality Assurance) - Testes e validação
- **@po** (Product Owner) - Priorização e aceitação

## Como Usar no Claude Code

### 1. Ativar um Agente

Digite `/AIOS/` seguido do nome do agente:

```
/AIOS/dev
/AIOS/qa
/AIOS/architect
```

### 2. Comandos Principais

#### Development (@dev)

```bash
# Implementar uma story
/AIOS/dev implement

# Code review
/AIOS/dev review

# Refatorar código
/AIOS/dev refactor
```

#### Quality Assurance (@qa)

```bash
# Executar testes
/AIOS/qa test

# Review de qualidade
/AIOS/qa review

# Gerar casos de teste
/AIOS/qa generate-tests
```

#### Scrum Master (@sm)

```bash
# Criar nova story
/AIOS/sm story

# Sprint planning
/AIOS/sm sprint

# Status report
/AIOS/sm status
```

## Workflow Recomendado

### 1. Planejamento

```
1. Ler PRD.md
2. /AIOS/architect - Revisar arquitetura
3. /AIOS/sm story - Criar stories
```

### 2. Desenvolvimento

```
1. /AIOS/dev - Ativar developer
2. Implementar código seguindo docs/framework/coding-standards.md
3. /AIOS/dev review - Auto-review
```

### 3. Quality Assurance

```
1. /AIOS/qa test - Executar testes
2. /AIOS/qa review - Review de qualidade
3. Corrigir issues identificados
```

### 4. Deploy

```
1. /AIOS/sm status - Verificar status
2. Git commit e push
3. Deploy seguindo PRD.md seção 11
```

## Estrutura de Stories

Stories são criadas em `docs/stories/` com o formato:

```markdown
# Story ID: STORY-001
# Title: Implementar PNCP Client
# Status: backlog | in-progress | completed
# Assignee: @dev

## Context
[Contexto e motivação]

## Acceptance Criteria
- [ ] Critério 1
- [ ] Critério 2

## Technical Notes
[Notas técnicas]

## Definition of Done
- [ ] Código implementado
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Code review aprovado
```

## Arquivos Importantes

### Configuração AIOS

- `.aios-core/core-config.yaml` - Configuração principal
- `.claude/commands/AIOS/agents/` - Comandos dos agentes
- `.aios/project-status.yaml` - Status do projeto

### Documentação Framework

- `docs/framework/tech-stack.md` - Stack tecnológico
- `docs/framework/source-tree.md` - Estrutura de arquivos
- `docs/framework/coding-standards.md` - Padrões de código

### Documentação Projeto

- `PRD.md` - Product Requirements Document
- `docs/architecture/` - Decisões arquiteturais
- `docs/stories/` - Stories de desenvolvimento

## Logs e Auditoria

O AIOS mantém logs de decisões em:

- `.ai/decision-logs-index.md` - Índice de decisões
- `.ai/ADR-*.md` - Architecture Decision Records
- `.aios/audit/` - Logs de auditoria

## Comandos Úteis

### Status do Projeto

```bash
# Ver status geral
/AIOS/sm status

# Ver stories ativas
ls docs/stories/

# Ver logs de decisão
cat .ai/decision-logs-index.md
```

### Gestão de Stories

```bash
# Criar nova story
/AIOS/sm story

# Listar stories
ls docs/stories/backlog/

# Mover story para in-progress
mv docs/stories/backlog/STORY-001.md docs/stories/in-progress/
```

### Quality Assurance

```bash
# Executar testes
/AIOS/qa test

# Ver relatórios de QA
ls docs/qa/
```

## Dicas

1. **Sempre ler o PRD** antes de implementar qualquer feature
2. **Seguir coding standards** em `docs/framework/coding-standards.md`
3. **Documentar decisões** importantes em ADRs
4. **Usar type hints** em Python e TypeScript
5. **Escrever testes** antes ou junto com o código
6. **Fazer commits semânticos**: `feat:`, `fix:`, `docs:`, etc.

## Troubleshooting

### Agente não responde

1. Verificar se AIOS está configurado: `ls .aios-core/`
2. Verificar se comandos existem: `ls .claude/commands/AIOS/agents/`
3. Recarregar Claude Code

### Stories não aparecem

1. Criar diretório: `mkdir -p docs/stories/backlog`
2. Verificar permissões de escrita
3. Verificar formato do arquivo

### Logs não são criados

1. Criar diretório: `mkdir -p .ai`
2. Verificar configuração em `.aios-core/core-config.yaml`
3. Habilitar decision logging

## Referências

- [AIOS Core Repository](https://github.com/tjsasakifln/aios-core)
- [User Guide](./.aios-core/user-guide.md)
- [Working in Brownfield](./.aios-core/working-in-the-brownfield.md)

## Suporte

Para dúvidas sobre o AIOS:
1. Consultar documentação em `.aios-core/`
2. Ver exemplos em `templates/`
3. Abrir issue no repositório AIOS
