# Story: Add Facilities Sector + Rebrand to SmartLic

**ID:** STORY-FACILITIES-REBRAND-001
**Epic:** Multi-Sector Expansion + White Label
**Prioridade:** High
**Squad:** Mission Squad (analyst, architect, dev, qa, devops)
**Criada:** 2026-02-02
**Status:** 🚀 In Progress

---

## 📝 **Contexto**

O BidIQ possui 8 setores de busca (vestuário, alimentos, informática, limpeza, mobiliário, papelaria, engenharia, software).

**Necessidade Dupla:**
1. **Facilities Sector:** Adicionar setor para facilities management (manutenção predial, serviços prediais, FM) - segmento importante em licitações públicas
2. **Rebranding:** Remover branding "Descomplicita" e migrar para solução white label (**SmartLic**)

**Motivação:**
- Facilities é um setor significativo de procurement público (manutenção, limpeza, segurança, recepção)
- White label permite multi-tenant deployment e profissionalização
- Eliminar dependência de marca cliente-específica

---

## 🎯 **Objetivos**

### Facilities Sector
1. Adicionar setor "facilities" com keywords abrangentes
2. Evitar overlap com setores "limpeza" e "engenharia"
3. Cobrir facilities management, manutenção predial, serviços prediais

### Rebranding
4. Remover 100% das referências "Descomplicita"
5. Implementar configuração white label via environment variables
6. Aplicar novo nome: **SmartLic** (ou alternativa aprovada)
7. Atualizar logo, favicon, meta tags, documentação

---

## ✅ **Critérios de Aceitação**

### Backend - Facilities Sector

- [ ] Nova configuração `SectorConfig` para "facilities" em `backend/sectors.py`
- [ ] Keywords específicas para facilities:
  - [ ] Facilities management, FM
  - [ ] Manutenção predial, conservação predial
  - [ ] Serviços prediais, serviços de facilities
  - [ ] Limpeza predial (diferente de produtos de limpeza)
  - [ ] Jardinagem predial
  - [ ] Recepção, portaria, segurança patrimonial
  - [ ] Copa e cozinha, alimentação corporativa
  - [ ] Gestão de utilidades (água, luz, gás)
  - [ ] Manutenção de ar condicionado (predial)
  - [ ] Manutenção elétrica predial, manutenção hidráulica predial
  - [ ] Controle de acesso, monitoramento predial
  - [ ] Manutenção preventiva, manutenção corretiva (predial)
- [ ] Exclusões para evitar falsos positivos:
  - [ ] Manutenção de equipamentos (IT/industrial)
  - [ ] Manutenção de veículos (automotive)
  - [ ] Construção civil, reforma (setor engenharia)
  - [ ] Software de facilities (setor software)
- [ ] Endpoint `/setores` retorna "facilities" na lista
- [ ] Testes unitários em `backend/tests/test_sectors.py`:
  - [ ] `test_facilities_keyword_match_success`
  - [ ] `test_facilities_keyword_exclusion`
  - [ ] `test_facilities_sector_available_in_list`
  - [ ] `test_facilities_normalization` (accents, case)
- [ ] Cobertura de testes mantida ≥70%

### Frontend - Rebranding

- [ ] Remover LOGO_URL hardcoded em `frontend/app/page.tsx:21`
- [ ] Implementar environment variables:
  - [ ] `NEXT_PUBLIC_APP_NAME` (default: "SmartLic")
  - [ ] `NEXT_PUBLIC_LOGO_URL` (default: "/logo.svg")
- [ ] Atualizar `frontend/app/layout.tsx` metadata:
  - [ ] `title`: "SmartLic - Busca Inteligente de Licitações"
  - [ ] `description`: Atualizar para remover "Descomplicita"
  - [ ] `og:title`: "SmartLic"
  - [ ] `og:site_name`: "SmartLic"
  - [ ] Remover qualquer referência a "Descomplicita"
- [ ] Adicionar logo placeholder em `frontend/public/logo.svg`
- [ ] Atualizar favicon (`frontend/public/favicon.ico`)
- [ ] Setor "Facilities" aparece no dropdown de setores
- [ ] Zero ocorrências de "descomplicita" ou "Descomplicita" no código:
  ```bash
  grep -ri "descomplicita" frontend/ backend/ docs/ --exclude-dir=node_modules --exclude-dir=htmlcov --exclude-dir=.git | grep -v CHANGELOG
  ```

### Documentation

