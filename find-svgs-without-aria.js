const fs = require('fs');
const path = require('path');

function findSVGsWithoutAria(dir, results = []) {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      findSVGsWithoutAria(filePath, results);
    } else if (file.endsWith('.tsx') || file.endsWith('.jsx')) {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');

      lines.forEach((line, index) => {
        // Look for <svg tags without aria-label or aria-hidden
        if (line.includes('<svg') &&
            !line.includes('aria-label') &&
            !line.includes('aria-hidden') &&
            !line.includes('role=')) {
          results.push({
            file: filePath.replace(/\\/g, '/'),
            line: index + 1,
            content: line.trim()
          });
        }
      });
    }
  }

  return results;
}

const frontendDir = path.join(__dirname, 'frontend', 'app');
const results = findSVGsWithoutAria(frontendDir);

console.log(`Found ${results.length} SVG elements without aria attributes:\n`);
results.forEach(r => {
  console.log(`${r.file}:${r.line}`);
  console.log(`  ${r.content.substring(0, 100)}${r.content.length > 100 ? '...' : ''}`);
  console.log('');
});
