@echo off
REM Reescreve histórico do Git removendo Co-Authored-By
REM ⚠️ AVISO: Operação IRREVERSÍVEL!

echo ⚠️ ATENÇÃO: Você vai REESCREVER o histórico do Git
echo Isso é IRREVERSÍVEL!
echo.
set /p confirm="Tem certeza? Digite SIM para continuar: "

if not "%confirm%"=="SIM" (
    echo ❌ Operacao cancelada.
    exit /b 0
)

REM Verificar se git-filter-repo está instalado
where git-filter-repo >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando git-filter-repo...
    pip install git-filter-repo
)

REM Backup
echo 💾 Criando backup...
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
git branch backup-before-rewrite-%date:~-4,4%%date:~-10,2%%date:~-7,2%

REM Reescrever
echo ✏️ Reescrevendo mensagens de commit...
git filter-repo --message-callback "import re; message = message.decode('utf-8'); message = re.sub(r'^Co-Authored-By:.*\n?', '', message, flags=re.MULTILINE); message = re.sub(r'^Squad:.*\n?', '', message, flags=re.MULTILINE); message = message.strip(); return (message + '\n').encode('utf-8')" --force

echo ✅ Histórico reescrito!
echo.
echo 📌 PROXIMOS PASSOS:
echo 1. Verificar: git log --oneline -20
echo 2. Force push: git push origin %CURRENT_BRANCH% --force
echo 3. Se algo der errado: git checkout backup-before-rewrite-*
pause