- [ ] `CLAUDE.md` - Atualizar "Project Overview" (linha 9)
- [ ] `README.md` - Atualizar nome do projeto e descrição
- [ ] `PRD.md` - Atualizar branding guidelines
- [ ] `.env.example` - Adicionar novas variáveis:
  ```env
  NEXT_PUBLIC_APP_NAME=SmartLic
  NEXT_PUBLIC_LOGO_URL=/logo.svg
  ```
- [ ] `docs/sessions/` - Criar handoff desta missão

### Testing

- [ ] Backend tests:
  - [ ] `pytest backend/tests/test_sectors.py -v -k facilities`
  - [ ] `pytest --cov --cov-fail-under=70`
  - [ ] Validar precisão de filtro Facilities (sem falsos positivos)
- [ ] Frontend tests:
  - [ ] Jest tests para componentes atualizados
  - [ ] Cobertura mantida ≥60%
- [ ] E2E tests:
  - [ ] Fluxo completo: Selecionar Facilities → Buscar → Resultados → Download
  - [ ] Visual QA: Logo exibido corretamente (desktop + mobile)
  - [ ] Verificar meta tags no browser inspector
  - [ ] Confirmar zero "Descomplicita" na UI
- [ ] Manual QA:
  - [ ] Preview social media (og:image)
  - [ ] Favicon correto
  - [ ] Responsive logo display

### Deployment

- [ ] PR criado com descrição completa
- [ ] CI/CD pipeline pass (all tests green)
- [ ] Code review aprovado
- [ ] Production `.env` documentado:
  ```env
  NEXT_PUBLIC_APP_NAME=SmartLic
  NEXT_PUBLIC_LOGO_URL=/logo.svg  # Replace with final asset URL
  ```
- [ ] Logo final substituído (SVG placeholder → final asset)
- [ ] Smoke test em staging
- [ ] Deploy para produção
- [ ] Post-deployment monitoring (24h)

---

## 🔧 **Implementação Técnica**

### 1. Facilities Sector Keywords

**Include (manutenção predial e serviços):**
```python
keywords={
    # Facilities management core
    "facilities", "facilities management", "fm",
    "manutenção predial", "manutencao predial",
    "conservação predial", "conservacao predial",
    "serviços prediais", "servicos prediais",
    "serviços de facilities", "servicos de facilities",

    # Specific services
    "limpeza predial",
    "jardinagem predial",
    "recepção", "recepcao", "portaria",
    "segurança patrimonial", "seguranca patrimonial",
    "copa e cozinha",
    "alimentação corporativa", "alimentacao corporativa",

    # Utilities management
    "gestão de utilidades", "gestao de utilidades",
    "gestão predial", "gestao predial",

    # HVAC
    "manutenção de ar condicionado", "manutencao de ar condicionado",
    "climatização predial", "climatizacao predial",

    # Electrical/plumbing
    "manutenção elétrica predial", "manutencao eletrica predial",
    "manutenção hidráulica predial", "manutencao hidraulica predial",
    "instalações prediais", "instalacoes prediais",

    # Security/monitoring
    "controle de acesso",
    "monitoramento predial",
    "vigilância patrimonial", "vigilancia patrimonial",

    # Maintenance types
    "manutenção preventiva", "manutencao preventiva",
    "manutenção corretiva", "manutencao corretiva",
    "manutenção preditiva", "manutencao preditiva",
}
```

**Exclude (evitar overlap com outros setores):**
```python
exclusions={
    # IT/Equipment (não é facilities)
    "manutenção de equipamentos", "manutencao de equipamentos",
    "manutenção de servidor", "manutencao de servidor",
    "manutenção de computador", "manutencao de computador",
    "manutenção de impressora", "manutencao de impressora",

    # Automotive (não é predial)
    "manutenção de veículos", "manutencao de veiculos",
    "manutenção de frota", "manutencao de frota",
    "manutenção automotiva", "manutencao automotiva",

    # Construction (setor engenharia)
    "construção civil", "construcao civil",
    "reforma", "reformas",
    "ampliação", "ampliacao",
    "obra", "obras",

    # Software (setor software)
    "software de facilities",
    "sistema de facilities",
    "software de manutenção", "software de manutencao",
}
```

### 2. Rebranding Implementation

**Before (hardcoded):**
```typescript
const LOGO_URL = "https://static.wixstatic.com/media/d47bcc_9fc901ffe70149ae93fad0f461ff9565~mv2.png/v1/crop/x_0,y_301,w_5000,h_2398/fill/w_198,h_95,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Descomplicita%20-%20Azul.png";
```

