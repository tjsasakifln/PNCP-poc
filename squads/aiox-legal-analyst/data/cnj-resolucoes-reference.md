# Referencia: Resolucoes CNJ Relevantes

> Resolucoes do Conselho Nacional de Justica integradas ao pipeline de analise processual

---

## Resolucao CNJ 331/2020 — DATAJUD

**Tema:** Institui a Base Nacional de Dados do Poder Judiciario (DATAJUD)

**Pontos-chave:**
- Todos os tribunais devem enviar dados processuais ao DATAJUD
- Schema padronizado de dados obrigatorios
- Atualizacao diaria
- Dados publicos acessiveis via API

**Impacto no pipeline:** Schema DATAJUD e obrigatorio para toda saida de dados.

---

## Resolucao CNJ 335/2020 — PDPJ

**Tema:** Institui a Plataforma Digital do Poder Judiciario Brasileiro (PDPJ-Br)

**Pontos-chave:**
- Plataforma nacional para servicos digitais do Judiciario
- Integracao entre sistemas de diferentes tribunais
- Microsservicos e APIs padronizadas
- Identidade digital e autenticacao unificada

**Impacto no pipeline:** Compatibilidade com formato PDPJ para integracao.

---

## Resolucao CNJ 332/2020 — IA e Etica

**Tema:** Dispoe sobre a etica, a transparencia e a governanca na producao e no uso de Inteligencia Artificial no ambito do Poder Judiciario

**Pontos-chave:**
- IA deve respeitar direitos fundamentais
- Transparencia: decisoes assistidas por IA devem ser identificadas
- Nao discriminacao: IA nao pode produzir discriminacao
- Supervisao humana: decisoes judiciais assistidas por IA exigem supervisao
- Governanca: tribunais devem ter politica de governanca de IA
- Auditabilidade: sistemas de IA devem ser auditaveis

**Impacto no pipeline:** Toda analise deve incluir nota de supervisao humana e transparencia sobre uso de IA.

---

## Resolucao CNJ 396/2021 — TPU

**Tema:** Atualiza as Tabelas Processuais Unificadas do Poder Judiciario

**Pontos-chave:**
- Classes processuais padronizadas (todos os ramos)
- Arvore de assuntos padronizada (niveis 1-3)
- Movimentacoes processuais padronizadas
- Sistema de Gestao de Tabelas (SGT) para atualizacao

**Impacto no pipeline:** Classificacao processual DEVE seguir TPU.

---

## Resolucao CNJ 235/2016 — Padronizacao

**Tema:** Dispoe sobre a padronizacao de procedimentos administrativos de julgamento de processos

**Pontos-chave:**
- Formato padrao de dados judiciais
- Padronizacao de nomes, datas, numeros
- Formato de numero de processo (NNNNNNN-DD.AAAA.J.TR.OOOO)

**Impacto no pipeline:** Formato de dados deve seguir padrao CNJ.

---

## Resolucao CNJ 185/2013 — PJe

**Tema:** Institui o Sistema Processo Judicial Eletronico (PJe)

**Pontos-chave:**
- Processo eletronico como padrao
- Peticao eletronica
- Assinatura digital
- Intimacao eletronica

**Impacto no pipeline:** Compatibilidade com formato PJe quando aplicavel.
