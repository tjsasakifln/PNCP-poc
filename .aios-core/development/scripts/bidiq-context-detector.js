#!/usr/bin/env node

/**
 * BidIQ Context Detector
 *
 * Analyzes project state and recommends next actions
 * - Detects story progress
 * - Identifies bottlenecks
 * - Suggests next squad activation
 * - Provides actionable recommendations
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class BidIQContextDetector {
  constructor() {
    this.projectRoot = process.cwd();
  }

  /**
   * Analyze project state and provide recommendations
   */
  async analyze() {
    console.log('\n🔍 Analyzing BidIQ Project State...\n');

    const analysis = {
      git: await this.analyzeGit(),
      stories: await this.analyzeStories(),
      tests: await this.analyzeTests(),
      code: await this.analyzeCode(),
      recommendations: []
    };

    // Generate recommendations
    analysis.recommendations = this.generateRecommendations(analysis);

    return analysis;
  }

  /**
   * Analyze Git status and branches
   */
  async analyzeGit() {
    const git = {
      branch: null,
      changes: { staged: 0, unstaged: 0, untracked: 0 },
      status: null,
      commits: 0
    };

    try {
      git.branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();

      const status = execSync('git status --porcelain', { encoding: 'utf8' }).trim();
      const lines = status.split('\n').filter(l => l.trim());

      lines.forEach(line => {
        const prefix = line.substring(0, 2);
        if (['M ', 'A ', 'D ', 'R ', 'C '].includes(prefix)) git.changes.staged++;
        else if ([' M', ' D', ' T'].includes(prefix)) git.changes.unstaged++;
        else if (prefix === '??') git.changes.untracked++;
      });

      git.status = lines.length > 0 ? 'dirty' : 'clean';

      // Get commits since main
      try {
        const commitDiff = execSync('git rev-list --count main..HEAD', { encoding: 'utf8' }).trim();
        git.commits = parseInt(commitDiff) || 0;
      } catch {
        git.commits = 0;
      }
    } catch (error) {
      git.status = 'error';
    }

    return git;
  }

  /**
   * Analyze stories and their progress
   */
  async analyzeStories() {
    const stories = {
      total: 0,
      inProgress: 0,
      pending: 0,
      completed: 0,
      blocked: 0,
      details: []
    };

    try {
      const storiesDir = path.join(this.projectRoot, 'docs/stories');
      const files = await fs.readdir(storiesDir);

      for (const file of files.filter(f => f.endsWith('.md'))) {
        const content = await fs.readFile(path.join(storiesDir, file), 'utf8');

        const story = {
          name: file.replace('.md', ''),
          total: (content.match(/- \[/g) || []).length,
          completed: (content.match(/- \[x\]/gi) || []).length,
          blocked: content.includes('🔴 BLOCKED'),
          status: 'pending'
        };

        if (story.blocked) {
          story.status = 'blocked';
          stories.blocked++;
        } else if (story.completed === story.total && story.total > 0) {
          story.status = 'completed';
          stories.completed++;
        } else if (story.completed > 0) {
          story.status = 'in-progress';
          stories.inProgress++;
        } else if (story.total > 0) {
          story.status = 'pending';
          stories.pending++;
        }

        stories.total++;
        stories.details.push(story);
      }
    } catch {
      // Stories directory might not exist
    }

    return stories;
  }

  /**
   * Analyze test status
   */
  async analyzeTests() {
    const tests = {
      backend: { passing: 0, failing: 0, coverage: 0, configured: false },
      frontend: { passing: 0, failing: 0, coverage: 0, configured: false }
    };

    // Check backend tests
    try {
      const backendPath = path.join(this.projectRoot, 'backend');
      await fs.access(backendPath);

      const output = execSync('cd backend && pytest --cov --tb=no -q 2>/dev/null || true', {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      });

      tests.backend.configured = true;

      // Parse pytest output (simplified)
      const passMatch = output.match(/(\d+) passed/);
      const failMatch = output.match(/(\d+) failed/);
      const covMatch = output.match(/(\d+(?:\.\d+)?)%/);

      if (passMatch) tests.backend.passing = parseInt(passMatch[1]);
      if (failMatch) tests.backend.failing = parseInt(failMatch[1]);
      if (covMatch) tests.backend.coverage = parseFloat(covMatch[1]);
    } catch {
      // Backend tests not available
    }

    // Check frontend tests
    try {
      const frontendPath = path.join(this.projectRoot, 'frontend');
      await fs.access(frontendPath);
      tests.frontend.configured = true;
      // Frontend tests TBD (Issue #21)
    } catch {
      // Frontend not set up
    }

    return tests;
  }

  /**
   * Analyze code status
   */
  async analyzeCode() {
    const code = {
      backend: { files: 0, size: 0 },
      frontend: { files: 0, size: 0 }
    };

    // Count backend Python files
    try {
      const backendPath = path.join(this.projectRoot, 'backend');
      const files = execSync(`find "${backendPath}" -name "*.py" | wc -l`, { encoding: 'utf8' }).trim();
      code.backend.files = parseInt(files) || 0;
    } catch {
      // Backend not available
    }

    // Count frontend files
    try {
      const frontendPath = path.join(this.projectRoot, 'frontend');
      const files = execSync(`find "${frontendPath}" -name "*.{ts,tsx,js}" | wc -l`, { encoding: 'utf8' }).trim();
      code.frontend.files = parseInt(files) || 0;
    } catch {
      // Frontend not available
    }

    return code;
  }

  /**
   * Generate actionable recommendations
   */
  generateRecommendations(analysis) {
    const recs = [];

    // Git recommendations
    if (analysis.git.status === 'dirty' && analysis.git.changes.unstaged > 0) {
      recs.push({
        priority: 'high',
        type: 'git',
        message: `Unstaged changes: ${analysis.git.changes.unstaged} file(s)`,
        action: 'git add . && git commit -m "description"',
        squad: 'team-bidiq-backend' // or frontend
      });
    }

    if (analysis.git.commits > 5) {
      recs.push({
        priority: 'medium',
        type: 'git',
        message: `${analysis.git.commits} unpushed commits`,
        action: 'git push origin ' + analysis.git.branch,
        squad: 'team-bidiq-feature'
      });
    }

    // Story recommendations
    if (analysis.stories.blocked > 0) {
      recs.push({
        priority: 'critical',
        type: 'story',
        message: `${analysis.stories.blocked} blocked story(ies)`,
        action: 'Resolve blockers',
        squad: 'team-bidiq-feature'
      });
    }

    if (analysis.stories.inProgress > 0) {
      recs.push({
        priority: 'high',
        type: 'story',
        message: `${analysis.stories.inProgress} story(ies) in progress`,
        action: 'Continue implementation with /bidiq feature',
        squad: 'team-bidiq-feature'
      });
    }

    if (analysis.stories.pending > 3) {
      recs.push({
        priority: 'medium',
        type: 'story',
        message: `${analysis.stories.pending} pending stories (backlog)`,
        action: 'Select next story from backlog',
        squad: 'team-bidiq-feature'
      });
    }

    // Test recommendations
    if (analysis.tests.backend.configured && analysis.tests.backend.coverage < 70) {
      recs.push({
        priority: 'high',
        type: 'testing',
        message: `Backend coverage: ${analysis.tests.backend.coverage}% (target: 70%)`,
        action: '/bidiq backend → *run-tests',
        squad: 'team-bidiq-backend'
      });
    }

    if (analysis.tests.backend.failing > 0) {
      recs.push({
        priority: 'critical',
        type: 'testing',
        message: `${analysis.tests.backend.failing} test(s) failing`,
        action: 'Fix failing tests before merging',
        squad: 'team-bidiq-backend'
      });
    }

    return recs;
  }

  /**
   * Display analysis in readable format
   */
  displayAnalysis(analysis) {
    console.log('\n╔════════════════════════════════════════════════════════════════╗');
    console.log('║           BidIQ PROJECT STATUS & RECOMMENDATIONS              ║');
    console.log('╚════════════════════════════════════════════════════════════════╝');

    // Git status
    console.log('\n📦 GIT STATUS');
    console.log(`   Branch: ${analysis.git.branch || 'main'}`);
    console.log(`   Status: ${analysis.git.status === 'clean' ? '✅ Clean' : '⚠️  Dirty'}`);
    if (analysis.git.changes.staged > 0 || analysis.git.changes.unstaged > 0) {
      console.log(`   Changes: ${analysis.git.changes.staged} staged, ${analysis.git.changes.unstaged} unstaged`);
    }
    if (analysis.git.commits > 0) {
      console.log(`   Commits ahead of main: ${analysis.git.commits}`);
    }

    // Stories
    console.log('\n📖 STORIES');
    console.log(`   Total: ${analysis.stories.total}`);
    console.log(`   ✅ Completed: ${analysis.stories.completed}`);
    console.log(`   ⏳ In Progress: ${analysis.stories.inProgress}`);
    console.log(`   ⏸️  Pending: ${analysis.stories.pending}`);
    if (analysis.stories.blocked > 0) {
      console.log(`   🔴 Blocked: ${analysis.stories.blocked}`);
    }

    // Tests
    console.log('\n🧪 TESTS');
    if (analysis.tests.backend.configured) {
      console.log(`   Backend: ${analysis.tests.backend.passing} passing, ${analysis.tests.backend.failing} failing`);
      if (analysis.tests.backend.coverage > 0) {
        const bar = this.progressBar(analysis.tests.backend.coverage, 100);
        console.log(`   Coverage: ${bar} ${analysis.tests.backend.coverage}%`);
      }
    }
    if (analysis.tests.frontend.configured) {
      console.log(`   Frontend: Configured (tests pending)`);
    }

    // Code
    console.log('\n💻 CODE');
    if (analysis.code.backend.files > 0) {
      console.log(`   Backend: ${analysis.code.backend.files} Python files`);
    }
    if (analysis.code.frontend.files > 0) {
      console.log(`   Frontend: ${analysis.code.frontend.files} TS/JS files`);
    }

    // Recommendations
    if (analysis.recommendations.length > 0) {
      console.log('\n🎯 RECOMMENDATIONS');

      const critical = analysis.recommendations.filter(r => r.priority === 'critical');
      const high = analysis.recommendations.filter(r => r.priority === 'high');
      const medium = analysis.recommendations.filter(r => r.priority === 'medium');

      const displayRecs = (recs, icon) => {
        recs.forEach(rec => {
          console.log(`\n   ${icon} ${rec.message}`);
          console.log(`      Action: ${rec.action}`);
          if (rec.squad) {
            console.log(`      Squad: ${rec.squad}`);
          }
        });
      };

      if (critical.length > 0) {
        console.log('\n   🔴 CRITICAL:');
        displayRecs(critical, '🔴');
      }
      if (high.length > 0) {
        console.log('\n   🟠 HIGH:');
        displayRecs(high, '🟠');
      }
      if (medium.length > 0) {
        console.log('\n   🟡 MEDIUM:');
        displayRecs(medium, '🟡');
      }
    } else {
      console.log('\n✅ No issues detected!');
    }

    console.log('\n' + '═'.repeat(65) + '\n');
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
 * Export for use as module or CLI
 */
const detector = new BidIQContextDetector();

if (require.main === module) {
  // Run as CLI
  detector.analyze().then(analysis => {
    detector.displayAnalysis(analysis);
  }).catch(console.error);
}

module.exports = BidIQContextDetector;