**After (white label):**
```typescript
const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic";
const LOGO_URL = process.env.NEXT_PUBLIC_LOGO_URL || "/logo.svg";
```

---

## 📊 **Impact Analysis**

### Files Changed (Estimated)

**Backend (3 files):**
- `backend/sectors.py` (+50 lines)
- `backend/tests/test_sectors.py` (+40 lines)
- `backend/main.py` (0 changes, auto-updated via `list_sectors()`)

**Frontend (6 files):**
- `frontend/app/page.tsx` (-1 +3 lines)
- `frontend/app/layout.tsx` (~10 lines)
- `frontend/public/logo.svg` (new file)
- `frontend/public/favicon.ico` (replace)
- `frontend/.env.example` (+2 lines)

**Documentation (5 files):**
- `CLAUDE.md` (~5 lines)
- `README.md` (~10 lines)
- `PRD.md` (~5 lines)
- `.env.example` (+2 lines)
- `docs/sessions/session-handoff-2026-02-02.md` (new file)

**Total:** ~14 files changed, ~126 lines added/modified

---

## 🧪 **Test Plan**

### Backend Tests

```bash
# Test new Facilities sector
pytest backend/tests/test_sectors.py -v -k facilities

# Full test suite with coverage
pytest --cov --cov-fail-under=70

# Validate no regressions in other sectors
pytest backend/tests/test_sectors.py -v
```

**Expected Results:**
- 4 new test cases passing
- Overall coverage ≥70%
- All existing sectors unchanged

### Frontend Tests

```bash
# Unit tests
npm test -- --coverage --testPathPattern=page.test

# Visual regression (manual)
npm run dev
# Check logo at http://localhost:3000
# Inspect metadata in browser DevTools

# E2E tests
npm run test:e2e -- --grep "Facilities"
```

**Expected Results:**
- All tests passing
- Coverage ≥60%
- "Facilities e Manutenção Predial" in sector dropdown
- Logo displays correctly (desktop + mobile)

### Integration Test

```bash
# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Manual flow:
1. Open http://localhost:3000
2. Select "Facilities e Manutenção Predial"
3. Select UFs (e.g., SC, PR, RS)
4. Set date range (last 7 days)
5. Click "Buscar"
6. Verify results contain facilities-related bids
7. Download Excel → verify "facilities" in filename
8. Check no "Descomplicita" anywhere in UI
```

### Grep Test (Zero Occurrences)

```bash
# Search for old branding (should return 0 results except CHANGELOG)
grep -ri "descomplicita" frontend/ backend/ docs/ \
  --exclude-dir=node_modules \
  --exclude-dir=htmlcov \
  --exclude-dir=.git \
  | grep -v CHANGELOG
```

---

## 🚀 **Deployment Plan**

### Pre-Deployment Checklist

- [ ] All tests passing (backend + frontend + E2E)
- [ ] Code review approved by 2+ reviewers
- [ ] QA sign-off (manual + automated tests)
- [ ] Staging deployment successful
- [ ] Smoke test on staging (5 critical flows)
- [ ] Production `.env` variables documented
- [ ] Logo asset ready for upload (or using SVG placeholder)
- [ ] Rollback plan documented

### Deployment Steps

1. **Merge PR to main**
   ```bash
   gh pr merge --squash --delete-branch
   ```

2. **Deploy backend** (if applicable)
   ```bash
   # Backend deployment (adjust per your infra)
   git pull origin main
   cd backend && source venv/bin/activate
   pip install -r requirements.txt
   systemctl restart bidiq-backend  # or equivalent
   ```

3. **Deploy frontend**
   ```bash
   # Frontend deployment (Vercel/Netlify)
   git push origin main
   # Set environment variables in hosting dashboard:
   # NEXT_PUBLIC_APP_NAME=SmartLic
   # NEXT_PUBLIC_LOGO_URL=/logo.svg
   ```

4. **Upload logo asset** (if not using default SVG)
   ```bash
   # Upload final logo to /public/logo.svg
   # Or use CDN URL in NEXT_PUBLIC_LOGO_URL
   ```

5. **Verify deployment**
   - Check https://your-domain.com
   - Verify logo loads
   - Test Facilities sector search
   - Inspect meta tags (og:title, og:image)
   - Search for "Descomplicita" in Network tab (should be 0)

### Post-Deployment Monitoring

