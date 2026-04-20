#!/usr/bin/env bash
# =============================================================================
# Legal Analyst Squad — Intake CLI
# =============================================================================
# Envia um PDF para o backend e inicia o pipeline de analise.
#
# Uso:
#   ./scripts/intake.sh /caminho/para/processo.pdf
#   ./scripts/intake.sh /caminho/para/processo.pdf --start
#
# Opcoes:
#   --start    Iniciar pipeline completo automaticamente apos upload
#
# Pre-requisito: Backend rodando (./deploy.sh local)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQUAD_DIR="$(dirname "$SCRIPT_DIR")"
API_URL="${API_URL:-http://localhost:8000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GOLD='\033[0;33m'
NC='\033[0m'

usage() {
  echo "Uso: $0 <caminho-do-pdf> [--start]"
  echo ""
  echo "  <caminho-do-pdf>  Caminho absoluto ou relativo do PDF"
  echo "  --start           Iniciar pipeline automaticamente"
  echo ""
  echo "Exemplos:"
  echo "  $0 ~/processos/acao-dano-moral.pdf"
  echo "  $0 ~/processos/recurso.pdf --start"
  echo ""
  echo "Variaveis de ambiente:"
  echo "  API_URL   URL do backend (default: http://localhost:8000)"
  exit 1
}

# ---------------------------------------------------------------------------
# Validacoes
# ---------------------------------------------------------------------------

if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  usage
fi

PDF_PATH="$1"
AUTO_START="${2:-}"

if [ ! -f "$PDF_PATH" ]; then
  echo -e "${RED}[x] Arquivo nao encontrado: $PDF_PATH${NC}"
  exit 1
fi

EXT="${PDF_PATH##*.}"
if [ "${EXT,,}" != "pdf" ]; then
  echo -e "${RED}[x] Apenas arquivos PDF sao aceitos. Extensao recebida: .$EXT${NC}"
  exit 1
fi

# Verificar se backend esta rodando
if ! curl -s "$API_URL/api/health" >/dev/null 2>&1; then
  echo -e "${YELLOW}[!] Backend nao esta rodando em $API_URL${NC}"
  echo -e "${YELLOW}    Inicie com: cd $SQUAD_DIR/webapp && ./deploy.sh local${NC}"
  echo ""

  # Fallback: copiar para pasta de uploads diretamente
  echo -e "${BLUE}[*] Copiando PDF para webapp/uploads/ como fallback...${NC}"
  UPLOAD_DIR="$SQUAD_DIR/webapp/uploads"
  mkdir -p "$UPLOAD_DIR"
  FILENAME="$(date +%Y%m%d_%H%M%S)_$(basename "$PDF_PATH")"
  cp "$PDF_PATH" "$UPLOAD_DIR/$FILENAME"
  echo -e "${GREEN}[OK] PDF copiado para: $UPLOAD_DIR/$FILENAME${NC}"
  echo ""
  echo -e "Quando o backend estiver rodando, o arquivo sera acessivel."
  echo -e "Ou use a webapp em ${BLUE}http://localhost:3000${NC} para upload interativo."
  exit 0
fi

# ---------------------------------------------------------------------------
# Enviar via API
# ---------------------------------------------------------------------------

echo -e "${GOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GOLD}║   Legal Analyst Squad — Intake CLI                   ║${NC}"
echo -e "${GOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Criar sessao
echo -e "${BLUE}[1/3] Criando sessao...${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/api/sessions")
SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)

if [ -z "$SESSION_ID" ]; then
  echo -e "${RED}[x] Falha ao criar sessao. Resposta: $SESSION_RESPONSE${NC}"
  exit 1
fi
echo -e "${GREEN}    Session ID: $SESSION_ID${NC}"

# 2. Upload do PDF
echo -e "${BLUE}[2/3] Enviando PDF: $(basename "$PDF_PATH")...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/api/documents/upload" \
  -F "file=@$PDF_PATH" \
  -H "X-Session-Id: $SESSION_ID")

DOC_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('doc_id',''))" 2>/dev/null)
PAGES=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_pages','?'))" 2>/dev/null)
PROC_NUM=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; m=json.load(sys.stdin).get('metadata',{}); print(m.get('process_number','N/I'))" 2>/dev/null)

if [ -z "$DOC_ID" ]; then
  echo -e "${RED}[x] Falha no upload. Resposta: $UPLOAD_RESPONSE${NC}"
  exit 1
fi

echo -e "${GREEN}    Doc ID: $DOC_ID${NC}"
echo -e "${GREEN}    Paginas: $PAGES${NC}"
echo -e "${GREEN}    Processo: $PROC_NUM${NC}"

# 3. Iniciar pipeline (se --start)
if [ "$AUTO_START" = "--start" ]; then
  echo -e "${BLUE}[3/3] Iniciando pipeline completo...${NC}"
  CHAT_RESPONSE=$(curl -s -X POST "$API_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"*intake\"}")

  AGENT=$(echo "$CHAT_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('agent_name',''))" 2>/dev/null)
  echo -e "${GREEN}    Agente: $AGENT${NC}"
  echo ""
  echo -e "${GREEN}Pipeline iniciado! Acompanhe pelo chat:${NC}"
  echo -e "  ${BLUE}http://localhost:3000${NC}"
else
  echo -e "${YELLOW}[3/3] Upload completo. Para iniciar o pipeline:${NC}"
  echo ""
  echo -e "  ${GOLD}Via chat:${NC} Acesse ${BLUE}http://localhost:3000${NC} e digite ${GREEN}*intake${NC}"
  echo ""
  echo -e "  ${GOLD}Via curl:${NC}"
  echo -e "  curl -X POST $API_URL/api/chat \\"
  echo -e "    -H 'Content-Type: application/json' \\"
  echo -e "    -d '{\"session_id\": \"$SESSION_ID\", \"message\": \"*intake\"}'"
fi

echo ""
echo -e "${GREEN}[OK] Processo registrado com sucesso.${NC}"
echo -e "     Session: $SESSION_ID"
echo -e "     Doc ID:  $DOC_ID"
