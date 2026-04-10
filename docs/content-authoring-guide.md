# Guia de Autoria de Conteúdo Estático

Este guia vale para quem edita ou cria conteúdo em arquivos TypeScript sob `frontend/lib/*.ts` — por exemplo `questions.ts`, `glossary-terms.ts`, `programmatic.ts`, `blog.ts`. As regras abaixo garantem qualidade linguística e renderização correta para usuários finais e mecanismos de busca.

## Regra 1 — Português com acentos completos (UTF-8)

Todo texto em prosa (campos `answer`, `definition`, `body`, `title`, `description`, `metaDescription`, `example`, etc.) deve ser escrito em **português acentuado**.

**Certo:** `licitação`, `pregão`, `órgão`, `até`, `são`, `análise`, `você`.

**Errado:** `licitacao`, `pregao`, `orgao`, `ate`, `sao`, `analise`, `voce`.

> **Exceção:** campos de identificador (`slug`, arrays como `relatedTerms`, `relatedSectors`, `relatedArticles`) mantêm a forma sem acento — eles compõem URLs e chaves, não são exibidos diretamente ao usuário. O linter automaticamente **ignora** strings que se pareçam com slugs.

### Como garantir encoding correto

- No VS Code, confirme o indicador no canto inferior direito: deve estar em `UTF-8`.
- Ao colar texto de outras fontes (Word, Google Docs, PDF), cheque se a cola veio com acentos intactos. Cola de alguns PDFs remove todos os diacríticos silenciosamente.
- Use sempre teclado português-Brasil ou método de entrada com acentos ativo. Nunca substitua `ã` por `a~` ou tokens similares.

## Regra 2 — Markdown é permitido em campos de prosa

Os campos de prosa (`answer`, `definition`, `body`, `example`) aceitam **markdown GFM**:

| Elemento | Sintaxe | Renderiza como |
|---|---|---|
| Negrito | `**texto**` | **texto** |
| Itálico | `*texto*` | *texto* |
| Listas com bullets | `- item` | • item |
| Listas numeradas | `1. item` | 1. item |
| Headings | `## Subtítulo` | `<h2>` estilizado |
| Link | `[texto](/url)` | [texto](/url) |
| Código inline | `` `código` `` | `código` |
| Tabela GFM | `\| col \| col \|` | tabela |

Esses marcadores são interpretados por `react-markdown` + `remark-gfm` em `frontend/app/perguntas/[slug]/page.tsx` e páginas equivalentes. Para dados passados ao schema.org JSON-LD, o markdown é **automaticamente removido** via `stripMarkdown()` em `frontend/lib/text.ts` — você não precisa escrever duas versões.

**Nunca** escreva markdown HTML cru (`<p>`, `<strong>`, `<ul>`) nesses campos. Use só a sintaxe markdown acima.

## Regra 3 — Valide em dois passos antes de commitar

O pipeline de acentos tem dois passos: um **determinístico** (sempre no CI) e um **LLM-assistido** (rodado localmente quando há conteúdo novo).

### Passo 3a — Normalização determinística (sem LLM)

Corrige palavras com acento óbvio (`licitacao→licitação`, `orgao→órgão`, `servicos→serviços`, etc.) via dicionário de ~400 entradas. Também aplica regras de frase (`e permitida→é permitida`, `e obrigatório→é obrigatório`, etc.).

```bash
# Preview
python scripts/fix_content_accents.py --dry-run --all

# Aplicar
python scripts/fix_content_accents.py --all

# Check (usado no CI — retorna exit 1 se encontrar)
python scripts/check_content_accents.py
```

### Passo 3b — Resolver ambíguos via LLM (`e`/`é`, `esta`/`está`, `pais`/`país`, `por`/`pôr`)

Algumas palavras têm significado duplo decidido apenas pelo contexto — conjunção ou verbo, demonstrativo ou verbo, nação ou plural de "pai". O resolver usa **GPT-4.1-mini** com prompt estrito de gramática PT-BR para decidir cada ocorrência, com cache por `(token, contexto)` em `scripts/.accent_cache.json` (gitignored) para idempotência.

```bash
# Preview (não chama LLM)
python scripts/resolve_ambiguous_accents.py --dry-run --all

# Executar (chama LLM, grava correções)
python scripts/resolve_ambiguous_accents.py --all

# Forçar reclassificação (ignora cache)
python scripts/resolve_ambiguous_accents.py --clear-cache --all
```

**Requisitos:** `OPENAI_API_KEY` no ambiente (o script lê automaticamente de `backend/.env`). Custo típico: ~$0.10 para ~1800 ocorrências em 46 chamadas batched.

**Quando rodar:** sempre que adicionar ou editar conteúdo em `frontend/lib/*.ts` com texto em português. O CI **não** roda este passo — o resolver é uma operação manual one-shot. Após rodar, o conteúdo fica corrigido em disco e o `check_content_accents.py` (determinístico, offline) continua passando sem nada a reclamar.

**Fluxo recomendado:**
1. Edite conteúdo em `frontend/lib/X.ts`
2. `python scripts/fix_content_accents.py --all` (determinístico)
3. `python scripts/resolve_ambiguous_accents.py --all` (LLM ambíguos)
4. `python scripts/check_content_accents.py` (confirma zero pendências)
5. Commit + push — o CI roda o check determinístico automaticamente

## Referências

- Dicionário determinístico: `scripts/_pt_accents.py`
- Normalizador CLI (determinístico): `scripts/fix_content_accents.py`
- Resolver LLM (ambíguos): `scripts/resolve_ambiguous_accents.py`
- Testes unitários: `scripts/tests/test_fix_content_accents.py` (39 testes)
- Helper de strip markdown (JSON-LD): `frontend/lib/text.ts`
- Página de referência que consome markdown: `frontend/app/perguntas/[slug]/page.tsx`