- [ ] Monitor error logs (24 hours)
- [ ] Check analytics for anomalies
- [ ] Verify social media preview (LinkedIn, Twitter)
- [ ] Collect user feedback on new branding

### Rollback Plan

**If Facilities sector has false positives:**
```bash
# Adjust exclusions in backend/sectors.py
git checkout -b hotfix/facilities-exclusions
# Edit exclusions
pytest backend/tests/test_sectors.py -v -k facilities
git commit -m "fix(facilities): add exclusion for X"
git push && gh pr create --fill
```

**If rebranding causes issues:**
```bash
# Revert to neutral fallback name
NEXT_PUBLIC_APP_NAME="BidIQ"
# Keep white label architecture (good for future)
# Can rebrand again later without code changes
```

---

## 📈 **Success Metrics**

### Quantitative

- [ ] Facilities sector returns ≥10 results in test search (UF=SP, last 7 days)
- [ ] False positive rate <5% (manual audit of 50 results)
- [ ] Zero "Descomplicita" occurrences in production
- [ ] Backend test coverage: ≥70%
- [ ] Frontend test coverage: ≥60%
- [ ] E2E tests: 100% passing
- [ ] Deploy without downtime (<1 min)

### Qualitative

- [ ] Logo displays professionally (desktop + mobile)
- [ ] Branding feels cohesive and modern
- [ ] Facilities keywords match domain expert validation
- [ ] Documentation is clear for future white label customization
- [ ] Code review feedback: "Clean implementation"

---

## 🔄 **Dependencies**

**Blocked By:** None (greenfield for Facilities, independent rebranding)

**Blocks:**
- Future multi-tenant deployment (requires white label)
- Client-specific branding configurations

**Related Stories:**
- STORY-SOFTWARE-001 (similar sector addition pattern)
- Feature #1 (saved searches - UI consistency)
- Feature #3 (onboarding - branding mentions)

---

## 📝 **Notes**

### Facilities Keywords - Domain Expertise

Consultar especialista em facilities management para validar keywords após implementação inicial. Possíveis fontes:
- Contratos PNCP existentes de facilities
- Normas ABNT de facilities management
- Associação Brasileira de Facilities (ABRAFAC)

### Alternative Branding Names (If Not "SmartLic")

| Name | Pros | Cons |
|------|------|------|
| SmartLic | Descriptive, searchable | Generic |
| PNCP Finder | Clear purpose | Less professional |
| BidIQ | Tech-savvy, memorable | Less descriptive |
| LicitaSmart | Portuguese, modern | May confuse non-BR users |

**Final decision:** SmartLic (can rebrand via .env later)

### Logo Design Guidelines (Future)

- Simple, scalable SVG
- Monochrome or 2-color max
- Works at 16x16px (favicon) and 200x50px (header)
- Includes text "SmartLic" or icon only (configurable)
- Use Figma/Adobe Illustrator for final asset

### YOLO Mode Justifications

- "YOLO" doesn't mean skip tests — maintain ≥70%/60% coverage
- "Move fast" means parallel work (backend + frontend simultaneously)
- Quality gates still enforced (CI/CD, code review)
- Rollback plan documented for worst-case scenarios

---

## 🏆 **Definition of Done**

- [x] Mission squad activated
- [ ] All acceptance criteria checked ✅
- [ ] Tests passing (backend ≥70%, frontend ≥60%, E2E 100%)
- [ ] Code review approved (2+ reviewers)
- [ ] QA sign-off (manual + automated)
- [ ] Documentation updated (CLAUDE.md, README, PRD)
- [ ] Deployed to production
- [ ] Smoke test passed in production
- [ ] Zero "Descomplicita" in live site
- [ ] Post-deployment monitoring (24h)
- [ ] Handoff document created (`docs/sessions/`)
- [ ] Story marked as ✅ **Completed**

---

## 📌 **Squad Activation**

```bash
# Activate mission squad
/squad-creator

# Load mission configuration
Load existing squad → "mission-facilities-rebranding"

# Start execution
@analyst: *analyze Facilities requirements
@architect: *analyze-impact
@dev: *develop backend → *develop frontend
@qa: *run-tests
@devops: *create-pr
```

**Squad Config:** `.aios-core/development/agent-teams/mission-facilities-rebranding.yaml`

---

**Story Created:** 2026-02-02 by @squad-creator
**Estimated Duration:** 5 days (YOLO mode: 3 days if parallel execution)
**Priority:** High (strategic: sector expansion + white label enablement)
