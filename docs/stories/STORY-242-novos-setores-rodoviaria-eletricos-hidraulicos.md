# STORY-242: Novos Setores — Engenharia Rodoviária, Materiais Elétricos, Materiais Hidráulicos

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-242 |
| **Priority** | P1 |
| **Sprint** | Sprint 2 |
| **Estimate** | 10h |
| **Depends on** | STORY-249 (sync de setores garante propagação correta), STORY-243 (renomear antes de adicionar) |
| **Blocks** | Nenhuma |

## Problema
Clientes de engenharia, eletricistas e fornecedores hidráulicos não encontram suas oportunidades porque os setores existentes não cobrem essas verticais. O setor "Engenharia e Construção" é genérico demais e mistura obras civis com rodovias, elétrica e hidráulica.

## Solução
Adicionar 3 novos setores em `sectors_data.yaml` com keywords curadas, exclusões e context_required_keywords. Propagação automática via STORY-249 (sync script).

## Investigação Técnica

### Setor Atual Relevante
- `engenharia` (line 1182 de sectors_data.yaml): "Engenharia e Construção" — cobre obras civis, reformas, pavimentação. Já inclui termos como "instalação elétrica" e "instalação hidráulica" nas keywords.
- **Decisão:** Os novos setores são COMPLEMENTARES, não substituem o setor `engenharia`. Keywords de overlap (ex: "instalação elétrica") podem existir em ambos — o filtro permite overlap entre setores.

### Novos Setores

#### 1. `engenharia_rodoviaria`
- **Nome:** "Engenharia Rodoviária e Infraestrutura Viária"
- **Descrição:** "Pavimentação, rodovias, pontes, viadutos, sinalização viária, conservação rodoviária"
- **max_contract_value:** null (obras rodoviárias podem ser bilionárias)
- **Keywords:** pavimentação, recapeamento, rodovia, BR-*, estrada, ponte, viaduto, sinalização viária, defensas metálicas, acostamento, terraplanagem rodoviária, conservação rodoviária, restauração rodoviária, pedágio, duplicação, faixa de rolamento, meio-fio, sarjeta, bueiro, drenagem rodoviária
- **Exclusões:** engenharia de software, rodoviária (como empresa de ônibus), passagem rodoviária, terminal rodoviário (transporte de passageiros)

#### 2. `materiais_eletricos`
- **Nome:** "Materiais Elétricos e Instalações"
- **Descrição:** "Fios, cabos, disjuntores, quadros elétricos, iluminação, subestações"
- **max_contract_value:** 20000000 (R$ 20M)
- **Keywords:** material elétrico, materiais elétricos, cabo elétrico, fio elétrico, disjuntor, quadro de distribuição, luminária, iluminação pública, LED, poste de iluminação, transformador, subestação, eletroduto, condulete, tomada, interruptor, reator, lâmpada, manutenção elétrica, instalação elétrica, rede elétrica, baixa tensão, média tensão, alta tensão
- **Exclusões:** eletrodoméstico, eletrônico, informática, computador, elétrica (como veículo elétrico)

#### 3. `materiais_hidraulicos`
- **Nome:** "Materiais Hidráulicos e Saneamento"
- **Descrição:** "Tubos, conexões, bombas, tratamento de água, esgoto, redes de distribuição"
- **max_contract_value:** 30000000 (R$ 30M)
- **Keywords:** material hidráulico, materiais hidráulicos, tubo PVC, conexão hidráulica, bomba d'água, bomba submersa, registro, válvula hidráulica, hidrômetro, caixa d'água, reservatório, saneamento, tratamento de água, tratamento de esgoto, rede de distribuição de água, rede coletora, ETA, ETE, adutora, emissário, poço artesiano, encanamento, tubulação
- **Exclusões:** hidráulica (como prensa hidráulica industrial), macaco hidráulico, plataforma hidráulica, direção hidráulica, freio hidráulico

### Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `backend/sectors_data.yaml` | Adicionar 3 novas seções (estimado ~150 linhas cada) |
| `frontend/app/signup/page.tsx` | Será atualizado automaticamente se STORY-249 cria sync para signup OU manual |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | Será atualizado via sync script OU manual |

## Acceptance Criteria

### Backend
- [ ] **AC1:** Setor `engenharia_rodoviaria` em sectors_data.yaml com ≥30 keywords, ≥15 exclusões, context_required_keywords para termos ambíguos ("estrada", "ponte").
- [ ] **AC2:** Setor `materiais_eletricos` em sectors_data.yaml com ≥25 keywords, ≥10 exclusões, max_contract_value=20000000.
- [ ] **AC3:** Setor `materiais_hidraulicos` em sectors_data.yaml com ≥25 keywords, ≥10 exclusões, max_contract_value=30000000.
- [ ] **AC4:** `sectors.py:list_sectors()` retorna os 3 novos setores (total: 15+ setores).
- [ ] **AC5:** Teste unitário: `test_new_sectors_loaded()` verifica que engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos existem em SECTORS.
- [ ] **AC6:** Teste de filtro: busca com setor `materiais_eletricos` em texto "aquisição de disjuntores" → match. Busca com mesmo setor em "aquisição de computadores" → no match.

### Frontend
- [ ] **AC7:** SETORES_FALLBACK em useSearchFilters.ts inclui os 3 novos setores.
- [ ] **AC8:** Signup page SECTORS inclui os 3 novos setores.
- [ ] **AC9:** Dropdown de setores exibe todos os novos setores corretamente (sem truncamento, com descrição clara).

### Regressão
- [ ] **AC10:** Setores existentes continuam funcionando sem alteração.
- [ ] **AC11:** Testes de filtro para setores existentes passam.

## Definition of Done
- Todos os ACs checked
- Keywords validadas contra exemplos reais do PNCP
- `pytest` sem regressões
- `npm test` sem regressões
