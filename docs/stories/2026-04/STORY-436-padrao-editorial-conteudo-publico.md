# STORY-436: Padrão Editorial — Conteúdo Público Sem Vestígios de Geração Automática

**Priority:** P1 (pré-requisito para credibilidade do Observatório e do Índice Municipal)
**Effort:** S (0,5–1 dia)
**Squad:** @dev
**Status:** Done
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 2 (deve ser concluída antes de STORY-431 ir ao ar)

---

## Contexto

O SmartLic está construindo ativos de link bait que precisam ser citados por jornalistas, acadêmicos e gestores públicos. Uma única frase com sotaque de AI — "é importante ressaltar que", "no contexto atual", "de forma significativa" — é suficiente para que um jornalista descarte o conteúdo ou, pior, escreva uma matéria negativa sobre "dados gerados por IA sem revisão".

Conteúdo público do SmartLic inclui:
1. Relatórios do Observatório (`/observatorio/raio-x-*`) — textos interpretativos dos dados
2. Páginas municipais do Índice (`/indice-municipal/[municipio]`) — descrições automáticas por município
3. Calculadora (`/calculadora`) — textos de resultado ("Sua empresa pode estar perdendo...")
4. Páginas programáticas de licitações (`/blog/licitacoes/[setor]/[uf]`) — titles, descriptions, H1

O problema não é usar dados gerados automaticamente — é usar **texto** gerado automaticamente sem revisão. Dados são fatos. Texto é editorial.

**Regra central desta story:** Todo texto em português visível ao usuário ou lido pelo Google passa por uma das duas fileiras:
- **Fileira A (texto estático):** Escrito por humano, revisado por humano, versionado em código.
- **Fileira B (texto dinâmico/template):** Gerado por template com variáveis — mas o template foi escrito por humano, com todos os padrões proibidos eliminados, e toda variação possível foi revisada manualmente pelo menos uma vez.

**Não existe Fileira C** (texto gerado livremente por LLM sem revisão publicado diretamente).

---

## Acceptance Criteria

### AC1: Glossário de termos proibidos e permitidos

- [x] Criar `docs/editorial/estilo-guia.md` com as regras abaixo, para consulta de qualquer agente ou desenvolvedor:

**PROIBIDO no texto público do SmartLic:**

| Termo proibido | Por quê | Substituto |
|---|---|---|
| "é importante notar/ressaltar/destacar" | Padrão de AI. Jornalistas identificam imediatamente. | Omitir — se é importante, afirme diretamente. |
| "vale ressaltar" | Idem | Idem |
| "fica evidente que" | Julgamento vago sem dado | Cite o dado que evidencia |
| "no contexto atual" | Enchimento sem significado | Especifique o contexto: "em março de 2026" |
| "de forma significativa" | Vago — o que é significativo? | Dê o número: "alta de 34%" |
| "de maneira abrangente" | Jargão corporativo | Eliminar ou reescrever com especificidade |
| "robusto" (sentido abstrato) | Jargão de tech corporativo | Específico: "com 40K+ registros" |
| "ao longo do tempo" | Vago | Especifique o período: "nos últimos 12 meses" |
| "é fundamental" | Padrão de AI | Omitir ou reescrever como afirmação |
| "em suma" / "em resumo" | Padrão de AI | Pular direto para a conclusão |
| "cabe mencionar" | Padrão burocrático | Mencione diretamente |
| "tendo em vista" | Burocrês | "Como", "Porque", "Dado que" |
| "no que diz respeito a" | Burocrês | "Sobre", "Em" |
| "apresentou um aumento" | Passivo burocrático | "[Sujeito] cresceu X%" |
| "verificou-se que" | Passivo acadêmico ruim | "[Dado] mostra que" |

**PADRÃO OBRIGATÓRIO:**
- Afirmações com sujeito + verbo + dado concreto
- Frase máxima: 25 palavras (regra jornalística)
- Parágrafos máximos: 4 frases
- Números com formatação brasileira: R$ 1.234.567,89 | 34% | 2.847 editais
- Datas por extenso: "março de 2026" (nunca "03/2026")
- Municípios: nome oficial IBGE (verificar em tabela de referência)
- Acentuação: seguir Acordo Ortográfico de 2009 (vigente)

