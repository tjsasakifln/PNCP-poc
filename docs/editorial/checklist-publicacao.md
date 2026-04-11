# Checklist de Publicação — SmartLic

Use antes de qualquer publicação pública: relatório do Observatório, página do Índice Municipal, artigo do blog editorial, landing page nova.

**Regra:** Story só vai para Done após revisão humana do fundador e aprovação explícita.

---

## Checklist (13 itens obrigatórios)

- [ ] Nenhum termo proibido (`node scripts/lint-text.js` passou sem erros)
- [ ] Frases com no máximo 25 palavras
- [ ] Nenhuma frase começa com frase proibida (verificar lista em `estilo-guia.md`)
- [ ] Todos os números em formato brasileiro: `R$ 1.234.567,89`, `34%`, `2.847 editais`
- [ ] Datas por extenso: "março de 2026" (não "03/2026" ou "2026-03")
- [ ] Palavras acentuadas corretamente: `município`, `licitação`, `públicas`, `índice`, `análise`, `período`, `seção`, `número`, `título`, `órgão`
- [ ] Nenhum marcador Markdown visível no HTML renderizado (asteriscos, hashes, underlines, backticks)
- [ ] Nomes de municípios conferidos com tabela IBGE (não abreviações)
- [ ] Cada afirmação factual tem dado de suporte
- [ ] Fonte dos dados citada: "Fonte: SmartLic Observatório — dados PNCP"
- [ ] Período dos dados especificado (mês/ano ou trimestre/ano)
- [ ] Leitura em voz alta (captura construções estranhas que leitura silenciosa não pega)
- [ ] **Fundador leu o texto completo do início ao fim e aprovou explicitamente**

---

## Para relatórios do Observatório

Checklist adicional:

- [ ] Título inclui número concreto (não afirmação vaga)
- [ ] Meta description inclui estatística central
- [ ] Headline principal declarada (fato mais impactante do período)
- [ ] Gráficos têm título descritivo, eixos rotulados, fonte citada
- [ ] CSV exportável tem header com comentário de fonte
- [ ] Schema.org Dataset incluído com licença CC BY 4.0

---

## Para páginas do Índice Municipal

Checklist adicional:

- [ ] Nome do município conferido com tabela IBGE (nome oficial)
- [ ] Score exibido com 1 decimal: "72,4 pontos"
- [ ] Ranking confirmado (nenhum empate exato — desempate por critério secundário)
- [ ] Texto interpretativo segue estrutura dado → contexto → implicação
- [ ] Template aprovado pelo fundador antes do primeiro deploy

---

## Aprovação

| Campo | Valor |
|-------|-------|
| Publicação | |
| Data da revisão | |
| Revisado por | Tiago Sasaki |
| Aprovado? | ☐ Sim ☐ Não |
| Observações | |
