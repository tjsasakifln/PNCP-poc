# CRIT-021 — context_required_keywords Restritivos para Engenharia e Outros Setores

**Tipo:** Bug / Recall Loss
**Prioridade:** P0 (Contribui para 0 resultados em buscas de engenharia)
**Criada:** 2026-02-22
**Status:** Concluída
**Origem:** Investigacao P0 — busca de engenharia retornando 0 resultados
**Dependencias:** Nenhuma (pode ser feito em paralelo com CRIT-019 e CRIT-020)
**Estimativa:** XS (expansao de termos no YAML)

---

## Problema

A keyword standalone `"engenharia"` no `sectors_data.yaml:1988-1996` requer um dos seguintes termos de contexto para ser considerada valida:

```yaml
engenharia:
  - civil
  - obra
  - construcao
  - projeto
  - laudo
  - tecnico
```

### Bids Legitimas Rejeitadas

| Objeto da licitacao | Keyword match | Context match? | Resultado |
|---|---|---|---|
| "Servico de engenharia para estudos ambientais" | "engenharia" | NAO ("estudos", "ambientais" ausentes) | REJEITADA |
| "Engenharia consultiva para analise estrutural" | "engenharia" | NAO ("consultiva", "analise" ausentes) | REJEITADA |
| "Servicos de engenharia eletrica" | "engenharia" | NAO ("eletrica" ausente) | REJEITADA |
| "Engenharia mecanica industrial" | "engenharia" | NAO ("mecanica" ausente) | REJEITADA |
| "Contratacao de engenharia sanitaria" | "engenharia" | NAO ("sanitaria" ausente) | REJEITADA |
| "Engenharia de trafego e sinalizacao" | "engenharia" | NAO ("trafego" ausente) | REJEITADA |

### Outros Termos com Context Gates Restritivos

| Keyword | Contexto atual | Termos faltantes |
|---|---|---|
| `reforma` | predio, edificacao, obra, construcao, predial, escola, hospital, unidade | sala, quadra, ginasio, ponte, viaduto, muro, telhado, cobertura |
| `ferro` | construcao, obra, vergalhao, armacao, estrutura, metalurgica | barra, tubo, perfil, chapa, grade |
| `concreto` | obra, construcao, armado, usinado, estrutura, fundacao | protendido, pre-moldado, bloco, meio-fio, poste |
| `piso` | revestimento, ceramico, porcelanato, vinilico, instalacao, obra | epoxy, borracha, cimentado, polido, industrial |
| `madeira` | construcao, obra, forro, estrutura, telhado, carpintaria, marcenaria | porta, janela, ripas, caibros, tabuas, assoalho |

### Mecanismo em `filter.py`

- `match_keywords()` (L787-812): quando um keyword bate, verifica se tem `context_required` no YAML
- Se sim, busca qualquer um dos context words no texto normalizado
- Se nenhum context word encontrado, o keyword match e **descartado** (nao conta para densidade)
- Impacto: densidade cai, podendo ir de zona "LLM" para zona "auto-reject"

---

## Solucao

### Abordagem: Expandir context words para engenharia e revisar outros setores

### Criterios de Aceitacao

#### Engenharia — Keyword "engenharia"

- [x] **AC1:** Adicionar context words: `servico`, `servicos`, `consultoria`, `estudo`, `estudos`, `ambiental`, `eletrica`, `eletrico`, `hidraulica`, `mecanica`, `mecanico`, `estrutural`, `sanitaria`, `sanitario`, `trafego`, `sinalizacao`, `contratacao`, `execucao`
- [x] **AC2:** Teste com "servicos de engenharia eletrica" retorna match valido
- [x] **AC3:** Teste com "engenharia de software" continua sendo bloqueado (via exclusions, nao context)

#### Engenharia — Keyword "reforma"

- [x] **AC4:** Adicionar context words: `sala`, `quadra`, `ginasio`, `ponte`, `viaduto`, `muro`, `telhado`, `cobertura`, `fachada`, `piscina`
- [x] **AC5:** Teste com "reforma da quadra esportiva" retorna match valido

#### Engenharia — Keyword "concreto"

- [x] **AC6:** Adicionar context words: `protendido`, `pre-moldado`, `bloco`, `meio-fio`, `poste`, `laje`, `pilar`, `viga`

#### Revisao Sistemica

- [x] **AC7:** Revisar `context_required_keywords` de todos os 15 setores (nao apenas engenharia)
- [x] **AC8:** Para cada setor, verificar se ha keywords com context gates muito restritivos
- [x] **AC9:** Documentar no YAML (como comentario) a razao de cada context gate

### Verificacao Pos-Deploy

- [ ] Busca "engenharia" retorna bids com "engenharia eletrica", "engenharia ambiental", etc.
- [ ] Recall geral do setor engenharia aumenta visivelmente

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---|---|
| `backend/sectors_data.yaml` | Expandir context_required_keywords para engenharia (L1906-1996) |
| `backend/tests/test_filter.py` | Testes de context matching expandido |

---

## Notas de Implementacao

- Alteracao apenas em YAML — nao requer mudanca de codigo Python
- Cuidado para nao criar termos de contexto que gerem falsos positivos
- "engenharia de software" e "engenharia de dados" ja estao na lista de exclusions do setor — o context gate nao e a unica protecao
- Considerar se `context_required` e realmente necessario para "engenharia" dado que as exclusions ja cobrem os falsos positivos