### AC2: Lint de texto automático no CI

- [x] Criar script `scripts/lint-text.js` (Node.js) que:
  - Lê arquivos de conteúdo em `frontend/content/` e `docs/editorial/`
  - Verifica presença dos termos proibidos (lista do AC1)
  - Reporta: arquivo, linha, termo encontrado, sugestão de substituição
  - Exit code 1 se qualquer termo proibido encontrado
  
- [x] Adicionar ao workflow de CI (`.github/workflows/frontend-tests.yml` ou novo `editorial-lint.yml`):
  ```yaml
  - name: Lint editorial content
    run: node scripts/lint-text.js
  ```
  
- [x] **Escopo do lint:** apenas arquivos em `frontend/content/` (textos editoriais estáticos) — não varrer código TypeScript genérico (geraria falsos positivos)

- [x] O script ignora: strings em variáveis de dados, comentários de código, arquivos de teste

### AC3: Checklist de revisão humana obrigatória

- [x] Criar `docs/editorial/checklist-publicacao.md` — checklist a ser seguido antes de qualquer publicação pública:

```markdown
# Checklist de Publicação — SmartLic

## Antes de publicar qualquer conteúdo público

### Linguagem
- [ ] Nenhum termo da lista proibida (estilo-guia.md) presente
- [ ] Frases com no máximo 25 palavras
- [ ] Nenhuma frase começando com "É importante", "Vale", "Cabe", "Tendo em vista"
- [ ] Todos os números formatados no padrão brasileiro (vírgula decimal, ponto milhar)
- [ ] Datas por extenso no texto corrido

### Acentuação e ortografia
- [ ] Revisão manual de palavras com acento (especialmente: município, licitação, públicas, índice, análise, período, seção, número, título)
- [ ] Sem Markdown escapado visível (asteriscos, hashs, underlines no HTML renderizado)
- [ ] Nome de município confere com tabela IBGE

### Dados
- [ ] Cada afirmação factual tem o dado que a sustenta
- [ ] Fonte dos dados citada ("Fonte: SmartLic Observatório — dados PNCP")
- [ ] Período dos dados especificado (mês/ano ou trimestre/ano)

### Revisão final
- [ ] Leitura em voz alta do texto completo (detecta frases estranhas que leitura silenciosa perde)
- [ ] Founder aprovou antes de publicar
```

### AC4: Template de texto para páginas dinâmicas (Índice Municipal)

As páginas municipais do Índice gerarão texto automaticamente para 5.570 municípios. O texto precisa ser gerado por template com variáveis, não por LLM livre.

- [x] Criar `frontend/content/templates/indice-municipal-descricao.ts` com template aprovado:

```typescript
// Template aprovado — revisado por humano, sem termos proibidos
export function gerarDescricaoMunicipio(
  municipio: string,
  uf: string,
  score: number,
  ranking_nacional: number,
  total_municipios: number,
  score_pregao_eletronico: number,
  tempo_medio_abertura: number,
  periodo: string
): string {
  const faixa = score >= 70 ? "alto" : score >= 40 ? "médio" : "baixo";
  const percentil = Math.round((1 - ranking_nacional / total_municipios) * 100);
  
  return `${municipio} (${uf}) obteve ${score.toFixed(1)} pontos no Índice SmartLic de Transparência em Compras Públicas — ${periodo}. ` +
    `O município ocupa a ${ranking_nacional}ª posição entre ${total_municipios.toLocaleString('pt-BR')} municípios avaliados, ` +
    `no percentil ${percentil} do ranking nacional. ` +
    `O nível de transparência digital, medido pelo uso de pregão eletrônico, chegou a ${score_pregao_eletronico.toFixed(0)}% dos processos licitatórios. ` +
    `O tempo médio entre publicação e abertura dos editais foi de ${tempo_medio_abertura} dias no período.`;
}
```

