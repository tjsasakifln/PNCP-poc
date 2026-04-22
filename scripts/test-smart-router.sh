#!/usr/bin/env bash
#
# Smart Router regression test — SmartLic
#
# Runs N canonical prompts through .claude/hooks/smart-router.cjs and
# validates the expected skill route is matched. Used to prevent regressions
# when adding new routes (e.g., aiox-* squads in squads-integration branch).
#
# Usage: bash scripts/test-smart-router.sh
# Exit 0: all pass. Exit 1: at least one mismatch.

set -uo pipefail

HOOK="$(dirname "$0")/../.claude/hooks/smart-router.cjs"
PASS=0
FAIL=0
FAILED_CASES=()

check() {
  local prompt="$1"
  local expected_skill="$2"
  local expected_or_empty="${3:-}"

  local actual
  actual=$(echo "{\"prompt\":\"${prompt}\"}" | node "$HOOK" 2>/dev/null)

  if [[ "$expected_skill" == "(none)" ]]; then
    if [[ -z "$actual" ]]; then
      PASS=$((PASS + 1))
      printf "  PASS  [%s] (no route — expected skip)\n" "$prompt"
    else
      FAIL=$((FAIL + 1))
      FAILED_CASES+=("$prompt → expected skip, got: $actual")
      printf "  FAIL  [%s] expected skip, got route\n" "$prompt"
    fi
    return
  fi

  # Extract the skill value from JSON using node for reliability (grep with escaped quotes is brittle).
  local extracted_skill
  extracted_skill=$(node -e "
    try {
      const o = JSON.parse(process.argv[1] || '{}');
      const ctx = (o.hookSpecificOutput && o.hookSpecificOutput.additionalContext) || '';
      const m = ctx.match(/skill:\\s\"([^\"]+)\"/);
      process.stdout.write(m ? m[1] : '');
    } catch(_) { process.stdout.write(''); }
  " "$actual" 2>/dev/null)

  if [[ "$extracted_skill" == "$expected_skill" ]]; then
    PASS=$((PASS + 1))
    printf "  PASS  [%s] → %s\n" "$prompt" "$expected_skill"
  else
    FAIL=$((FAIL + 1))
    FAILED_CASES+=("$prompt → expected '$expected_skill', got '$extracted_skill'")
    printf "  FAIL  [%s] expected %s, got %s\n" "$prompt" "$expected_skill" "${extracted_skill:-<none>}"
  fi
}

echo "=== Legacy routes (must still work after aiox-* additions) ==="
check "o login quebrou, estou com bug"                     "squad-creator"
check "preciso implementar uma nova feature"               "squad-creator"
check "integrar api do novo cliente"                       "squad-creator"
check "a busca está lenta, timeout"                        "squad-creator"
check "qual a próxima issue para fazer"                    "pick-next-issue"
check "review do PR 123"                                   "review-pr"
check "auditar roadmap"                                    "audit-roadmap"
check "preciso mudar o schema do banco de dados"           "data-engineer"
check "criar testes para o filtro"                         "qa"
check "decisão de arquitetura sobre cache"                 "architect"
check "analisar CNPJ 12345678000190 histórico de editais"  "intel-busca"
check "qual o preço médio e benchmark P50"                 "pricing-b2g"
check "participar deste edital ou não"                     "war-room-b2g"
check "monitorar novos editais radar"                      "radar-b2g"
check "relatório executivo análise profunda"               "report-b2g"
check "mapear concorrentes fornecedores players do setor"  "intel-b2g"
check "qualificar leads scoring prospects"                 "qualify-b2g"
check "cadência de prospecção follow-up sistemático"       "cadencia-b2g"
check "pipeline comercial funil forecast"                  "pipeline-b2g"
check "reter cliente upsell churn renovação"               "retention-b2g"

echo ""
echo "=== Advisory boards ==="
check "copy de texto landing page email marketing"         "copymasters"
check "cold email outreach SDR abordagem inicial"          "outreach"
check "revenue monetização unit economics"                 "turbocash"

echo ""
echo "=== aiox squads (novos) ==="
check "preciso de parecer sobre Lei 14.133"                "aiox-legal-analyst"
check "jurisprudência licitação do TCU"                    "aiox-legal-analyst"
check "impugnação do edital por habilitação"               "aiox-legal-analyst"
check "componente frontend buscar com SSE"                 "aiox-apex"
check "refactor frontend pipeline com animação"            "aiox-apex"
check "supplier_contracts query para SEO orgânico blog"    "aiox-seo"
check "programmatic SEO para observatório"                 "aiox-seo"
check "pesquisa multi-fonte dos editais"                   "aiox-deep-research"
check "deep research sobre mercado B2G"                    "aiox-deep-research"
check "paralelizar UF em batch"                            "aiox-dispatch"
check "decompor story em agentes em paralelo"              "aiox-dispatch"
check "kaizen do ecossistema"                              "aiox-kaizen-v2"
check "aprendizado contínuo via Ebbinghaus"                "aiox-kaizen-v2"

echo ""
echo "=== Skip patterns (deve NÃO rotear) ==="
check "obrigado"                                           "(none)"
check "ok"                                                 "(none)"
check "sim"                                                "(none)"
check "/comando explicito"                                 "(none)"
check "@agent-explicito"                                   "(none)"

echo ""
echo "=============================================="
echo "TOTAL: $((PASS + FAIL))"
echo "PASS:  $PASS"
echo "FAIL:  $FAIL"
echo "=============================================="

if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "Failed cases:"
  for c in "${FAILED_CASES[@]}"; do
    echo "  - $c"
  done
  exit 1
fi

echo ""
echo "✓ All router tests passed."
exit 0
