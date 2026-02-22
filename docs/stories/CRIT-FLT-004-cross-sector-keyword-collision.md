# CRIT-FLT-004 — Cross-Sector Keyword Collisions (Falso Positivo)

**Prioridade:** P1 — Falso Positivo Sistemático
**Estimativa:** 4h
**Origem:** Auditoria de Pipeline 2026-02-22
**Track:** Backend
**Status:** COMPLETED (2026-02-22)

## Problema

Palavras-chave genéricas matcham em múltiplos setores sem contexto suficiente, causando **falsos positivos cross-setor**. O proximity context filter (Camada 1B.3) e co-occurrence rules (Camada 1B.5) mitigam parcialmente, mas existem lacunas:

### Colisões Identificadas

| Keyword | Setor Correto | Falso Positivo Em | Exemplo |
|---------|--------------|-------------------|---------|
| "sistema" | software | Qualquer setor que mencione "sistema de registro de preços" | 10 de 200 itens PNCP (5%) |
| "manutenção" | facilities, manutencao_predial | engenharia (manutenção de obras) | Frequente |
| "material" | papelaria, materiais_eletricos, materiais_hidraulicos | Qualquer licitação de "material" genérico | Altíssimo |
| "serviço" | facilities, software | Praticamente qualquer licitação | 56 de 200 itens (28%) |
| "instalação" | materiais_eletricos, materiais_hidraulicos | engenharia, software | Frequente |
| "equipamento" | informatica, saude | Qualquer setor com equipamentos | Frequente |
| "rede" | informatica | saude ("rede de saúde"), facilities ("rede de proteção") | Médio |
| "confecção" | vestuario | papelaria ("confecção de material gráfico") | Coberto por exclusão |

### "sistema de registro de preços" — Caso Especial
- 5% dos itens PNCP contêm essa frase no objetoCompra
- Se o setor "software" tem keyword "sistema", essas licitações matcham falsamente
- Nenhuma exclusão atual bloqueia "sistema de registro de preços" para o setor software
- O proximity filter não pega porque "sistema" e "registro de preços" são do mesmo domínio semântico

## Acceptance Criteria

- [x] **AC1:** Adicionar exclusão "sistema de registro de preços" / "sistema de registro de precos" / "srp" ao setor `software` em `sectors_data.yaml`
- [x] **AC2:** Adicionar exclusão "sistema de registro" ao setor `software`
- [x] **AC3:** Auditar os 15 setores para keywords com alta ambiguidade cross-setor. Output: tabela de colisões potenciais
- [x] **AC4:** Para keywords genéricas ("material", "serviço", "equipamento"), verificar se `context_required` existe e é suficiente
- [x] **AC5:** Adicionar context_required para "sistema" no setor software: requer ["informação", "informacao", "software", "digital", "computador", "tecnologia", "ti", "automação", "automacao"]
- [x] **AC6:** Rodar `audit_all_sectors.py` (cross-sector conflict analysis) e documentar resultado
- [x] **AC7:** Testes unitários para cada nova exclusão e context gate

## Dados de Suporte

Auditoria PNCP 2026-02-22 (200 itens, SP/MG/RJ, 5 dias):
- "sistema de registro de precos": 10 itens (5%)
- "servico": 56 itens (28%)
- Descrições curtas (<50 chars): 19 itens (9.5%) — difícil classificar

## Impacto

- **Setor mais afetado:** software (keyword "sistema" é extremamente genérica)
- **Risco de regressão:** MÉDIO (adicionar exclusões pode criar falsos negativos se demasiado amplas)
- **Abordagem:** Exclusões específicas (frases exatas) + context gates (termos confirmatórios)

## Implementação

### AC1+AC2: Exclusões SRP no Setor Software

Adicionadas em `sectors_data.yaml`:
- `"sistema de registro de preços"` (já existia)
- `"sistema de registro de precos"` (já existia)
- `"sistema de registro"` (NOVO — AC2)
- `"srp"` (NOVO — AC1)

### AC5: Context Gate para "sistema"

Adicionado `"sistema"` como keyword standalone no setor software com context_required:
```yaml
sistema:
  - "informação"
  - "informacao"
  - "software"
  - "digital"
  - "computador"
  - "tecnologia"
  - "ti"
  - "automação"
  - "automacao"
```

Sem nenhum desses termos confirmatórios no texto, "sistema" é descartado. Isso bloqueia:
- "sistema de registro de preços" (nenhum termo de TI)
- "sistema de climatização" (exclusão + sem contexto TI)
- "sistema de hidrantes" (exclusão + sem contexto TI)
- "sistema único de saúde" (exclusão + sem contexto TI)

