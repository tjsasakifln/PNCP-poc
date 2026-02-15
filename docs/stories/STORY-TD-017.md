# STORY-TD-017: Backend Scalability -- Redis, Storage, Routes

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2-3: Consolidacao e Refatoracao / Qualidade

## Prioridade
P2

## Estimativa
24h

## Descricao

Esta story resolve problemas de escalabilidade do backend que impedem scaling horizontal e limpeza de recursos.

1. **Progress tracker -> Redis pub/sub primario (SYS-04, HIGH, 8h)** -- `_active_trackers` dict e o registro primario em `progress.py`. Redis pub/sub existe mas e secundario. Se Railway escalar para 2+ instancias, estado SSE sera fragmentado. Migrar Redis para registro primario com fallback in-memory.

2. **Auth token cache compartilhado (SYS-05, HIGH, 4h)** -- `_token_cache` dict em `auth.py` nao e compartilhado entre instancias. Cada instancia mantem cache independente, causando fragmentacao e validacoes desnecessarias. Migrar para Redis com TTL.

3. **Excel tmpdir -> Supabase Storage signed URL (SYS-08, HIGH, 4h)** -- Frontend `app/api/buscar/route.ts` linhas 197-223 grava Excel como base64 em tmpdir como fallback. Nao limpo em crash, nao escalavel. Usar Supabase Storage com signed URLs e tempo de expiracao.

4. **Dual route mounting cleanup (SYS-09, MEDIUM, 4h)** -- Backend monta rotas 2x (root + `/v1/` prefix), dobrando tabela de rotas. Sunset date: 2026-06-01. Preparar migracao: deprecation warnings em rotas root, migrar frontend para usar `/v1/` prefix.

5. **Legacy plan seeds cleanup (SYS-06, HIGH, 4h)** -- Migration 001 cria planos `free`, `pack_5`; codigo usa `free_trial`, `consultor_agil`. Traducao em `quota.py` linhas 525-531 e fragil. Criar migration que atualiza seeds ou remove dependencia de seeds legados.

## Itens de Debito Relacionados
- SYS-04 (HIGH): In-memory progress tracker nao escalavel horizontalmente
- SYS-05 (HIGH): In-memory auth token cache nao compartilhado entre instancias
- SYS-08 (HIGH): Excel base64 fallback grava em tmpdir (nao limpo em crash)
- SYS-09 (MEDIUM): Backend routes montadas 2x (root + /v1/ prefix)
- SYS-06 (HIGH): Legacy plan seeds vs current plan IDs

## Criterios de Aceite

### Redis Progress Tracker
- [ ] Redis e registro primario de progress state
- [ ] In-memory e fallback (quando Redis indisponivel)
- [ ] SSE funciona com 2 instancias simuladas (requests para instancias diferentes recebem progress)
- [ ] Publicacao e consumo via Redis pub/sub
- [ ] TTL em progress entries (auto-cleanup)

### Redis Auth Cache
- [ ] Token cache usa Redis com TTL
- [ ] Cache compartilhado entre instancias
- [ ] Fallback in-memory quando Redis indisponivel
- [ ] Performance: token validation nao adiciona > 5ms de latencia

### Excel Storage
- [ ] Excel gerado e enviado para Supabase Storage
- [ ] Signed URL retornado ao frontend (com expiracao de 10 minutos)
- [ ] Nenhum arquivo temporario em tmpdir para Excel
- [ ] Cleanup automatico via expiracao de signed URL
- [ ] Download funciona corretamente via signed URL

### Route Cleanup
- [ ] Rotas root incluem header `Deprecation: true` (RFC 8594)
- [ ] Rotas root incluem header `Sunset: 2026-06-01`
- [ ] Frontend migrado para usar `/v1/` prefix
- [ ] Logs indicam quando rota root e usada (para monitorar migracao)

### Plan Seeds
- [ ] `PLAN_TYPE_MAP` em quota.py removido ou simplificado
- [ ] Migration cria plan seeds consistentes com nomes atuais
- [ ] Nenhum mapping "free" -> "free_trial" necessario em runtime

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| -- | SSE progress com Redis como primary | Integracao | P2 |
| -- | Token cache hit/miss com Redis | Unitario | P2 |
| -- | Download Excel via signed URL | E2E | P2 |
| -- | Rotas /v1/ retornam mesmos dados que root | Integracao | P2 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (independente, mas SYS-06 preferivelmente apos TD-001)

## Riscos
- Redis downtime causa fallback para in-memory, perdendo beneficio de scaling.
- Supabase Storage pode ter limites de tamanho/throughput. Verificar para Excel > 5MB.
- Route migration requer coordenacao frontend/backend.
- Plan seeds cleanup pode afetar usuarios existentes se nao cuidadoso.

## Rollback Plan
- Redis: manter fallback in-memory como safety net permanente.
- Storage: manter tmpdir como fallback por 2 sprints.
- Routes: manter dual mounting ate deadline (2026-06-01).
- Plan seeds: migration reversivel.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao + E2E)
- [ ] CI/CD green
- [ ] Redis health check incluido em `/health` endpoint
- [ ] Documentacao atualizada (arquitetura de scalability)
- [ ] Deploy em staging verificado
- [ ] SSE progress testado com multiplas instancias
