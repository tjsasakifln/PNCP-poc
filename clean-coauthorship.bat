@echo off
REM Script de limpeza de coautoria - Windows
REM Execute: clean-coauthorship.bat

echo 🧹 Limpando evidencias de coautoria...

REM 1. Remover arquivos markdown com Co-Authored-By
echo 📄 Limpando arquivos markdown...
powershell -Command "Get-ChildItem -Recurse -Filter *.md | ForEach-Object { (Get-Content $_.FullName) -replace 'Co-Authored-By:.*', '' -replace 'Squad:.*', '' | Set-Content $_.FullName }"

REM 2. Remover arquivos temporarios
echo 🗑️ Removendo arquivos temporarios...
if exist ".claude\*-OLD.md" del /q ".claude\*-OLD.md"
if exist ".claude\.pr-*-review-*.md" del /q ".claude\.pr-*-review-*.md"

REM 3. Atualizar .gitignore
echo 📝 Atualizando .gitignore...
echo. >> .gitignore
echo # ============================================================================= >> .gitignore
echo # Development Framework Artifacts (stealth mode) >> .gitignore
echo # ============================================================================= >> .gitignore
echo .aios-core/ >> .gitignore
echo .claude/ >> .gitignore
echo *.aios-* >> .gitignore
echo *-aios-* >> .gitignore
echo .ai/ >> .gitignore

REM 4. Remover do git
echo 🚫 Removendo arquivos AIOS do git...
git rm -r --cached .aios-core\ 2>nul
git rm -r --cached .claude\ 2>nul
git rm --cached CLAUDE.md 2>nul
git rm --cached .claude\CLAUDE.md 2>nul

echo ✅ Limpeza completa!
echo.
echo ⚠️ PROXIMOS PASSOS:
echo 1. Commit: git add . ^&^& git commit -m "chore: cleanup project structure"
echo 2. Se quiser reescrever historico: rewrite-git-history.bat
echo 3. Force push: git push origin main --force
pause
