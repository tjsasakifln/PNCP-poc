#!/usr/bin/env node

/**
 * brown-disc Orchestrator
 *
 * Orquestra o workflow completo de brownfield-discovery
 * Pode ser invocado via CLI ou através de um agente AIOS
 *
 * Uso:
 *   node brown-disc-orchestrator.js [--auto]
 *   @architect *brown-disc
 */

const fs = require('fs');
const path = require('path');

class BrownDiscOrchestrator {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '../../..');
    this.workflowFile = path.join(this.projectRoot, '.aios-core/development/workflows/brownfield-discovery.yaml');
    this.outputDirs = [
      'docs/architecture',
      'docs/frontend',
      'docs/prd',
      'docs/reviews',
      'docs/reports',
      'docs/stories',
      'supabase/docs',
      '.aios/workflow-state'
    ];
    this.phases = [];
    this.currentPhase = 0;
  }

  /**
   * Inicializa o orquestrador
   */
  async initialize() {
    console.log('\n🚀 Brownfield Discovery Orchestrator v1.0\n');
    console.log('📋 Preparando para executar workflow completo...\n');

    // Criar diretórios
    this.createOutputDirectories();

    // Carregar fases
    this.loadPhases();

    // Mostrar status
    this.showStatus();
  }

  /**
   * Cria diretórios de output necessários
   */
  createOutputDirectories() {
    console.log('📁 Criando diretórios de saída...');
    this.outputDirs.forEach(dir => {
      const fullPath = path.join(this.projectRoot, dir);
      if (!fs.existsSync(fullPath)) {
        fs.mkdirSync(fullPath, { recursive: true });
        console.log(`   ✓ ${dir}`);
      }
    });
    console.log('');
  }

  /**
   * Carrega definições das fases
   */
  loadPhases() {
    this.phases = [
      {
        id: 1,
        name: 'Coleta: Sistema',
        agent: 'architect',
        task: 'document-project.md',
        command: '*document-project',
        output: 'docs/architecture/system-architecture.md',
        duration: '30-60 min',
        required: true
      },
      {
        id: 2,
        name: 'Coleta: Database',
        agent: 'data-engineer',
        task: 'db-schema-audit.md',
        command: '*db-schema-audit',
        output: 'supabase/docs/SCHEMA.md',
        duration: '20-40 min',
        conditional: 'project_has_database',
        optional: true
      },
      {
        id: 3,
        name: 'Coleta: Frontend',
        agent: 'ux-design-expert',
        task: 'audit-codebase.md',
        command: '*audit-codebase',
        output: 'docs/frontend/frontend-spec.md',
        duration: '30-45 min',
        required: true
      },
      {
        id: 4,
        name: 'Consolidação Inicial',
        agent: 'architect',
        task: 'brown-disc.md (FASE 4)',
        command: '(manual prompt)',
        output: 'docs/prd/technical-debt-DRAFT.md',
        duration: '30-45 min',
        required: true,
        manual: true
      },
      {
        id: 5,
        name: 'Validação: Database',
        agent: 'data-engineer',
        task: 'brown-disc.md (FASE 5)',
        command: '(manual review)',
        output: 'docs/reviews/db-specialist-review.md',
        duration: '20-30 min',
        conditional: 'project_has_database',
        optional: true,
        manual: true
      },
      {
        id: 6,
        name: 'Validação: UX/Frontend',
        agent: 'ux-design-expert',
        task: 'brown-disc.md (FASE 6)',
        command: '(manual review)',
        output: 'docs/reviews/ux-specialist-review.md',
        duration: '20-30 min',
        required: true,
        manual: true
      },
      {
        id: 7,
        name: 'Validação: QA Review',
        agent: 'qa',
        task: 'brown-disc.md (FASE 7)',
        command: '(manual review)',
        output: 'docs/reviews/qa-review.md',
        duration: '30-45 min',
        required: true,
        manual: true,
        gatekeeper: true
      },
      {
        id: 8,
        name: 'Assessment Final',
        agent: 'architect',
        task: 'brown-disc.md (FASE 8)',
        command: '(manual consolidation)',
        output: 'docs/prd/technical-debt-assessment.md',
        duration: '30-45 min',
        required: true,
        manual: true
      },
      {
        id: 9,
        name: 'Relatório Executivo',
        agent: 'analyst',
        task: 'brown-disc.md (FASE 9)',
        command: '(manual report)',
        output: 'docs/reports/TECHNICAL-DEBT-REPORT.md',
        duration: '30-45 min',
        required: true,
        manual: true,
        highlight: true
      },
      {
        id: 10,
        name: 'Planning: Epic + Stories',
        agent: 'pm',
        task: 'brown-disc.md (FASE 10)',
        command: '*create-epic + *create-story',
        output: 'docs/stories/epic-*.md + story-*.md',
        duration: '30-60 min',
        required: true,
        manual: true
      }
    ];
  }

  /**
   * Mostra status do workflow
   */
  showStatus() {
    console.log('📊 FASES DO WORKFLOW:\n');
    console.log('┌────┬──────────────────────┬──────────────────┬─────────┐');
    console.log('│ ID │ FASE                 │ AGENTE           │ TEMPO   │');
    console.log('├────┼──────────────────────┼──────────────────┼─────────┤');

    this.phases.forEach(phase => {
      const highlight = phase.highlight ? '⭐ ' : '';
      const optional = phase.optional ? ' [OPT]' : '';
      const gate = phase.gatekeeper ? ' [GATE]' : '';
      const id = String(phase.id).padEnd(2);
      const name = (highlight + phase.name + optional + gate).padEnd(19);
      const agent = phase.agent.padEnd(16);
      const duration = phase.duration.padEnd(7);

      console.log(`│ ${id} │ ${name} │ ${agent} │ ${duration}│`);
    });
    console.log('└────┴──────────────────────┴──────────────────┴─────────┘\n');

    console.log('⏱️  TEMPO TOTAL ESTIMADO: 4-6 horas\n');
  }

  /**
   * Mostra instruções para próxima fase
   */
  showNextPhaseInstructions() {
    if (this.currentPhase >= this.phases.length) {
      console.log('\n✅ WORKFLOW COMPLETO!\n');
      console.log('📊 SAÍDAS GERADAS:');
      console.log('  docs/');
      console.log('  ├── architecture/system-architecture.md');
      console.log('  ├── frontend/frontend-spec.md');
      console.log('  ├── prd/technical-debt-DRAFT.md');
      console.log('  ├── prd/technical-debt-assessment.md');
      console.log('  ├── reviews/db-specialist-review.md');
      console.log('  ├── reviews/ux-specialist-review.md');
      console.log('  ├── reviews/qa-review.md');
      console.log('  ├── reports/TECHNICAL-DEBT-REPORT.md ⭐');
      console.log('  └── stories/epic-*.md + story-*.md');
      console.log('  supabase/docs/SCHEMA.md + DB-AUDIT.md\n');
      return;
    }

    const phase = this.phases[this.currentPhase];
    const marker = phase.manual ? '👤' : '🤖';

    console.log(`\n${marker} FASE ${phase.id}: ${phase.name}`);
    console.log(`   Agente: @${phase.agent}`);
    console.log(`   Tempo: ${phase.duration}`);

    if (phase.manual) {
      console.log(`   Tipo: Manual (prompt especializado)`);
    } else {
      console.log(`   Comando: ${phase.command}`);
    }

    console.log(`   Output: ${phase.output}\n`);

    if (phase.gatekeeper) {
      console.log('   ⚠️  QUALITY GATE: QA precisa aprovar para continuar\n');
    }

    if (phase.optional) {
      console.log('   ℹ️  Fase condicional - pode ser pulada se não aplicável\n');
    }
  }

  /**
   * Mostra referência rápida
   */
  showQuickReference() {
    console.log('\n📖 REFERÊNCIA RÁPIDA:\n');
    console.log('Para iniciar a FASE 1:');
    console.log('  @architect *brown-disc\n');
    console.log('Para executar uma fase específica:');
    console.log('  @[agent] *[command]\n');
    console.log('Para ver o arquivo de task completo:');
    console.log('  cat .aios-core/development/tasks/brown-disc.md\n');
    console.log('Para usar o workflow YAML diretamente:');
    console.log('  @aios-master *workflow brownfield-discovery\n');
  }

  /**
   * Executa o orquestrador
   */
  async run(autoMode = false) {
    await this.initialize();
    this.showStatus();
    this.showNextPhaseInstructions();
    this.showQuickReference();

    if (autoMode) {
      console.log('\n🎯 AUTO MODE: Siga as instruções acima para cada fase.\n');
    }
  }
}

// Main execution
const args = process.argv.slice(2);
const autoMode = args.includes('--auto');

const orchestrator = new BrownDiscOrchestrator();
orchestrator.run(autoMode).catch(error => {
  console.error('❌ Erro:', error.message);
  process.exit(1);
});
