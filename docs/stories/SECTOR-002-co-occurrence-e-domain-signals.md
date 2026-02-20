# SECTOR-002: Co-Occurrence Rules e Domain Signals para 12 setores

**Prioridade:** P1
**Setores:** Todos os 12 sem co-occurrence rules (todos exceto vestuario, informatica, saude)
**Estimativa:** L (8-16h)
**Tipo:** Refinamento de setor em lote

---

## Contexto

Apenas 3/15 setores (vestuario, informatica, saude) tem co-occurrence rules e domain signals. Os 12 restantes dependem exclusivamente de keyword+exclusion+context_required, o que e insuficiente para setores com termos ambiguos como "reforma" (engenharia), "limpeza" (facilities), "mecanica" (transporte), "camera" (vigilancia).

**Impact:** Adicionar co-occurrence rules reduz falsos positivos em ~30-40% nos setores afetados (estimativa baseada no padrao do vestuario, onde rules eliminam ~35% dos FPs).

---

## Acceptance Criteria

### Track A: Co-Occurrence Rules (12 setores)

#### AC1: alimentos (2 rules)
- [ ] "carne" + negativo (bovina viva, pecuaria, veterinaria, abatedouro) -> evitar livestock
- [ ] "leite" + negativo (cosmetico, hidratante, corporal, capilar) -> evitar cosmetics

#### AC2: software (2 rules)
- [ ] "sistema" + negativo (hidraulico, eletrico, incendio, alarme, ar condicionado, elevador, bomba) -> evitar infrastructure
- [ ] "plataforma" + negativo (elevacao, elevador, caminhao, carroceria) -> evitar equipment

#### AC3: mobiliario (2 rules)
- [ ] "mesa" + negativo (cirurgia, negociacao, redonda reuniao) -> evitar non-furniture
- [ ] "cadeira" + negativo (rodas medica, odontologica, ginecologica) -> evitar medical

#### AC4: facilities (2 rules)
- [ ] "limpeza" + negativo (terreno, fossa, rio, bueiro, galeria, drenagem) -> evitar infra publica
- [ ] "conservacao" + negativo (ambiental, florestal, biodiversidade, patrimonio historico) -> evitar conservation

#### AC5: engenharia (2 rules)
- [ ] "reforma" + negativo (administrativa, tributaria, curricular, politica, agraria) -> evitar policy
- [ ] "obra" + negativo (literaria, artistica, musical, cinematografica) -> evitar arts

#### AC6: vigilancia (2 rules)
- [ ] "camera" + negativo (fotografica, digital, celular, smartphone, drone) -> evitar electronics
- [ ] "alarme" + negativo (incendio, hospitalar, medico, fumaca) -> evitar fire/medical

#### AC7: transporte (2 rules)
- [ ] "mecanica" + negativo (solos, ventilacao, quantica, fluidos, computacional) -> evitar science
- [ ] "filtro" + negativo (agua, linha, solar, internet, email) -> evitar non-auto

#### AC8: manutencao_predial (2 rules)
- [ ] "ar condicionado" + negativo (veicular, automotivo, carro, onibus, caminhao) -> evitar auto
- [ ] "elevador" + negativo (carga industrial, mina, plataforma offshore) -> evitar industrial

#### AC9: papelaria (1 rule)
- [ ] "papel" + negativo (parede, moeda, higienico, toalha, aluminio) -> evitar non-stationery

#### AC10: engenharia_rodoviaria (1 rule)
- [ ] "ponte" + negativo (dental, fixa dental, protese, dados, VPN, rede) -> evitar non-road

#### AC11: materiais_eletricos (1 rule)
- [ ] "transformador" + negativo (digital, social, cultural, organizacional) -> evitar figurative

### Track B: Domain Signals (NCM codes para 8 setores prioritarios)

#### AC12: mobiliario
- [ ] NCM: "9401" (assentos), "9403" (moveis), "9404" (colchoes)
- [ ] Units: "peca", "unidade", "conjunto", "jogo"

#### AC13: papelaria
- [ ] NCM: "4802" (papel), "4820" (cadernos), "9608" (canetas), "9609" (lapis)
- [ ] Units: "resma", "caixa", "pacote", "unidade"

#### AC14: transporte
- [ ] NCM: "8702-8704" (veiculos), "4011" (pneus), "8708" (pecas auto)
- [ ] Units: "unidade", "litro", "peca", "jogo"

#### AC15: materiais_eletricos
- [ ] NCM: "8536" (disjuntores), "8537" (quadros), "8544" (cabos), "9405" (luminarias)
- [ ] Units: "metro", "rolo", "peca", "unidade"

#### AC16: vigilancia
- [ ] NCM: "8525" (cameras), "8531" (alarmes)
- [ ] Units: "posto", "hora", "unidade"

#### AC17: facilities
- [ ] NCM: "3402" (detergentes), "4818" (papel higienico), "9603" (vassouras)
- [ ] Units: "litro", "unidade", "caixa", "pacote"

#### AC18: engenharia
- [ ] NCM: "6810" (cimento/concreto), "7214" (barras de aco), "6802" (pedras)
- [ ] Units: "m2", "m3", "tonelada", "metro"

#### AC19: engenharia_rodoviaria
- [ ] NCM: "2713" (asfalto), "6810" (concreto)
- [ ] Units: "m2", "tonelada", "km"

### Track C: Testes

#### AC20: Testes de co-occurrence
- [ ] 2 test cases por regra (1 reject + 1 pass) = 48 tests
- [ ] Verificar que regras nao afetam true positives

#### AC21: Testes de domain signals
- [ ] 2 test cases por setor (1 match NCM + 1 no-match) = 16 tests
- [ ] Verificar compatibilidade com item_inspector.py

#### AC22: Regression
- [ ] Rodar pytest completo — zero regressoes
- [ ] Rodar 3 buscas reais com setores criticos (engenharia, facilities, transporte) e comparar resultados antes/depois

---

## Definicao de Pronto

- [ ] 22 co-occurrence rules adicionadas (nos 12 setores)
- [ ] 8 setores com domain signals (NCM codes)
- [ ] 64+ testes novos passando
- [ ] Zero regressoes
- [ ] Setores alimentos, papelaria, engenharia, vigilancia, transporte, manutencao_predial sobem de 3/5 para 4/5
