#!/usr/bin/env node

/**
 * PM Command Handler
 * Extends PM agent with custom command execution
 *
 * Usage: node pm-command-handler.js --command <command> [args...]
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

class PMCommandHandler {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '../../..');
  }

  /**
   * Parse command-line arguments
   */
  parseArgs(args) {
    const result = {
      command: null,
      args: []
    };

    let i = 0;
    while (i < args.length) {
      if (args[i] === '--command') {
        result.command = args[++i];
      } else if (args[i].startsWith('--')) {
        // Skip other flags
      } else {
        result.args.push(args[i]);
      }
      i++;
    }

    return result;
  }

  /**
   * Execute status command
   */
  async executeStatus() {
    try {
      const scriptPath = path.join(
        this.projectRoot,
        '.aios-core/development/scripts/pm-project-status.js'
      );

      if (!fs.existsSync(scriptPath)) {
        console.error('❌ Status script not found');
        process.exit(1);
      }

      execSync(`node "${scriptPath}"`, {
        cwd: this.projectRoot,
        stdio: 'inherit'
      });
    } catch (error) {
      console.error('❌ Failed to execute status command:', error.message);
      process.exit(1);
    }
  }

  /**
   * Execute help command
   */
  async executeHelp() {
    const helpText = `
📋 PM Agent Commands

DOCUMENT CREATION:
  *create-prd              Create product requirements document
  *create-brownfield-prd   PRD for existing/brownfield projects
  *create-epic             Create epic for brownfield development
  *create-story            Create user story
  *doc-out                 Output complete document

STRATEGIC ANALYSIS:
  *research {topic}        Generate deep research prompt
  *correct-course          Analyze and correct deviations

PROJECT MANAGEMENT:
  *status                  Display detailed project status
  *session-info            Show current session details

DOCUMENTATION:
  *shard-prd               Break PRD into smaller parts
  *guide                   Show comprehensive usage guide

UTILITIES:
  *yolo                    Toggle confirmation skipping
  *help                    Show this help text
  *exit                    Exit PM mode

EXAMPLES:
  *status                  See current project state
  *create-prd              Start new PRD
  *research deployment     Deep dive on deployment
  *correct-course          Analyze deviations

Type command without * when in PM mode
`;
    console.log(helpText);
  }

  /**
   * Route and execute command
   */
  async execute(command, args) {
    switch (command) {
      case 'status':
        await this.executeStatus();
        break;
      case 'help':
        await this.executeHelp();
        break;
      default:
        console.error(`❌ Unknown command: ${command}`);
        console.log('\nTry: node pm-command-handler.js --command help');
        process.exit(1);
    }
  }

  /**
   * Run handler
   */
  async run() {
    const parsed = this.parseArgs(process.argv.slice(2));

    if (!parsed.command) {
      console.error('❌ No command specified\n');
      await this.executeHelp();
      process.exit(1);
    }

    await this.execute(parsed.command, parsed.args);
  }
}

// Execute
if (require.main === module) {
  const handler = new PMCommandHandler();
  handler.run().catch(error => {
    console.error('Error:', error);
    process.exit(1);
  });
}

module.exports = PMCommandHandler;
