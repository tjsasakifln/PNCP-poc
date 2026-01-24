#!/bin/bash

REPO="tjsasakifln/PNCP-poc"

echo "Criando labels..."

# Labels principais
gh label create --repo "$REPO" "epic" --color "5319E7" --description "Epic / Milestone principal"
gh label create --repo "$REPO" "infrastructure" --color "0E8A16" --description "Infraestrutura e setup"
gh label create --repo "$REPO" "backend" --color "D93F0B" --description "Backend (Python/FastAPI)"
gh label create --repo "$REPO" "frontend" --color "1D76DB" --description "Frontend (Next.js/React)"
gh label create --repo "$REPO" "feature" --color "A2EEEF" --description "Nova funcionalidade"
gh label create --repo "$REPO" "integration" --color "FBCA04" --description "Integração entre componentes"
gh label create --repo "$REPO" "testing" --color "D4C5F9" --description "Testes"
gh label create --repo "$REPO" "documentation" --color "0075CA" --description "Documentação"
gh label create --repo "$REPO" "deployment" --color "C2E0C6" --description "Deploy e CI/CD"
gh label create --repo "$REPO" "setup" --color "BFD4F2" --description "Configuração inicial"
gh label create --repo "$REPO" "configuration" --color "C5DEF5" --description "Configuração de ambiente"
gh label create --repo "$REPO" "docker" --color "0DB7ED" --description "Docker e containers"
gh label create --repo "$REPO" "api" --color "F9D0C4" --description "API REST"
gh label create --repo "$REPO" "core-logic" --color "E99695" --description "Lógica de negócio principal"
gh label create --repo "$REPO" "output" --color "FEF2C0" --description "Geração de saídas"
gh label create --repo "$REPO" "ai" --color "B60205" --description "Integração com LLM/AI"
gh label create --repo "$REPO" "enhancement" --color "84B6EB" --description "Melhoria"
gh label create --repo "$REPO" "optional" --color "EDEDED" --description "Opcional (não crítico)"

echo "✓ Labels criados com sucesso!"
