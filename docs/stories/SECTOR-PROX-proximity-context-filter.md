# SECTOR-PROX: Proximity Context Filter — Cross-Sector Disambiguation

**Prioridade:** P0 (false positive que passou por todas as camadas)
**Tipo:** Nova camada de filtro (Camada 1B.3)
**Estimativa:** M (4-8h)
**Dependencias:** Nenhuma (aditivo, nao quebra nada existente)

---

## Contexto

O setor `vestuario` (5/5 maturidade) produziu falso positivo em "compra de alimentos para confeccao de merenda escolar". A keyword "confeccao" casou com vestuario, e a exclusao "confeccao de merenda" (sectors_data.yaml L143) deveria ter pego — mas falhou porque o texto real usa variante de preposicao (e.g., "confeccao **da** merenda" em vez de "confeccao **de** merenda").

O sistema atual de exclusoes usa regex `\b...\b` exact-phrase, que e **estruturalmente fragil** contra variacoes linguisticas (troca de preposicao, artigos, plurais).

**Diretriz do usuario:** "o jeito burro e caro e jogar tudo no colo da LLM, mas somos melhores que isso" — o fix deve ser barato (pure Python), nao LLM.

**Solucao escolhida:** Proximity Context. Quando uma keyword casa, extrair janela de N palavras ao redor. Se a janela contem **signature terms** de OUTRO setor, REJECT. Abordagem preposition-agnostic (nao importa de/da/das/dos entre palavras), deterministica (zero custo LLM), rapida (microsegundos).

---

## Arquitetura

### Posicao no Pipeline (filter.py `aplicar_todos_filtros()`)

```
Exclusions (exact phrase) → Keywords → Context Required
  → ★ NEW: Proximity Context (Camada 1B.3) ★
    → Co-occurrence (Camada 1B.5) → LLM Zero Match → Item Inspection → Density Scoring → LLM Arbiter
```

### Conceito: Signature Terms

Cada setor declara `signature_terms` — 5-15 palavras altamente especificas que sao **identificadores unambiguos** daquele setor. Quando a keyword de um setor DIFERENTE casa em uma licitacao, e a janela ao redor contem signature terms de outro setor → a licitacao e rejeitada do setor que casou.

Exemplo: `alimentos.signature_terms` inclui "merenda". Quando vestuario casa "confeccao", e "merenda" aparece dentro de 8 palavras → REJECT de vestuario.

---

## Acceptance Criteria

### AC1: Adicionar `signature_terms` a sectors_data.yaml (15 setores)

- [ ] Adicionar campo `signature_terms` a cada um dos 15 setores
- [ ] Cada setor deve ter 5-10 termos (minimo 5)
- [ ] Termos devem ser normalizados (lowercase, sem acentos)
- [ ] Termos devem ser altamente especificos ao setor (improvavel aparecer legitimamente em outro)
- [ ] Suporte a termos multi-palavra (e.g., "cesta basica", "licenca de software")

**Tabela de referencia:**

| Setor | Signature Terms |
|-------|----------------|
| vestuario | uniforme, fardamento, jaleco, vestimenta, camiseta, gandola, farda |
| alimentos | merenda, alimenticio, refeicao, hortifruti, cesta basica, rancho, genero alimenticio |
| informatica | computador, notebook, impressora, servidor, monitor, switch, roteador |
| software | licenca de software, sistema de gestao, erp, saas, cloud |
| mobiliario | movel, mobiliario, estante, armario, biro |
| papelaria | resma, toner, cartucho, papel a4, caneta |
| engenharia | pavimentacao, terraplanagem, drenagem, concreto armado, laje, fundacao |
| facilities | limpeza predial, jardinagem, copeiragem, portaria, recepcionista |
| saude | medicamento, farmaceutico, cirurgico, ambulatorial, hospitalar, protese dentaria |
| vigilancia | vigilante, cftv, monitoramento eletronico, ronda, escolta |
| transporte | veiculo, automotivo, pneu, mecanica automotiva, frete |
| manutencao_predial | predial, dedetizacao, ar condicionado split, elevador |
| engenharia_rodoviaria | asfalto, pavimento, sinalizacao viaria, rodovia, acostamento |
| materiais_eletricos | disjuntor, luminaria, quadro eletrico, fiacao, condulete |
| materiais_hidraulicos | encanamento, sifao, torneira, tubo pvc, esgoto |

### AC2: Atualizar SectorConfig em sectors.py

- [ ] Adicionar campo `signature_terms: Set[str]` ao dataclass `SectorConfig`
- [ ] Default: `field(default_factory=set)`
- [ ] Atualizar `_load_sectors_from_yaml()` para parsear o novo campo: `set(cfg.get("signature_terms", []))`
- [ ] Passar ao construtor de `SectorConfig`

### AC3: Implementar funcao `check_proximity_context()` em filter.py

- [ ] Assinatura: `check_proximity_context(texto, matched_terms, current_sector, other_sectors_signatures, window_size=8) -> Tuple[bool, Optional[str]]`
- [ ] Normalizar texto (lowercase, remover acentos)
- [ ] Splittar em lista de palavras
- [ ] Para cada matched_term, encontrar posicao(oes) no array de palavras
- [ ] Extrair janela `[pos - window_size : pos + term_len + window_size]`
- [ ] Construir set de palavras da janela (single-word) + texto da janela (multi-word)
- [ ] Checar signature terms de cada OUTRO setor contra a janela
- [ ] Se match encontrado → return `(True, "keyword:confeccao near alimentos:merenda")`
- [ ] Se nenhum match → return `(False, None)`

