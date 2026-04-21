// Posts a Lighthouse performance summary to the PR.
// Extracted from `.github/workflows/lighthouse.yml` because embedding the
// JavaScript template literal inline inside a YAML `script: |` block scalar
// caused de-indented lines (e.g. Markdown tables starting with `|` at column 1)
// to terminate the YAML block, making the workflow file invalid.

const fs = require('fs');
const path = require('path');

module.exports = async ({ github, context }) => {
  const lhciDir = 'frontend/.lighthouseci';
  if (!fs.existsSync(lhciDir)) {
    console.log('No Lighthouse results found');
    return;
  }

  const files = fs.readdirSync(lhciDir);
  const manifestFile = files.find((f) => f.startsWith('manifest'));
  if (!manifestFile) {
    console.log('No manifest found');
    return;
  }

  const manifest = JSON.parse(fs.readFileSync(path.join(lhciDir, manifestFile), 'utf8'));
  const latestRun = manifest[0];
  if (!latestRun) {
    console.log('No runs in manifest');
    return;
  }

  const resultPath = path.join(lhciDir, latestRun.jsonPath);
  const result = JSON.parse(fs.readFileSync(resultPath, 'utf8'));

  const scores = {
    performance: Math.round(result.categories.performance.score * 100),
    accessibility: Math.round(result.categories.accessibility.score * 100),
    bestPractices: Math.round(result.categories['best-practices'].score * 100),
    seo: Math.round(result.categories.seo.score * 100),
  };

  const audits = result.audits;
  const fcp = Math.round(audits['first-contentful-paint'].numericValue);
  const lcp = Math.round(audits['largest-contentful-paint'].numericValue);
  const tbt = Math.round(audits['total-blocking-time'].numericValue);
  const cls = audits['cumulative-layout-shift'].numericValue.toFixed(3);
  const si = Math.round(audits['speed-index'].numericValue);

  const scoreEmoji = (score) => {
    if (score >= 90) return '🟢';
    if (score >= 50) return '🟡';
    return '🔴';
  };

  const lines = [
    '## 🚦 Lighthouse Performance Report',
    '',
    '### Category Scores',
    '| Category | Score |',
    '|----------|-------|',
    `| ${scoreEmoji(scores.performance)} Performance | **${scores.performance}** |`,
    `| ${scoreEmoji(scores.accessibility)} Accessibility | **${scores.accessibility}** |`,
    `| ${scoreEmoji(scores.bestPractices)} Best Practices | **${scores.bestPractices}** |`,
    `| ${scoreEmoji(scores.seo)} SEO | **${scores.seo}** |`,
    '',
    '### Core Web Vitals',
    '| Metric | Value | Target |',
    '|--------|-------|--------|',
    `| First Contentful Paint (FCP) | ${fcp}ms | < 2000ms |`,
    `| Largest Contentful Paint (LCP) | ${lcp}ms | < 2500ms |`,
    `| Total Blocking Time (TBT) | ${tbt}ms | < 300ms |`,
    `| Cumulative Layout Shift (CLS) | ${cls} | < 0.1 |`,
    `| Speed Index (SI) | ${si}ms | < 3400ms |`,
    '',
    '### Performance Budget',
    `${scores.performance >= 85 ? '✅' : '❌'} Performance score meets threshold (85+)`,
    `${lcp <= 2500 ? '✅' : '❌'} LCP within budget (< 2.5s)`,
    `${cls <= 0.1 ? '✅' : '❌'} CLS within budget (< 0.1)`,
    '',
    `📊 [View full Lighthouse report in artifacts](https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId})`,
  ];
  const message = lines.join('\n');

  try {
    await github.rest.issues.createComment({
      issue_number: context.issue.number,
      owner: context.repo.owner,
      repo: context.repo.repo,
      body: message,
    });
  } catch (error) {
    console.log('Failed to post comment:', error.message);
  }
};
