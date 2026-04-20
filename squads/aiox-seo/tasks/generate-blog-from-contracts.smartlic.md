# Task: Generate Blog/Observatory Content from supplier_contracts

Task canônica para agentes `aiox-seo` gerarem conteúdo long-tail baseado em supplier_contracts.

## Quando usar

- Criar/atualizar página `/observatorio/[setor]` ou `/observatorio/[setor]/[uf]`
- Criar/atualizar página `/fornecedores/[cnpj]` para top 10k CNPJs
- Criar/atualizar página `/orgaos/[cnpj]` para top 5k órgãos
- Gerar post analítico de blog (ex: "Evolução das licitações de limpeza em SC em 2025")

## Pipeline padrão

### Fase 1 — Query dataset (~30s)

Executar query SQL contra `supplier_contracts`. Ver schema em `../data/supplier-contracts-schema.md`.

Exemplo — hub setor × UF:
```sql
SELECT
  uf_orgao,
  COUNT(*) AS n,
  SUM(valor_contrato) AS volume,
  AVG(valor_contrato) AS ticket_medio,
  array_agg(DISTINCT nome_fornecedor ORDER BY nome_fornecedor) FILTER (WHERE nome_fornecedor IS NOT NULL) AS fornecedores_amostra
FROM supplier_contracts
WHERE objeto_contrato ~* '<keywords do setor via sectors_data.yaml>'
  AND data_assinatura >= CURRENT_DATE - INTERVAL '12 months'
  AND uf_orgao = $1
GROUP BY uf_orgao;
```

### Fase 2 — Enrichment (opcional)

Se o contexto pede análise qualitativa:
- Delegar a `aiox-deep-research` para bias audit + síntese
- Adicionar citações/referências

### Fase 3 — LLM narrative generation (Haiku/Sonnet)

**INPUT** para LLM:
- JSON estruturado dos dados quantitativos
- Glossário do setor
- Instrução de tom: informativo, factual, sem superlativos

**OUTPUT esperado:**
- Parágrafo introdutório (setor + UF + escopo)
- 3-5 bullets de destaque
- Contexto regulatório (se aplicável — consultar `aiox-legal-analyst`)
- Call-to-action sutil: "veja editais abertos deste setor no SmartLic"

**ANTI-PATTERNS vetados na geração:**
- ❌ "A cidade cresceu muito no setor X" (se dataset não comprovou)
- ❌ "É o melhor fornecedor" (opinião, não fact)
- ❌ Extrapolação sem N amostral claro
- ❌ Repetição de keywords (keyword stuffing detectável)
- ❌ Conteúdo vazio ("este é um dos setores mais importantes do Brasil")

### Fase 4 — Render via Next.js page

Page em `frontend/app/observatorio/[setor]/[uf]/page.tsx` (ou equivalente):

```tsx
export async function generateMetadata({ params }) {
  return {
    title: `Licitações de ${setor} em ${uf} | SmartLic`,
    description: `Análise de ${N} contratos em ${uf} no setor de ${setor}...`,
    openGraph: { ... },
    alternates: { canonical: `https://smartlic.tech/observatorio/${setor}/${uf}` }
  };
}

export default async function Page({ params }) {
  const data = await fetchAggregatedData(params.setor, params.uf);
  return (
    <article>
      <Breadcrumbs ... />
      <StructuredData data={jsonLd(data)} />
      <Header ... />
      <NarrativeSection content={data.narrative} />
      <ChartSection data={data.timeseries} />
      <TopFornecedores data={data.topFornecedores} />
      <RelatedEditais uf={params.uf} setor={params.setor} />
    </article>
  );
}
```

Delegar renderização complexa a `aiox-apex`.

### Fase 5 — Validação SEO

Checklist obrigatório:
- [ ] Title único (não duplicado em outra page)
- [ ] Description 120-160 chars
- [ ] Canonical correto (sem trailing slash)
- [ ] H1 único por page
- [ ] Alt text em gráficos
- [ ] Schema.org JSON-LD válido (validar em schema.org/validator)
- [ ] Internal links (3+ para pages relacionadas)
- [ ] Mobile-friendly (Tailwind responsive)
- [ ] LCP <2.5s (Lighthouse)

## Refresh cadence

- Hub pages (/observatorio/*): weekly refresh via cron
- Fornecedor/Órgão pages: refresh ao mergir nova ingestion (3x/sem)
- Post de blog analítico: one-off, não re-gerar (mas adicionar "atualizado em" se editar)

## Caching

- HTTP: `Cache-Control: public, max-age=86400, stale-while-revalidate=604800`
- Next.js: `export const revalidate = 86400` (daily)
- Nunca `export const revalidate = 0` (sem cache — pesa DB)

## Observabilidade

- Google Search Console: monitorar impressões + CTR por template
- Sentry: capturar 404s para criar redirects se slug muda
- Mixpanel/analytics: track outbound clicks para `/buscar` (conversão)
