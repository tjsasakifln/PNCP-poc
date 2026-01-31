# Story: Adicionar Setor "Software" nas Opções de Busca

**ID:** STORY-SOFTWARE-001
**Epic:** Multi-Sector Expansion
**Prioridade:** High
**Squad:** Full-Stack (pm, architect, dev, qa, devops)
**Criada:** 2026-01-31
**Status:** 🚀 In Progress

---

## 📝 **Contexto**

O BidIQ já possui 7 setores de busca (vestuário, alimentos, informática, limpeza, mobiliário, papelaria, engenharia). O setor "Informática e Tecnologia" atualmente inclui hardware, periféricos e software genérico.

**Necessidade:** Criar um setor **exclusivo para software** (licenças, SaaS, software customizado, desenvolvimento de sistemas) para facilitar buscas específicas de contratação de soluções de software, que possuem características diferentes de hardware de TI.

---

## 🎯 **Objetivos**

1. Adicionar novo setor "software" com keywords específicas
2. Manter setor "informatica" focado em hardware
3. Zero regressão nos setores existentes
4. Testes automatizados completos (backend + frontend + E2E)
5. Deploy sem downtime

---

## ✅ **Critérios de Aceitação**

### Backend

- [ ] Nova configuração `SectorConfig` para "software" em `backend/sectors.py`
- [ ] Keywords específicas para software:
  - Licenças (Microsoft, Adobe, ERP, CRM, etc.)
  - SaaS (plataformas cloud, assinaturas)
  - Desenvolvimento customizado (sistemas web, aplicativos)
  - Consultoria e serviços de software
- [ ] Exclusões para evitar falsos positivos:
  - Hardware de informática
  - Cursos e treinamentos
  - Manutenção de equipamentos
- [ ] Endpoint `/setores` retorna novo setor
- [ ] Testes unitários em `backend/tests/test_sectors.py`:
  - [ ] Validar keywords do novo setor
  - [ ] Validar exclusões
  - [ ] Garantir que setores existentes não foram alterados
- [ ] Testes de integração validam busca por setor "software"

### Frontend

- [ ] Dropdown de setores inclui "Software" na lista
- [ ] UI renderiza corretamente o novo setor
- [ ] Busca funciona com setor "software" selecionado
- [ ] Testes unitários em `frontend/__tests__/`:
  - [ ] Componente renderiza novo setor
  - [ ] Seleção de "software" atualiza estado corretamente
- [ ] Testes E2E em `frontend/e2e-tests/`:
  - [ ] Selecionar setor "Software" → Buscar → Validar resultados
  - [ ] Download Excel com filtro "Software"

### Qualidade

- [ ] Cobertura de testes backend: ≥70%
- [ ] Cobertura de testes frontend: ≥60%
- [ ] Zero falhas em testes E2E
- [ ] Linting passa (backend ruff, frontend eslint)
- [ ] TypeScript typecheck passa

### DevOps

- [ ] CI/CD passa (GitHub Actions)
- [ ] Build sucesso (backend + frontend)
- [ ] Deploy staging validado
- [ ] Rollback plan documentado

---

## 📐 **Arquitetura & Impacto**

### Arquivos Modificados

**Backend:**
- `backend/sectors.py` (adicionar novo setor)
- `backend/tests/test_sectors.py` (novos testes)

**Frontend:**
- Nenhuma alteração necessária (sistema dinâmico já suporta novos setores via API `/setores`)
- Apenas testes novos em `frontend/__tests__/` e `frontend/e2e-tests/`

### Dependências

- Nenhuma nova dependência
- Usa infraestrutura existente de setores

### Riscos

- **Baixo:** Sistema já projetado para múltiplos setores
- **Regressão:** Possível se keywords de "software" conflitarem com "informatica"
  - **Mitigação:** Exclusões claras + testes automatizados

---

## 🚀 **Plano de Implementação (Paralelo)**

### Wave 1 (Paralelo) - 10min

1. **@architect** - Definir keywords e exclusões do setor "software"
2. **@pm** - Validar requisitos e critérios de aceitação

### Wave 2 (Paralelo) - 15min

1. **@dev (Backend)** - Implementar novo setor em `sectors.py`
2. **@qa (Backend)** - Criar testes unitários em `test_sectors.py`

### Wave 3 (Paralelo) - 15min

1. **@dev (Backend)** - Rodar testes backend (`pytest --cov`)
2. **@qa (Frontend)** - Criar testes E2E para novo setor
3. **@devops** - Verificar CI/CD config

### Wave 4 (Sequencial) - 10min

1. **@qa (Full)** - Rodar todos os testes (backend + frontend + E2E)
2. **@devops** - Validar build e preparar deploy

