#!/bin/bash
# Reescreve histórico do Git removendo Co-Authored-By
# ⚠️ AVISO: Isso reescreve TODO o histórico do repositório
# Execute APENAS se tiver certeza e backup!

set -e

echo "⚠️ ATENÇÃO: Você está prestes a REESCREVER o histórico do Git"
echo "Isso é uma operação IRREVERSÍVEL!"
echo ""
read -p "Tem certeza? Digite 'SIM' para continuar: " confirm

if [ "$confirm" != "SIM" ]; then
    echo "❌ Operação cancelada."
    exit 0
fi

# Verificar se git-filter-repo está instalado
if ! command -v git-filter-repo &> /dev/null; then
    echo "📦 Instalando git-filter-repo..."
    pip install git-filter-repo
fi

# Backup do branch atual
echo "💾 Criando backup..."
CURRENT_BRANCH=$(git branch --show-current)
git branch backup-before-rewrite-$(date +%Y%m%d-%H%M%S)

# Reescrever mensagens de commit
echo "✏️ Reescrevendo mensagens de commit..."
git filter-repo --message-callback '
import re
message = message.decode("utf-8")
# Remove Co-Authored-By lines
message = re.sub(r"^Co-Authored-By:.*\n?", "", message, flags=re.MULTILINE)
# Remove Squad lines
message = re.sub(r"^Squad:.*\n?", "", message, flags=re.MULTILINE)
# Remove empty lines at the end
message = message.strip()
return (message + "\n").encode("utf-8")
' --force

echo "✅ Histórico reescrito!"
echo ""
echo "📌 PRÓXIMOS PASSOS:"
echo "1. Verificar: git log --oneline -20"
echo "2. Force push: git push origin $CURRENT_BRANCH --force"
echo "3. Se algo der errado: git checkout backup-before-rewrite-*"
