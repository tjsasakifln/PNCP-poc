#!/usr/bin/env node

/**
 * BidIQ Squad Exit Hooks
 *
 * Runs when user exits a squad to suggest next actions
 * - Summarizes what was accomplished
 * - Detects incomplete work
 * - Suggests next squad or action
 * - Prompts for commit if needed
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class BidIQExitHooks {
  constructor(options = {}) {
    this.projectRoot = process.cwd();
    this.squad = options.squad || 'unknown';
    this.duration = options.duration || null;
    this.accomplishments = options.accomplishments || [];
    this.issues = options.issues || [];
  }

  /**
   * Handle squad exit and suggest next steps
   */
  async onSquadExit() {
    console.log('\n' + '═'.repeat(70));
    console.log(`🔄 Exiting ${this.squad}`);
    console.log('═'.repeat(70));

    // Get current status
    const status = await this.getCurrentStatus();

    // Display summary
    await this.displayExitSummary(status);

    // Suggest next steps
    await this.suggestNextSteps(status);

    console.log('═'.repeat(70) + '\n');
  }

  /**
   * Gather current project status
   */
  async getCurrentStatus() {
    const status = {
      git: {
        changes: 0,
        uncommitted: false,
        branch: null
      },
      story: {
        active: null,
        tasksCompleted: 0,
        totalTasks: 0
      },
      tests: {
        passing: true,
        coverage: 0
      }
    };

    // Git status
    try {
      const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
      status.git.branch = branch;

      const changesOutput = execSync('git status --porcelain', { encoding: 'utf8' }).trim();
      status.git.changes = changesOutput.split('\n').filter(l => l.trim()).length;
      status.git.uncommitted = status.git.changes > 0;
    } catch {
      // Git not available
    }

    // Find active story
    try {
      const storiesDir = path.join(this.projectRoot, 'docs/stories');
      const files = await fs.readdir(storiesDir);

      for (const file of files.filter(f => f.endsWith('.md')).sort().reverse()) {
        const content = await fs.readFile(path.join(storiesDir, file), 'utf8');

        // Check if story has incomplete tasks
        const totalTasks = (content.match(/- \[/g) || []).length;
        const completed = (content.match(/- \[x\]/gi) || []).length;

        if (totalTasks > 0 && completed > 0 && completed < totalTasks) {
          status.story.active = file.replace('.md', '');
          status.story.totalTasks = totalTasks;
          status.story.tasksCompleted = completed;
          break;
        } else if (totalTasks > 0 && completed === 0) {
          status.story.active = file.replace('.md', '');
          status.story.totalTasks = totalTasks;
          status.story.tasksCompleted = 0;
          break;
        }
      }
    } catch {
      // Stories not available
    }

    // Test status
    try {
      if (this.squad.includes('backend')) {
        const output = execSync('cd backend && pytest --tb=no -q 2>/dev/null || echo "failed"', {
          encoding: 'utf8',
          stdio: ['pipe', 'pipe', 'pipe']
        });
        status.tests.passing = !output.includes('failed');

        const covMatch = output.match(/(\d+(?:\.\d+)?)%/);
        if (covMatch) status.tests.coverage = parseFloat(covMatch[1]);
      }
    } catch {
      // Tests not available
    }

    return status;
  }

  /**
   * Display exit summary
   */
  async displayExitSummary(status) {
    console.log('\n📊 SESSION SUMMARY\n');

    if (this.accomplishments.length > 0) {
      console.log('✅ Accomplishments:');
      this.accomplishments.forEach(acc => {
        console.log(`   • ${acc}`);
      });
      console.log();
    }

    if (status.story.active) {
      const progress = status.story.totalTasks > 0
        ? Math.round((status.story.tasksCompleted / status.story.totalTasks) * 100)
        : 0;
      const bar = this.progressBar(progress, 100, 30);
      console.log(`📖 Active Story: ${status.story.active}`);
      console.log(`   Progress: ${bar} ${progress}% (${status.story.tasksCompleted}/${status.story.totalTasks} tasks)`);
      console.log();
    }

    if (status.git.uncommitted) {
      console.log(`📝 Uncommitted Changes: ${status.git.changes} file(s)`);
      console.log();
    }

    if (status.tests.coverage > 0) {
      const bar = this.progressBar(status.tests.coverage, 100, 30);
      const target = this.squad.includes('backend') ? 70 : 60;
      const status_icon = status.tests.coverage >= target ? '✅' : '⚠️';
      console.log(`🧪 Test Coverage: ${status_icon} ${bar} ${status.tests.coverage}% (target: ${target}%)`);
      console.log();
    }

    if (this.issues.length > 0) {
      console.log('⚠️  Issues:');
      this.issues.forEach(issue => {
        console.log(`   • ${issue}`);
      });
      console.log();
    }

    if (this.duration) {
      console.log(`⏱️  Session Duration: ${this.duration}`);
      console.log();
    }
  }

  /**
   * Suggest next steps
   */
  async suggestNextSteps(status) {
    console.log('🎯 NEXT STEPS\n');

    const nextSteps = [];

    // Uncommitted changes
    if (status.git.uncommitted) {
      nextSteps.push({
        priority: 1,
        action: 'Commit your changes',
        command: 'git add . && git commit -m "message"',
        reason: `${status.git.changes} file(s) with uncommitted changes`
      });
    }

    // Incomplete story
    if (status.story.active && status.story.tasksCompleted < status.story.totalTasks) {
      const remaining = status.story.totalTasks - status.story.tasksCompleted;
      nextSteps.push({
        priority: 2,
        action: `Continue ${status.story.active}`,
        command: `/bidiq feature (or appropriate squad)`,
        reason: `${remaining} task(s) remaining in active story`
      });
    }

    // Test coverage
    if (status.tests.coverage > 0 && status.tests.coverage < (this.squad.includes('backend') ? 70 : 60)) {
      const target = this.squad.includes('backend') ? 70 : 60;
      nextSteps.push({
        priority: 1,
        action: 'Improve test coverage',
        command: `/bidiq ${this.getSquadType()} → *run-tests`,
        reason: `Coverage ${status.tests.coverage}% below target of ${target}%`
      });
    }

    if (nextSteps.length === 0) {
      console.log('   ✅ No immediate next steps. Ready for code review!');
      nextSteps.push({
        priority: 3,
        action: 'Create Pull Request',
        command: 'gh pr create --title "Feature/Fix description"',
        reason: 'Work appears complete'
      });
    } else {
      nextSteps.sort((a, b) => a.priority - b.priority);

      nextSteps.forEach((step, idx) => {
        const priority = {
          1: '🔴',
          2: '🟠',
          3: '🟡'
        }[step.priority];

        console.log(`${idx + 1}. ${priority} ${step.action}`);
        console.log(`   Reason: ${step.reason}`);
        console.log(`   Run: ${step.command}`);
        console.log();
      });
    }
  }

  /**
   * Get squad type from squad name
   */
  getSquadType() {
    if (this.squad.includes('backend')) return 'backend';
    if (this.squad.includes('frontend')) return 'frontend';
    return 'feature';
  }

  /**
   * Create progress bar
   */
  progressBar(current, max, width = 20) {
    const percent = Math.round((current / max) * width);
    const filled = '█'.repeat(percent);
    const empty = '░'.repeat(width - percent);
    return `[${filled}${empty}]`;
  }
}

/**
 * Export for use as module
 */
module.exports = BidIQExitHooks;

/**
 * Example usage as CLI
 */
if (require.main === module) {
  const options = {
    squad: process.argv[2] || 'team-bidiq-backend',
    duration: process.argv[3] || '45 minutes',
    accomplishments: [
      'Implemented PNCP pagination logic',
      'Added 4 new test cases',
      'Updated documentation'
    ],
    issues: []
  };

  const hooks = new BidIQExitHooks(options);
  hooks.onSquadExit().catch(console.error);
}
