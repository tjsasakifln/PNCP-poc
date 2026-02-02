#!/bin/bash
# Script de limpeza de coautoria - PNCP-POC
# Execute: bash clean-coauthorship.sh

set -e

echo "🧹 Limpando evidências de coautoria..."

# 1. Remover Co-Authored-By de arquivos markdown
echo "📄 Limpando arquivos markdown..."
find . -name "*.md" -type f -exec sed -i '/Co-Authored-By:/d' {} \;
find . -name "*.md" -type f -exec sed -i '/Squad:/d' {} \;

# 2. Remover arquivos temporários/OLD
echo "🗑️ Removendo arquivos temporários..."
find .claude -name "*-OLD.md" -delete
find .claude -name ".pr-*-review-*.md" -delete

# 3. Atualizar .gitignore para AIOS
echo "📝 Atualizando .gitignore..."
cat >> .gitignore << 'EOF'

# =============================================================================
# Development Framework Artifacts (stealth mode)
# =============================================================================
.aios-core/
.claude/
*.aios-*
*-aios-*
.ai/
EOF

# 4. Remover arquivos tracked do git
echo "🚫 Removendo arquivos AIOS do git..."
git rm -r --cached .aios-core/ 2>/dev/null || true
git rm -r --cached .claude/ 2>/dev/null || true
git rm --cached CLAUDE.md 2>/dev/null || true
git rm --cached .claude/CLAUDE.md 2>/dev/null || true

echo "✅ Limpeza de arquivos completa!"
echo ""
echo "⚠️ PRÓXIMOS PASSOS (opcional):"
echo "1. Commit as mudanças: git add . && git commit -m 'chore: cleanup project structure'"
echo "2. Se quiser reescrever histórico (CUIDADO!):"
echo "   bash rewrite-git-history.sh"
echo "3. Force push: git push origin main --force"
