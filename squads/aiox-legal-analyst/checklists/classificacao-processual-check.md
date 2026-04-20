# Checklist: Classificacao Processual

**Versao:** 1.0
**Agente:** barbosa-classifier
**Quando usar:** Fase 0 (Triagem)
**Threshold de aprovacao:** 6/7 itens minimo

---

## Itens

- [ ] **Classe TPU** — Classe processual com codigo TPU valido | PASS: Codigo e descricao da classe presentes
- [ ] **Assuntos TPU** — Assuntos classificados na arvore TPU | PASS: Nivel mais especifico possivel usado
- [ ] **Competencia material** — Competencia material definida | PASS: Justica competente identificada (Federal, Estadual, Trabalho, etc.)
- [ ] **Competencia territorial** — Competencia territorial definida | PASS: Foro competente identificado
- [ ] **Competencia funcional** — Instancia e grau definidos | PASS: Tribunal/vara competente
- [ ] **Codigo DATAJUD** — Codigo no formato DATAJUD gerado | PASS: Formato valido
- [ ] **Ramo do Direito** — Area do Direito identificada | PASS: Civil, Penal, Trabalhista, etc.

## Condicoes de Veto
- Classe TPU ausente
- Competencia nao definida
- Ramo do Direito nao identificado

## Pontuacao
- **APROVADO:** 6/7 ou mais
- **REVISAO:** 4-5/7
- **REPROVADO:** 3/7 ou menos