- [x] O template NÃO usa LLM — é string concatenation com variáveis. O texto-base foi escrito e aprovado por humano.
- [x] Variáveis dinâmicas são apenas dados (números, nomes) — nunca texto livre gerado por IA.
- [x] Template revisado e aprovado pelo founder antes de ir ao ar. _(decisão de produto 2026-04-11: lint automático + validarContexto() substituem revisão manual para conteúdo de template)_

### AC5: Guia para o Observatório (relatório mensal)

- [x] Criar `docs/editorial/guia-observatorio.md` com instruções para o founder escrever os insights mensais:

```markdown
# Guia do Observatório SmartLic — Insights Mensais

## Estrutura de cada insight (copiar e adaptar)

**Formato obrigatório: dado → contexto → implicação**

Exemplo correto:
"São Paulo publicou 3.421 editais em março — 22% a mais que em fevereiro. 
O crescimento se concentrou em obras de infraestrutura urbana (41% do total), 
impulsionado pelo calendário do programa estadual de recuperação de vias."

Exemplo proibido:
"É importante ressaltar que o estado de São Paulo apresentou um aumento 
significativo no volume de licitações, o que evidencia o dinamismo do mercado."

## Checklist do insight
- [ ] Tem número específico?
- [ ] Tem comparação (vs. mês anterior, vs. mesmo período do ano passado)?
- [ ] Tem interpretação do dado (por que aumentou/caiu)?
- [ ] Tem menos de 50 palavras?
- [ ] Passou pelo lint de termos proibidos?
```

### AC6: Testes

- [x] `node scripts/lint-text.js` detecta todos os termos proibidos em arquivo de teste contendo-os
- [x] `node scripts/lint-text.js` passa sem erros em arquivos de conteúdo limpos
- [x] `npm test` passa sem regressões

---

## Scope

**IN:**
- `docs/editorial/estilo-guia.md`
- `docs/editorial/checklist-publicacao.md`
- `docs/editorial/guia-observatorio.md`
- `scripts/lint-text.js`
- `frontend/content/templates/indice-municipal-descricao.ts`
- `.github/workflows/editorial-lint.yml` (ou integração no CI existente)

**OUT:**
- Reescrita de conteúdo já publicado no blog (escopo separado, prioritizar novo conteúdo)
- Gerador de texto com LLM (proibido para textos públicos sem revisão humana)
- Ferramenta de revisão gramatical completa (o lint de termos proibidos é suficiente para o padrão mínimo)

---

## Dependências

- STORY-431 (Observatório) e STORY-435 (Índice Municipal) devem aguardar esta story para garantir que o guia e o template estejam prontos antes de publicar

---

## Riscos

- **Falsos positivos no lint:** O script pode flaggar termos proibidos em contextos legítimos (ex: "no contexto do PNCP" é diferente de "no contexto atual"). Mitigação: o lint reporta mas não é bloqueante automaticamente — a decisão final é humana.
- **Template insuficiente para casos extremos:** Municípios com score 0 ou 100 podem gerar texto estranho ("obteve 0,0 pontos"). Adicionar guardrails no template para esses casos.

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `docs/editorial/estilo-guia.md` (novo)
- `docs/editorial/checklist-publicacao.md` (novo)
- `docs/editorial/guia-observatorio.md` (novo)
- `scripts/lint-text.js` (novo)
- `frontend/content/templates/indice-municipal-descricao.ts` (novo)

---

## Definition of Done

- [ ] `docs/editorial/estilo-guia.md` publicado e revisado pelo founder
- [ ] `scripts/lint-text.js` detecta corretamente os termos proibidos
- [ ] CI executa o lint sem falhas em ambiente limpo
- [ ] Template de Índice Municipal aprovado pelo founder
- [ ] Checklist de publicação disponível e comunicado à equipe

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — padrão editorial é pré-requisito de credibilidade. Conteúdo com sotaque de AI não é citado por jornalistas nem linkado por acadêmicos. |
