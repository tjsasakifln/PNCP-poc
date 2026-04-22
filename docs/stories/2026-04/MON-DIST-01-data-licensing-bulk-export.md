# MON-DIST-01: Data Licensing / Bulk Export (Pacotes Temáticos One-Shot)

**Priority:** P2
**Effort:** L (5-6 dias)
**Squad:** @dev + @devops + @pm
**Status:** Draft
**Epic:** [EPIC-MON-DIST-2026-04](EPIC-MON-DIST-2026-04.md)
**Sprint:** Wave 3 (depende MON-REP-01)

---

## Contexto

Compradores **enterprise** (consultorias estratégicas, universidades, think tanks, M&A advisors) precisam do dataset **temático em bulk** para análise offline (Python/R/Excel) — não querem API nem relatórios PDF. Querem CSV/JSON/Parquet.

**Modelo:** catálogo de pacotes pré-montados + pacotes on-demand customizados. Checkout reutiliza MON-REP-01.

**Exemplos de pacotes iniciais:**
- "Construção Civil SP 2020-2025" (~500k contratos, R$ 9.997)
- "TI Federal 2023-2025" (~150k contratos, R$ 4.997)
- "Limpeza Municipal Nordeste 2021-2025" (~300k contratos, R$ 6.997)
- "Top 100 Fornecedores por Setor" (R$ 2.997 por setor)

**Upsell:** assinatura "Data Feed Mensal" (delta de novos contratos no recorte, R$ 997/mês) — considerar em v2.

---

## Acceptance Criteria

### AC1: Tabela `data_packages` + admin UI

- [ ] Migração:
```sql
CREATE TABLE public.data_packages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  description text NOT NULL,
  filters jsonb NOT NULL,  -- {setor, ufs, periodo_inicio, periodo_fim, modalidades, ...}
  price_cents int NOT NULL,
  row_count_est int NOT NULL,
  formats text[] NOT NULL DEFAULT ARRAY['csv','json','parquet'],
  schema_doc_url text NULL,  -- link para docs.smartlic.tech/data-packages/{slug}
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
```
- [ ] Admin UI `/admin/data-packages` para CRUD de pacotes
- [ ] Seed inicial com 10 pacotes em `scripts/seed_data_packages.py`

### AC2: Gerador async de bulk export

- [ ] `backend/services/bulk_export.py`:
  - Input: `package_id` ou `custom_filters`, `formato`
  - Streaming export: `COPY TO STDOUT` do PostgreSQL para arquivo temporário
  - Formato Parquet via `pyarrow` (mais leve que CSV para dados numéricos)
  - Upload ao Supabase Storage (bucket `data-exports`, TTL 7 dias)
  - Geração pode levar 2-15 min dependendo do tamanho

### AC3: Checkout + entrega

- [ ] Reutiliza MON-REP-01: `POST /v1/purchases/checkout` com `product_type='data_package'`, `product_params: {package_id, formato}`
- [ ] Após payment: ARQ job `generate_data_package` invoca bulk_export, persiste em `generated_reports` (reutiliza infra MON-REP-02)
- [ ] Email específico `data_package_ready.py` com link signed URL 7 dias

### AC4: Landing `/dados-empresariais`

- [ ] `frontend/app/dados-empresariais/page.tsx`:
  - Hero: "Licença Enterprise de Dados de Contratações Públicas"
  - Grid de 10+ pacotes (filtrar por setor)
  - Cada card: nome, descrição, row count, preço, formatos, "Ver schema"
  - Botão "Solicitar pacote custom" → form que gera lead (email p/ equipe + opcional checkout direto)
  - Seção "FAQ": formato, licença (CC-BY 4.0 + termos SmartLic), uso permitido (comercial OK, redistribuição não), atualização

### AC5: Termos de uso

- [ ] `docs/legal/data-license-terms.md`:
  - Uso comercial e acadêmico permitido
  - Redistribuição não permitida (client-specific license)
  - Fonte original: PNCP (obrigatório citar)
  - Rights reserved SmartLic para dados derivados (score, classificação IA)
- [ ] Checkbox obrigatório no checkout: "Li e aceito os termos"

### AC6: Analytics

- [ ] Prometheus: `smartlic_data_packages_sold_total{package_slug}`, `smartlic_data_packages_revenue_cents_total`
- [ ] Top N pacotes mais vendidos → destaque na landing

### AC7: Testes

- [ ] Unit: `test_bulk_export.py` — export de 1k rows para 3 formatos, validar schemas
- [ ] Integration: purchase → job → file generated → download funciona
- [ ] Performance: pacote 500k rows gera em <15 min

---

## Scope

**IN:**
- Tabela + admin UI
- Gerador bulk export (3 formatos)
- Checkout + delivery (reutiliza MON-REP-01/02)
- Landing + FAQ + termos
- Seed 10 pacotes iniciais
- Testes

**OUT:**
- Pacotes recorrentes / data feed mensal — v2
- API B2B de data license — cobre MON-API-05 (RapidAPI) com tier enterprise custom
- White-label do dataset — fora de escopo (overlap com MON-DIST-02)

---

## Dependências

- MON-REP-01 (checkout one-shot)
- MON-REP-02 (delivery infra)
- Dados `pncp_supplier_contracts` populados (já existem)

---

## Riscos

- **Cliente reivindica redistribuição:** termos claros + audit log por signed URL download
- **Export muito grande trava worker:** limit 1M rows por pacote; se > solicitar Enterprise custom
- **Compliance LGPD para datasets com CNPJs:** dados públicos (lei transparência); incluir campo de opt-out para CNPJs que solicitarem (raríssimo)

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_data_packages.sql` + `.down.sql`
- `backend/services/bulk_export.py` (novo)
- `backend/jobs/data_package_generation.py` (novo)
- `backend/templates/emails/data_package_ready.py` (novo)
- `scripts/seed_data_packages.py` (novo)
- `backend/routes/data_packages.py` (novo — admin + public)
- `backend/routes/admin_data_packages.py` (novo)
- `frontend/app/dados-empresariais/page.tsx` (novo)
- `frontend/app/admin/data-packages/page.tsx` (novo)
- `docs/legal/data-license-terms.md` (novo)
- `backend/tests/services/test_bulk_export.py` (novo)

---

## Definition of Done

- [ ] 10 pacotes seeded em prod
- [ ] Landing live com pacotes visíveis
- [ ] Test purchase: compra Parquet → download funciona → arquivo válido em pandas
- [ ] Termos de uso publicados + aceite obrigatório
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — canal enterprise one-shot; extras de distribuição |
