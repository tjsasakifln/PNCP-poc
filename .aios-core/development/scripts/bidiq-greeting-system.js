#!/usr/bin/env node

/**
 * BidIQ Adaptive Greeting System
 *
 * Detects user context and proactively offers appropriate squad activation
 * Runs on session start or on file system changes
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class BidIQGreetingSystem {
  constructor() {
    this.projectRoot = process.cwd();
    this.context = null;
    this.lastSuggestion = null;
  }

  /**
   * Main entry point - detect context and offer squad
   */
  async initialize() {
    try {
      this.context = await this.detectContext();

      if (!this.context) {
        return; // Not in BidIQ project
      }

      const suggestion = await this.generateSuggestion();

      if (suggestion && suggestion !== this.lastSuggestion) {
        await this.displayGreeting(suggestion);
        this.lastSuggestion = suggestion;
      }
    } catch (error) {
      // Silent fail - don't interrupt user
    }
  }

  /**
   * Detect current context based on:
   * - Working directory
   * - Files being edited
   * - Git branch
   * - Story status
   */
  async detectContext() {
    const context = {
      type: 'unknown',
      details: {},
      suggestedSquad: null
    };

    // Check if we're in BidIQ project
    try {
      const claudeMd = await fs.readFile(path.join(this.projectRoot, 'CLAUDE.md'), 'utf8');
      if (!claudeMd.includes('BidIQ')) {
        return null;
      }
    } catch {
      return null;
    }

    // 1. Detect directory context
    const cwd = process.env.PWD || process.cwd();
    if (cwd.includes('/backend') || cwd.includes('\\backend')) {
      context.type = 'backend';
      context.suggestedSquad = 'team-bidiq-backend';
    } else if (cwd.includes('/frontend') || cwd.includes('\\frontend')) {
      context.type = 'frontend';
      context.suggestedSquad = 'team-bidiq-frontend';
    } else if (cwd.includes('/docs/stories') || cwd.includes('\\docs\\stories')) {
      context.type = 'story-creation';
      context.suggestedSquad = 'team-bidiq-feature';
    }

    // 2. Detect git branch context
    try {
      const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
      context.details.branch = branch;

      if (branch.includes('feature/')) {
        context.suggestedSquad = context.suggestedSquad || 'team-bidiq-feature';
      } else if (branch.includes('fix/')) {
        context.type = 'bugfix';
        context.suggestedSquad = 'team-bidiq-backend'; // Could be either
      }
    } catch {
      // Git not available or not a repo
    }

    // 3. Detect story status
    try {
      const storiesDir = path.join(this.projectRoot, 'docs/stories');
      const files = await fs.readdir(storiesDir);

      const activeStories = files.filter(f => {
        // Look for stories with [ ] (pending) tasks
        return f.endsWith('.md');
      });

      if (activeStories.length > 0) {
        context.details.activeStories = activeStories.length;
        if (context.suggestedSquad === null) {
          context.suggestedSquad = 'team-bidiq-feature';
        }
      }
    } catch {
      // Stories directory doesn't exist yet
    }

    // 4. Detect modified files context
    try {
      const status = execSync('git status --porcelain', { encoding: 'utf8' }).trim();
      const lines = status.split('\n').filter(l => l.trim());

      const backendFiles = lines.filter(l => l.includes('backend/'));
      const frontendFiles = lines.filter(l => l.includes('frontend/'));
      const docsFiles = lines.filter(l => l.includes('docs/'));

      context.details.modifiedFiles = {
        backend: backendFiles.length,
        frontend: frontendFiles.length,
        docs: docsFiles.length
      };

      // Suggest squad based on modified files
      if (backendFiles.length > 0 && frontendFiles.length === 0) {
        context.suggestedSquad = context.suggestedSquad || 'team-bidiq-backend';
      } else if (frontendFiles.length > 0 && backendFiles.length === 0) {
        context.suggestedSquad = context.suggestedSquad || 'team-bidiq-frontend';
      } else if (backendFiles.length > 0 && frontendFiles.length > 0) {
        context.suggestedSquad = 'team-bidiq-feature';
      }
    } catch {
      // Git status failed
    }

    return context;
  }

  /**
   * Generate greeting and suggestion based on context
   */
  async generateSuggestion() {
    if (!this.context || !this.context.suggestedSquad) {
      return null;
    }

    const squadMap = {
      'team-bidiq-backend': {
        name: 'Team BidIQ Backend',
        icon: '🐍',
        description: 'FastAPI development, PNCP client, database work',
        agents: 'architect, dev, data-engineer, qa'
      },
      'team-bidiq-frontend': {
        name: 'Team BidIQ Frontend',
        icon: '⚛️',
        description: 'React/Next.js development, UI components',
        agents: 'ux-design-expert, dev, qa'
      },
      'team-bidiq-feature': {
        name: 'Team BidIQ Feature',
        icon: '🚀',
        description: 'Complete features (backend + frontend)',
        agents: 'pm, architect, dev, qa, devops'
      }
    };

    const squad = squadMap[this.context.suggestedSquad];
    if (!squad) return null;

    return {
      squad: this.context.suggestedSquad,
      squadInfo: squad,
      context: this.context,
      confidence: this.calculateConfidence()
    };
  }

  /**
   * Calculate confidence level (0-100) for suggestion
   */
  calculateConfidence() {
    let confidence = 50; // Base confidence

    // Increase confidence based on signals
    if (this.context.type === 'backend') confidence = 90;
    if (this.context.type === 'frontend') confidence = 90;
    if (this.context.type === 'story-creation') confidence = 95;
    if (this.context.type === 'bugfix') confidence = 85;

    if (this.context.details.modifiedFiles?.backend > 3) confidence += 10;
    if (this.context.details.modifiedFiles?.frontend > 3) confidence += 10;
    if (this.context.details.activeStories > 0) confidence += 5;

    return Math.min(confidence, 100);
  }

  /**
   * Display adaptive greeting with squad suggestion
   */
  async displayGreeting(suggestion) {
    const { squadInfo, context, confidence } = suggestion;

    console.log('\n' + '─'.repeat(70));
    console.log(`${squadInfo.icon}  BidIQ Development Assistant`);
    console.log('─'.repeat(70));

    // Show context detection
    if (context.type !== 'unknown') {
      console.log(`\n📍 Detected: ${this.getContextLabel(context)}`);

      if (context.details.modifiedFiles?.backend > 0 ||
          context.details.modifiedFiles?.frontend > 0) {
        const mods = context.details.modifiedFiles;
        let fileInfo = [];
        if (mods.backend > 0) fileInfo.push(`${mods.backend} backend file(s)`);
        if (mods.frontend > 0) fileInfo.push(`${mods.frontend} frontend file(s)`);
        if (mods.docs > 0) fileInfo.push(`${mods.docs} doc(s)`);
        if (fileInfo.length > 0) {
          console.log(`   Modified: ${fileInfo.join(', ')}`);
        }
      }

      if (context.details.activeStories > 0) {
        console.log(`   Active stories: ${context.details.activeStories}`);
      }

      if (context.details.branch) {
        console.log(`   Branch: ${context.details.branch}`);
      }
    }

    // Show suggestion
    console.log(`\n💡 Recommended Squad:`);
    console.log(`   ${squadInfo.icon}  ${squadInfo.name}`);
    console.log(`   ${squadInfo.description}`);
    console.log(`   Agents: ${squadInfo.agents}`);
    console.log(`   Confidence: ${'█'.repeat(Math.round(confidence / 5))}${'░'.repeat(20 - Math.round(confidence / 5))} ${confidence}%`);

    // Show next steps
    console.log(`\n🚀 Next Steps:`);
    console.log(`   1. Type: /bidiq ${this.getSquadCommand(suggestion.squad)}`);
    console.log(`   2. Use: *help (for command reference)`);
    console.log(`   3. Start: *develop (to begin implementation)`);

    // Show help link
    console.log(`\n📖 Need help? See: docs/guides/bidiq-development-guide.md`);
    console.log('─'.repeat(70) + '\n');
  }

  /**
   * Get human-readable context label
   */
  getContextLabel(context) {
    const labels = {
      'backend': '🐍 Backend Development',
      'frontend': '⚛️ Frontend Development',
      'story-creation': '📖 Story Planning',
      'bugfix': '🐛 Bug Fix',
      'unknown': 'General Development'
    };
    return labels[context.type] || labels['unknown'];
  }

  /**
   * Get squad command (backend, frontend, feature)
   */
  getSquadCommand(squadId) {
    const map = {
      'team-bidiq-backend': 'backend',
      'team-bidiq-frontend': 'frontend',
      'team-bidiq-feature': 'feature'
    };
    return map[squadId] || 'feature';
  }
}

/**
 * Export for use as module or CLI
 */
const greeting = new BidIQGreetingSystem();

if (require.main === module) {
  // Run as CLI
  greeting.initialize().catch(console.error);
}

module.exports = BidIQGreetingSystem;
