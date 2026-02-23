# GTM-UX-001: Unificar Banners em DataQualityBanner Unico

## Epic
Root Cause — UX (EPIC-GTM-ROOT)

## Sprint
Sprint 7: GTM Root Cause — Tier 2

## Prioridade
P1

## Estimativa
12h

## Descricao

O frontend tem 8 banners independentes que podem empilhar simultaneamente na pagina de busca: CacheBanner, PartialResultsPrompt, DegradationBanner, OperationalStateBanner, SourcesUnavailable, refresh banner, truncation warning, e failed UFs indicator. No pior caso (outage parcial), todos aparecem ao mesmo tempo, criando um "muro de avisos" que destroi a confianca do usuario e empurra o conteudo principal para baixo.

### Situacao Atual

| Banner | Componente | Quando Aparece |
|--------|-----------|----------------|
| Cache stale | `CacheBanner.tsx` | Resultados de cache |
| Partial results | `PartialResultsPrompt.tsx` | Nem todas UFs retornaram |
| Degradation | `DegradationBanner.tsx` | Circuit breaker ativo |
| Operational state | `OperationalStateBanner` (inline) | Estado degraded do sistema |
| Sources unavailable | `SourcesUnavailable.tsx` | Nenhuma fonte disponivel |
| Refresh | Inline em `SearchResults.tsx` | Dados desatualizados |
| Truncation | Inline warning | Resultados truncados |
| Failed UFs | `UfProgressGrid` badges | UFs com erro |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| UX-ISSUE-029 | UX | 8 banners empilham — muro de avisos destroi confianca |

## Criterios de Aceite

### Banner Consolidado

- [x] AC1: Novo componente `DataQualityBanner.tsx` substitui 6-8 banners individuais
- [x] AC2: Banner unico com formato: "Resultados de 4/7 estados | Cache de 2h | 2 timeouts. [Atualizar]"
- [x] AC3: Maximo 1 banner visivel por vez (nunca empilhar)
- [x] AC4: Prioridade de exibicao: erro total > parcial > cache stale > truncation > info

### Informacao Consolidada

- [x] AC5: Badge discreto de UFs: "5/7 estados" (clicavel para expandir detalhes)
- [x] AC6: Badge de freshness: "Dados de 2h atras" ou "Dados em tempo real"
- [x] AC7: Badge de fonte: "3/3 fontes" ou "1/3 fontes" (tooltip com nomes)
- [x] AC8: Botao de acao contextual: "Atualizar" quando stale, "Tentar novamente" quando erro

### Remocao dos Banners Individuais

- [x] AC9: `CacheBanner.tsx` removido ou deprecated
- [x] AC10: `DegradationBanner.tsx` removido ou deprecated
- [x] AC11: `PartialResultsPrompt.tsx` integrado ao DataQualityBanner
- [x] AC12: Banners inline em `SearchResults.tsx` removidos

### Visual

- [x] AC13: Banner usa glass morphism consistente (GlassCard base)
- [x] AC14: Cores: info (azul), warning (amarelo), error (vermelho) — um por vez
- [x] AC15: Mobile: banner compacto, badges em linha unica com scroll horizontal

## Testes Obrigatorios

```bash
cd frontend && npm test -- --testPathPattern="DataQualityBanner" --no-coverage
```

- [x] T1: Banner mostra "5/7 estados" quando 2 UFs falham
- [x] T2: Banner mostra "Cache de 2h" quando dados stale
- [x] T3: Apenas 1 banner visivel mesmo com multiplos problemas
- [x] T4: Botao "Atualizar" dispara refresh
- [x] T5: Mobile: banner compacto (375px)

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/buscar/components/DataQualityBanner.tsx` | Criar — banner consolidado |
| `frontend/app/buscar/components/SearchResults.tsx` | Modificar — usar DataQualityBanner |
| `frontend/app/buscar/components/CacheBanner.tsx` | Remover ou deprecated |
| `frontend/app/buscar/components/DegradationBanner.tsx` | Remover ou deprecated |
| `frontend/app/buscar/components/PartialResultsPrompt.tsx` | Remover ou deprecated |
| `frontend/app/buscar/page.tsx` | Modificar — simplificar banner logic |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | GTM-UX-002 | Error states complementam banner |
| Paralela | GTM-UX-003 | Retry unificado complementa |