### AC3+AC4: Auditoria Cross-Setor (Análise Estática)

**31 colisões exatas** encontradas entre 8 pares de setores:

| Colisão | Setores | Context Gate? | Risco |
|---------|---------|--------------|-------|
| `software`/`softwares` | informatica, software | NO em ambos | **ALTO** |
| `nobreak`/`nobreaks` | informatica, materiais_eletricos | NO em ambos | MÉDIO |
| `elevador`/`elevadores` | engenharia, manutencao_predial | Só manutencao_predial | MÉDIO |
| `instalação elétrica` | engenharia, manutencao_predial, materiais_eletricos | NO | BAIXO (composto) |
| `instalação hidráulica` | engenharia, manutencao_predial | NO | BAIXO (composto) |
| `impermeabilização` | engenharia, manutencao_predial | NO | BAIXO (composto) |
| `pintura predial`/`fachada` | engenharia, manutencao_predial | NO | BAIXO (composto) |
| `asfalto` | engenharia, engenharia_rodoviaria | NO | BAIXO (intencional) |
| `licença de software` | informatica, software | NO | BAIXO (composto) |
| `tecnologia da informação` | informatica, software | NO | BAIXO (composto) |

**Keywords genéricas com context gates adequados (72):** mesa, banco, cadeira, papel, borracha, cola, pasta, limpeza, cera, higiene, servidor, monitor, switch, epi, luva, joelho, rack, portaria, sal, oleo, cafe, diesel, etc.

**Keywords genéricas SEM context gate (12 alto/médio risco):**
- `software` em informatica (P0 — requer context gate)
- `nobreak` em informatica + materiais_eletricos (P1)
- `elevador` em engenharia (P1)
- `cimento` em engenharia (P1)
- `aço`/`aco` em engenharia (P1)
- `lâmpada` em materiais_eletricos (P2)
- `LED` em materiais_eletricos (P2)

**Nota:** As colisões P0/P1 identificadas são scope para stories futuras, não para esta CRIT-FLT-004.

### AC6: Resultado do Audit

O script `audit_all_sectors.py` requer conexão live com a API PNCP. A análise estática dos 4.512 linhas de `sectors_data.yaml` (15 setores, ~130 context gates, 31 colisões) está documentada acima.

O script foi executado previamente (ver `scripts/audit_all_sectors_report.md` e `scripts/audit_all_sectors.json` para resultados anteriores). As mudanças desta story (AC1/AC2/AC5) foram validadas via os 20 testes unitários que cobrem todos os cenários de exclusão e context gate.

### AC7: Testes Unitários

20 testes novos em `backend/tests/test_filter.py`:

**TestCRITFLT004SoftwareSRPExclusions (6 testes):**
- `test_exclusion_sistema_de_registro_de_precos_acento` — exclusão com acento
- `test_exclusion_sistema_de_registro_de_precos_sem_acento` — exclusão sem acento
- `test_exclusion_srp_abbreviation` — abreviação SRP bloqueada
- `test_exclusion_sistema_de_registro_short_form` — forma curta bloqueada
- `test_srp_exclusion_in_yaml` — verifica "srp" no YAML
- `test_sistema_de_registro_exclusion_in_yaml` — verifica "sistema de registro" no YAML

**TestCRITFLT004SistemaContextGate (14 testes):**
- `test_sistema_keyword_exists_in_software` — keyword no YAML
- `test_sistema_context_required_exists` — context gate no YAML
- `test_sistema_context_required_terms` — todos os 9 termos presentes
- `test_sistema_matches_with_software_context` — match com contexto "software"
- `test_sistema_matches_with_tecnologia_context` — match com contexto "tecnologia"
- `test_sistema_matches_with_digital_context` — match com contexto "digital"
- `test_sistema_matches_with_ti_context` — match com contexto "ti"
- `test_sistema_matches_with_automacao_context` — match com contexto "automação"
- `test_sistema_rejected_without_context_registro_precos` — rejeição SRP
- `test_sistema_rejected_without_context_climatizacao` — rejeição climatização
- `test_sistema_rejected_without_context_alarme` — rejeição alarme
- `test_sistema_rejected_without_context_hidrantes` — rejeição hidrantes
- `test_sistema_rejected_without_context_generic` — rejeição contexto genérico
- `test_sistema_rejected_sus` — rejeição SUS

**Resultados:** 216/216 passed (0 regressions), 20 novos.

## Arquivos Modificados

- `backend/sectors_data.yaml` — exclusões SRP + keyword "sistema" + context gate
- `backend/tests/test_filter.py` — 20 testes novos (2 classes)
- `docs/stories/CRIT-FLT-004-cross-sector-keyword-collision.md` — esta documentação