### Wave 5 (Sequencial) - 5min

1. **@devops** - Criar PR e merge
2. **@devops** - Deploy staging → produção

**Tempo Total Estimado:** ~55min (execução paralela máxima)

---

## 🧪 **Estratégia de Testes**

### Testes Unitários Backend

```python
# backend/tests/test_sectors.py

def test_software_sector_exists():
    """Validate new 'software' sector exists."""
    from sectors import SECTORS
    assert "software" in SECTORS
    assert SECTORS["software"].name == "Software e Sistemas"

def test_software_keywords():
    """Validate software-specific keywords."""
    from sectors import SECTORS
    keywords = SECTORS["software"].keywords
    assert "licença" in keywords or "licenca" in keywords
    assert "saas" in keywords
    assert "desenvolvimento de software" in keywords

def test_software_exclusions():
    """Validate exclusions prevent hardware matches."""
    from sectors import SECTORS
    exclusions = SECTORS["software"].exclusions
    assert "hardware" in exclusions
    assert "impressora" in exclusions

def test_existing_sectors_unchanged():
    """Ensure adding 'software' didn't break existing sectors."""
    from sectors import SECTORS
    assert len(SECTORS) == 8  # was 7, now 8
    assert "vestuario" in SECTORS
    assert "informatica" in SECTORS
```

### Testes E2E Frontend

```typescript
// frontend/e2e-tests/software-sector.spec.ts

test('should search with software sector', async ({ page }) => {
  await page.goto('/');

  // Select software sector
  await page.selectOption('select[name="setor"]', 'software');

  // Select UF and date range
  await page.click('button:has-text("SP")');
  await page.fill('input[name="data_inicial"]', '2026-01-01');
  await page.fill('input[name="data_final"]', '2026-01-31');

  // Search
  await page.click('button:has-text("Buscar")');

  // Validate results
  await expect(page.locator('text=Software')).toBeVisible();
  await expect(page.locator('button:has-text("Download Excel")')).toBeEnabled();
});
```

---

## 🔑 **Keywords e Exclusões Propostas**

### Keywords (Software)

```python
{
    # Software licenses
    "licença de software", "licenca de software",
    "licenciamento", "licenciamento de software",
    "microsoft office", "office 365", "microsoft 365",
    "adobe", "autocad", "corel",
    "sap", "oracle", "salesforce",

    # SaaS & Cloud
    "saas", "software como serviço", "software como servico",
    "plataforma cloud", "plataforma em nuvem",
    "assinatura de software",

    # Custom development
    "desenvolvimento de software",
    "desenvolvimento de sistema",
    "sistema web", "sistema de gestão", "sistema de gestao",
    "aplicativo", "aplicativos",
    "software customizado",

    # Software services
    "consultoria de software",
    "implantação de sistema", "implantacao de sistema",
    "integração de sistema", "integracao de sistema",
    "manutenção de software", "manutencao de software",

    # Specific systems
    "erp", "crm", "bi", "business intelligence",
    "sistema de folha de pagamento",
    "sistema de protocolo",
    "sistema de almoxarifado",
    "sistema de gestão escolar", "sistema de gestao escolar",
    "sistema de gestão hospitalar", "sistema de gestao hospitalar",
}
```

### Exclusões (Software)

```python
{
    # Hardware (keep in "informatica")
    "hardware",
    "equipamento de informatica", "equipamento de informática",
    "computador", "notebook", "servidor",
    "impressora", "scanner",
    "roteador", "switch",

    # Training/courses
    "curso de software",
    "treinamento de software",
    "capacitação em software", "capacitacao em software",

    # Physical goods
    "caixa de software",  # physical boxes
    "embalagem de software",
}
```

---

## 📊 **Métricas de Sucesso**

- [ ] Build passa em CI/CD (GitHub Actions)
- [ ] Cobertura backend ≥70%
- [ ] Cobertura frontend ≥60%
- [ ] Zero regressão em setores existentes
- [ ] E2E passa em 100% dos casos
- [ ] Deploy staging OK
- [ ] Deploy produção OK

---

## 📚 **Referências**

- **Backend Sectors:** `backend/sectors.py`
- **Filter Logic:** `backend/filter.py`
- **Frontend Types:** `frontend/app/types.ts`
- **API Endpoint:** `frontend/app/api/setores/route.ts`
- **E2E Tests:** `frontend/e2e-tests/search-flow.spec.ts`

---

## 🎬 **Próximos Passos**

1. **@architect** → Revisar keywords/exclusões propostas
2. **@dev** → Implementar `sectors.py` + testes
3. **@qa** → Validar testes completos
4. **@devops** → Deploy staging → produção

---

**Squad Ready! GO GO GO! 🚀**
