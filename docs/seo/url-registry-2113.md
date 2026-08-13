# Registro de URLs — #2113

Baseline 2026-08-13. Decisões sobre patrimônio indexado.

| Família | Padrão | Destino | Motivo |
|---|---|---|---|
| Home | `/` | KEEP + ADAPT | Entrada de autoridade |
| Licitações | `/licitacoes`, `/licitacoes/[setor]` | KEEP + ADAPT | Intenção comercial alta |
| Contratos | `/contratos`, `/contratos/[setor]/[uf]` | KEEP + ADAPT | Dado único |
| Empresas | `/cnpj`, `/cnpj/[cnpj]`, `/fornecedores/[cnpj]` | KEEP + ADAPT | Query GSC de CNPJ |
| Órgãos | `/orgaos`, `/orgaos/[slug]` | KEEP + ADAPT | Comprador |
| Municípios | `/municipios`, `/municipios/[slug]` | KEEP + ADAPT | Recorte local |
| Observatório | `/observatorio`, `/observatorio/raio-x-*` | KEEP + ADAPT | Autoridade |
| Ferramentas | `/calculadora`, `/comparador`, `/compliance` | KEEP + ADAPT | Product-as-content |
| Editorial | `/blog`, `/perguntas`, `/glossario`, `/guia` | KEEP + ADAPT | Internal linking |
| Consultoria | `/consultoria-b2g` | KEEP + PRIORITIZE | Conversão |
| Sobre | `/sobre` | KEEP + ADAPT | Relação CONFENGE |
| Pricing | `/pricing` | REDIRECT 301 → `/consultoria-b2g` | SaaS morto |
| Planos | `/planos`, `/planos/*` | REDIRECT 301 → `/consultoria-b2g` | SaaS morto |
| Signup | `/signup`, `/signup/*` | REDIRECT 301 → `/consultoria-b2g` | SaaS morto |
| Fundadores | `/fundadores`, `/fundadores/*` | REDIRECT 301 → `/sobre` | Oferta morta |
| Founding | `/founding`, `/founding/*` | REDIRECT 301 → `/sobre` | Evita chain `/founding` → `/fundadores` → `/sobre` |
| Busca auth | `/buscar` | KEEP + ADAPT (não CTA público) | Admin/legado |
| Login | `/login` | KEEP | Admin interno |

Regras: zero chain nova além do founding legado; zero 404 planejado nestas famílias; empty = `EmptyStateSEO` + noindex, nunca 404 de dado.

GSC baseline: usar snapshots já versionados em `docs/seo/` e a página admin `/admin/seo`. Este ciclo não teve API GSC acessível — cliques/impressões por URL ficam UNKNOWN, não zero.