### AC4: Integrar no pipeline `aplicar_todos_filtros()`

- [ ] Inserir apos keyword matching (~L2266) e antes de co-occurrence (~L2278)
- [ ] Guardar por feature flag `PROXIMITY_CONTEXT_ENABLED`
- [ ] Construir `other_sigs` dict excluindo setor atual
- [ ] Iterar `resultado_keyword`, chamar `check_proximity_context()` para cada bid
- [ ] Contar `stats["proximity_rejections"]`
- [ ] Log: `logger.debug()` para cada rejection, `logger.info()` para total
- [ ] Bids rejeitadas nao passam para proximas camadas

### AC5: Feature flag + config em config.py

- [ ] Adicionar `"PROXIMITY_CONTEXT_ENABLED": ("PROXIMITY_CONTEXT_ENABLED", "true")` ao `_FEATURE_FLAG_REGISTRY`
- [ ] Adicionar constante: `PROXIMITY_WINDOW_SIZE: int = int(os.getenv("PROXIMITY_WINDOW_SIZE", "8"))`
- [ ] Default: habilitado (true)

### AC6: Testes unitarios — funcao core (~12 testes)

- [ ] "confeccao de merenda escolar" → REJECT de vestuario (alimentos sig "merenda")
- [ ] "confeccao da merenda" → REJECT (variante de preposicao — o fix principal)
- [ ] "confeccao das merendas" → REJECT (plural + artigo)
- [ ] "confeccao de uniformes" → KEEP (nenhum sig de outro setor perto)
- [ ] "reforma do predio com pintura" → testar com sigs relevantes
- [ ] "luva de procedimento cirurgico" → testar cross-sector com saude
- [ ] "sistema hidraulico de bombeamento" → KEEP (sem sig de outro setor)
- [ ] Texto vazio → (False, None)
- [ ] Sem matched_terms → (False, None)
- [ ] Janela no inicio do texto (edge case) → bounds corretos
- [ ] Janela no final do texto (edge case) → bounds corretos
- [ ] Signature term multi-palavra → detectado corretamente

### AC7: Testes de integracao no pipeline (~8 testes)

- [ ] Feature flag OFF → zero proximity rejections
- [ ] Feature flag ON → proximity rejections contadas em stats
- [ ] Chave `proximity_rejections` presente em stats
- [ ] Bids rejeitadas por proximity nao aparecem no resultado final
- [ ] Co-occurrence ainda roda apos proximity (camadas compoem corretamente)
- [ ] Sem setor especificado → proximity skipped
- [ ] Sem matched_terms no bid → proximity skipped para aquele bid
- [ ] Todos os 15 setores tem signature_terms carregados

### AC8: Testes cross-sector (~8 testes)

- [ ] Mesmo termo na janela de 2 setores diferentes → rejeita com primeiro encontrado
- [ ] Signature terms do PROPRIO setor na janela → NAO rejeita (so OUTROS setores)
- [ ] Window size maior → pega mais contexto
- [ ] Window size = 0 → nenhum proximity check (efetivamente desabilitado)
- [ ] Todos os 15 setores tem signature_terms carregados no SECTORS dict

### AC9: Testes de regressao (~4 testes)

- [ ] Casos existentes de vestuario continuam passando
- [ ] Casos existentes de alimentos continuam passando
- [ ] Testes de co-occurrence existentes continuam passando
- [ ] Rodar `pytest backend/` completo — zero regressoes vs baseline (~35 fail / ~3900+ pass)

---

## Definicao de Pronto

- [ ] Todos os ACs implementados e verificados
- [ ] `pytest backend/tests/test_proximity_context.py -v` — todos passam
- [ ] `pytest backend/ --tb=short` — zero regressoes vs baseline
- [ ] Feature flag `PROXIMITY_CONTEXT_ENABLED` funciona (ON/OFF)
- [ ] O caso exato do falso positivo ("confeccao da/de/das merenda") e rejeitado de vestuario
- [ ] Zero mudancas no frontend
- [ ] Zero mudancas no banco/migracoes
- [ ] Zero mudancas no contrato da API

---

## Arquivos Afetados

| Arquivo | Mudanca |
|---------|---------|
| `backend/sectors_data.yaml` | Adicionar `signature_terms` aos 15 setores |
| `backend/sectors.py` | Campo `signature_terms` em SectorConfig + parsing |
| `backend/filter.py` | `check_proximity_context()` + integracao no pipeline |
| `backend/config.py` | Feature flag + `PROXIMITY_WINDOW_SIZE` |
| `backend/tests/test_proximity_context.py` | ~30 testes (NOVO) |

---

## Notas Tecnicas

- **Performance:** Pure Python, microsegundos por bid. Sem I/O, sem LLM, sem rede.
- **Normalizacao:** Remover acentos (`unicodedata.normalize`) + lowercase antes de comparar.
- **Multi-word sigs:** Para "cesta basica", checar se a substring aparece no texto da janela (nao no set de palavras individuais).
- **Nao substitui exclusoes:** Proximity e ADITIVO. Exclusoes exatas continuam rodando antes.
- **Nao afeta LLM arbiter:** Camada downstream, nao muda nada.
- **`_matched_terms`:** Ja existe no dict de cada bid apos keyword matching — reusar.
