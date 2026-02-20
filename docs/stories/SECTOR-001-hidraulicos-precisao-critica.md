# SECTOR-001: Precisao Critica — materiais_hidraulicos

**Prioridade:** P0 (Highest false-positive risk)
**Setor:** materiais_hidraulicos (Maturity: 2/5 -> target 4/5)
**Estimativa:** M (4-8h)
**Tipo:** Refinamento de setor

---

## Contexto

O setor `materiais_hidraulicos` e o PIOR classificado (2/5). Tem o menor conjunto de exclusoes (22) e keywords extremamente genericas ("joelho", "curva", "te", "luva", "adaptador") que causam falsos positivos em massa. Nao tem co-occurrence rules nem domain signals.

**Problema real:** "luva" casa com EPI/vestuario, "curva" com rodoviaria, "te" com qualquer texto, "adaptador" com informatica, "registro" com documentos burocraticos, "bomba" com militar.

---

## Acceptance Criteria

### AC1: Expandir keywords (+15 termos de alta frequencia)
- [ ] Adicionar: "torneira", "sifao", "chuveiro", "ducha", "descarga", "vaso sanitario", "valvula de retencao", "cavalete", "pressurizador", "irrigacao", "aspersao", "mangueira", "cisterna", "cano", "ramal"
- [ ] Verificar que cada keyword tem forma singular + plural
- [ ] Verificar cobertura de acentos (torneira nao precisa, sifao/sifoes sim)

### AC2: Expandir exclusoes (+20 termos criticos)
- [ ] "luva" em contexto PPE/vestuario: "luva de procedimento", "luva cirurgica", "luva de protecao", "luva de latex", "luva de nitrila", "luva descartavel", "luva de seguranca", "luva termica"
- [ ] "curva" em contexto nao-hidraulico: "curva de nivel", "curva granulometrica", "curva de aprendizado", "curva rodoviaria", "curva de demanda"
- [ ] "adaptador" em contexto IT/eletrico: "adaptador usb", "adaptador de tomada", "adaptador de energia", "adaptador eletrico", "adaptador de rede"
- [ ] "bomba" em contexto nao-hidraulico: "bomba de fumaca", "bomba lacrimogenea", "bomba de concreto", "bomba de infusao" (medica)
- [ ] "registro" em contexto documental: "registro de precos", "registro de imoveis", "registro civil", "registro de nascimento", "registro eletronico"
- [ ] "tubo" em contexto medico: "tubo endotraqueal", "tubo de coleta", "tubo de ensaio"
- [ ] "reservatorio" em contexto nao-agua: "reservatorio de combustivel", "reservatorio de oleo"

### AC3: Adicionar co-occurrence rules (3 regras)
- [ ] Regra 1: "luva" + contexto negativo (cirurgica, procedimento, protecao, latex, nitrila, descartavel) -> REJECT
- [ ] Regra 2: "registro" + contexto negativo (precos, imoveis, civil, nascimento, eletronico, cartorio) -> REJECT
- [ ] Regra 3: "bomba" + contexto negativo (infusao, fumaca, concreto, lacrimogenea) -> REJECT

### AC4: Adicionar domain signals
- [ ] NCM prefixes: "3917" (tubos plasticos), "7307" (conexoes de ferro/aco), "7411-7412" (tubos/conexoes de cobre), "3926" (artigos de plastico para construcao), "8413" (bombas de liquidos)
- [ ] Unit patterns: "metro", "metro linear", "m", "peca", "unidade", "kit"

### AC5: Expandir context_required_keywords
- [ ] Adicionar: "bomba" (requer: agua, submersa, centrifuga, hidraulica, poco, captacao)
- [ ] Adicionar: "registro" (requer: agua, hidraulico, gaveta, esfera, pressao)
- [ ] Adicionar: "mangueira" (requer: agua, jardim, incendio, hidraulica)
- [ ] Adicionar: "tanque" (requer: agua, reservatorio, armazenamento) -- excluir "tanque de guerra", "tanque militar"

### AC6: Testes
- [ ] Adicionar 15+ test cases em test_filter.py para materiais_hidraulicos
- [ ] Testar false positives: "luva de procedimento" NAO deve casar
- [ ] Testar false positives: "registro de precos" NAO deve casar
- [ ] Testar true positives: "torneira de cozinha" DEVE casar
- [ ] Testar true positives: "tubo PVC 100mm" DEVE casar
- [ ] Rodar pytest completo — zero regressoes

---

## Definicao de Pronto

- [ ] Maturity score sobe de 2/5 para 4/5
- [ ] Exclusoes passam de 22 para 42+
- [ ] Keywords passam de 63 para 78+
- [ ] 3 co-occurrence rules ativas
- [ ] Domain signals com 5 NCM prefixes
- [ ] 15+ testes novos passando
- [ ] Zero regressoes nos outros setores
