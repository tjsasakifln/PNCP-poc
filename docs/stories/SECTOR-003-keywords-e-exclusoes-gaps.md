# SECTOR-003: Keywords e Exclusoes — Gaps de Cobertura

**Prioridade:** P1
**Setores:** alimentos, vigilancia, manutencao_predial, materiais_eletricos, engenharia, transporte, papelaria, software
**Estimativa:** M (4-8h)
**Tipo:** Refinamento de setor em lote

---

## Contexto

Alem dos problemas estruturais (falta de co-occurrence e domain signals, tratados no SECTOR-002), varios setores tem gaps de keywords (itens comuns de licitacao ausentes) e exclusoes insuficientes. Esta story foca nos termos especificos faltantes.

---

## Acceptance Criteria

### AC1: alimentos — Keywords faltantes (+20 termos)
- [ ] Ovos/aves: "ovo", "ovos", "frango congelado", "peito de frango"
- [ ] Graos: "aveia", "trigo", "milho", "fuba", "polvilho"
- [ ] Processados: "margarina", "manteiga", "molho de tomate", "tempero", "condimento", "vinagre", "maionese"
- [ ] Laticinios: "queijo", "iogurte", "creme de leite", "requeijao"
- [ ] Bebidas: "cha", "achocolatado"
- [ ] Institucional: "restaurante industrial", "refeitorio"

### AC2: alimentos — Exclusoes faltantes (+5 termos)
- [ ] "oleo mineral" (medico, nao alimentar)
- [ ] "sal grosso industrial" (piscina/industrial)
- [ ] "cafe da manha" como metafora (improvavel mas possivel)
- [ ] "nutricao animal" / "racao"
- [ ] "suplemento alimentar" (mais saude que alimentos)

### AC3: vigilancia — Keywords faltantes (+12 termos)
- [ ] Servicos: "ronda", "ronda motorizada", "escolta", "escolta armada", "transporte de valores"
- [ ] Equipamentos: "drone", "vant", "cerca eletrica" (como seguranca), "sensor de presenca", "interfone", "porteiro eletronico"
- [ ] Infraestrutura: "cofre", "casa-forte"

### AC4: vigilancia — Exclusoes faltantes (+3 termos)
- [ ] "seguranca juridica"
- [ ] "vigilancia do peso" (saude)
- [ ] "seguranca social" (previdencia)

### AC5: manutencao_predial — Keywords faltantes (+15 termos)
- [ ] Servicos: "desentupimento", "desentupidora", "conserto", "reparo"
- [ ] Especificos: "troca de piso", "pintura interna", "pintura externa"
- [ ] Manutencao de sistemas: "manutencao de telhado", "manutencao de calhas", "manutencao de extintores", "manutencao de grupo gerador", "manutencao de bombas", "manutencao de caixa d'agua"
- [ ] Servicos especializados: "vidracaria", "serralheria", "marcenaria", "spda"

### AC6: manutencao_predial — Context-required faltantes
- [ ] "ar condicionado" (pode ser veicular) -> requer: predial, split, janela, btu, instalacao
- [ ] "impermeabilizacao" (pode ser industrial) -> requer: laje, telhado, banheiro, piscina, parede
- [ ] "climatizacao" (pode ser veicular) -> requer: sala, ambiente, predial, edificio

### AC7: materiais_eletricos — Keywords faltantes (+12 termos)
- [ ] Solar: "painel solar", "painel fotovoltaico", "energia solar", "modulo fotovoltaico", "inversor solar"
- [ ] Componentes: "rele", "contator", "eletrocalha", "conector eletrico", "terminal eletrico", "fusivel", "barramento"

### AC8: materiais_eletricos — Exclusoes faltantes (+3 termos)
- [ ] "energia eletrica" (fatura de consumo, nao material)
- [ ] "reator nuclear" (cientifico)
- [ ] "transformador digital" (TI/negocios)

### AC9: engenharia — Keywords faltantes (+10 termos)
- [ ] Estruturais: "fundacao", "estrutura metalica", "laje", "viga", "pilar", "argamassa"
- [ ] Projetos: "projeto estrutural", "projeto eletrico", "projeto hidrossanitario", "topografia"

### AC10: engenharia — Exclusoes faltantes (+3 termos)
- [ ] "fundacao" como organizacao (ex: "Fundacao Catarinense de Educacao")
- [ ] "estrutura" em contexto organizacional
- [ ] "pilar" em contexto figurativo ("pilar da educacao")

### AC11: transporte — Keywords faltantes (+6 termos)
- [ ] "reboque", "guincho", "tacografo"
- [ ] "lavagem de veiculo", "lavagem automotiva"
- [ ] "bicicleta" (crescente em licitacoes publicas)

### AC12: papelaria — Keywords faltantes (+10 termos)
- [ ] "canetinha", "apontador", "corretivo"
- [ ] "caixa de arquivo", "elastico"
- [ ] "plastificadora", "plastificacao", "guilhotina"
- [ ] "papel kraft", "papel cartao"

### AC13: software — Keywords faltantes (+8 termos)
- [ ] Cybersecurity: "ciberseguranca", "seguranca da informacao", "antivirus"
- [ ] AI/RPA: "inteligencia artificial", "rpa", "automacao de processos"
- [ ] DevOps: "backup"
- [ ] Specific: "vpn"

### AC14: informatica — Keywords faltantes (+7 termos)
- [ ] "webcam", "headset", "fone de ouvido"
- [ ] "access point", "wifi"
- [ ] "pendrive", "pen drive"

### Track B: Testes

### AC15: Testes de novos keywords
- [ ] 1 test case por keyword novo = ~100 tests
- [ ] Verificar que keywords novos nao conflitam com exclusoes existentes
- [ ] Rodar pytest completo — zero regressoes

### AC16: Validacao cruzada
- [ ] Verificar que keywords adicionados em um setor nao geram overlap com exclusoes de outro
- [ ] Especial atencao: "luva" (vestuario vs hidraulico), "painel" (eletrico vs solar), "drone" (vigilancia vs transporte)

---

## Definicao de Pronto

- [ ] ~120 keywords novos adicionados nos 8 setores
- [ ] ~17 exclusoes novas adicionadas
- [ ] ~6 context-required novos
- [ ] ~100 testes novos passando
- [ ] Zero regressoes
- [ ] Todos os setores 3/5 sobem para pelo menos 3.5/5 (melhoria incremental pre-SECTOR-002)
