# STORY-243: Renomear Setores para Inclusividade

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-243 |
| **Priority** | P1 |
| **Sprint** | Sprint 1 |
| **Estimate** | 4h |
| **Depends on** | STORY-249 (sync de setores) |
| **Blocks** | STORY-242 (renomear antes de adicionar novos setores) |

## Problema
O nome "Construção Civil" (setor `engenharia`, line 1182 de sectors_data.yaml) exclui escritórios de projeto, consultorias de engenharia, empresas de fiscalização e empresas de topografia. Eles não "fazem obras" mas participam de licitações de engenharia.

Outros setores também têm nomes que poderiam ser mais claros e inclusivos.

## Solução
Renomear setores no backend (sectors_data.yaml) com nomes mais inclusivos e descritivos. O frontend será atualizado via sync (STORY-249) ou manualmente.

## Investigação Técnica

### Renomeações Propostas

| Setor ID | Nome Atual | Nome Novo | Justificativa |
|----------|-----------|-----------|---------------|
| `engenharia` | "Engenharia e Construção" | "Engenharia, Projetos e Obras" | Inclui escritórios de projeto, consultorias, topografia, fiscalização |
| `facilities` | "Facilities (Limpeza e Zeladoria)" | "Facilities e Manutenção" | Mais conciso, cobre limpeza+zeladoria+jardinagem+portaria |
| `manutencao_predial` | "Manutenção Predial" | "Manutenção e Conservação Predial" | Mais descritivo, inclui conservação |
| `vigilancia` | "Vigilância e Segurança" | "Vigilância e Segurança Patrimonial" | Diferencia de segurança de TI/cibernética |
| `informatica` | "Informática e Tecnologia" | "Hardware e Equipamentos de TI" | Diferencia de Software (que é outro setor) |

### IDs NÃO mudam
Os IDs dos setores (`engenharia`, `facilities`, etc.) permanecem inalterados. Apenas `name` e `description` mudam. Isso garante:
- Perfis de usuários no Supabase que referenciam setor_id continuam válidos
- Analytics existentes por setor_id não quebram
- URLs com parâmetro `setor=` continuam funcionando

### Arquivos a Modificar

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `backend/sectors_data.yaml` | 1182-1183 | `name: "Engenharia, Projetos e Obras"`, `description` atualizada |
| `backend/sectors_data.yaml` | 1643-1644 | `name: "Facilities e Manutenção"`, description atualizada |
| `backend/sectors_data.yaml` | 2633-2634 | `name: "Manutenção e Conservação Predial"`, description atualizada |
| `backend/sectors_data.yaml` | 2276-2277 | `name: "Vigilância e Segurança Patrimonial"`, description atualizada |
| `backend/sectors_data.yaml` | 534-535 | `name: "Hardware e Equipamentos de TI"`, description atualizada |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | 59-72 | SETORES_FALLBACK nomes atualizados |
| `frontend/app/signup/page.tsx` | 12-26 | SECTORS nomes atualizados |

## Acceptance Criteria

### Backend
- [x] **AC1:** `engenharia` sector name = "Engenharia, Projetos e Obras", description inclui "escritórios de projeto, consultorias, fiscalização, topografia".
- [x] **AC2:** `facilities` sector name = "Facilities e Manutenção".
- [x] **AC3:** `manutencao_predial` sector name = "Manutenção e Conservação Predial".
- [x] **AC4:** `vigilancia` sector name = "Vigilância e Segurança Patrimonial".
- [x] **AC5:** `informatica` sector name = "Hardware e Equipamentos de TI".
- [x] **AC6:** Nenhum setor ID foi alterado (apenas name e description).
- [x] **AC7:** `list_sectors()` retorna os nomes novos.
- [x] **AC8:** Teste: `test_sector_ids_unchanged()` verifica que os mesmos IDs existem antes e depois.

### Frontend
- [x] **AC9:** SETORES_FALLBACK reflete os novos nomes.
- [x] **AC10:** Signup page SECTORS reflete os novos nomes.
- [x] **AC11:** Dropdown de setores na busca mostra os novos nomes.

### Regressão
- [x] **AC12:** Busca por setor ID `engenharia` funciona igual ao antes (keywords não mudaram).
- [x] **AC13:** Analytics por setor_id não afetados (IDs preservados).

## Definition of Done
- Todos os ACs checked
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
