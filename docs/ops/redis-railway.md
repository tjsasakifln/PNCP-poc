# Redis on Railway — Operational Guide

**Service:** `Redis-hejG`
**Project:** `bidiq-uniformes`
**Internal URL:** `redis://default:***@redis-hejg.railway.internal:6379`
**Public URL:** `redis://default:***@yamanote.proxy.rlwy.net:40978`

---

## 1. Provisioning

Redis was provisioned via Railway dashboard as the `Redis-hejG` service.

### Environment Variable

The backend service (`bidiq-backend`) reads `REDIS_URL` from its environment variables. This was set to the internal Railway URL for low-latency communication within the same private network.

```bash
# Verify REDIS_URL is set
railway variables --service bidiq-backend | grep REDIS

# Set/update REDIS_URL if needed
railway variables --set "REDIS_URL=redis://default:<password>@redis-hejg.railway.internal:6379" --service bidiq-backend
```

### Architecture

```
bidiq-backend (worker A) ──┐
                           ├── redis-hejg.railway.internal:6379
bidiq-backend (worker B) ──┘
```

- **Internal networking**: All traffic stays within Railway's private network
- **No public exposure needed**: Backend connects via internal domain
- **Gunicorn workers**: 2 UvicornWorker processes share the same Redis instance

### What Redis Provides

| Feature | Without Redis | With Redis |
|---------|--------------|------------|
| Cache L2 | Per-worker (isolated) | Shared (unified) |
| Circuit breaker | Per-worker (divergent) | Shared (consistent) |
| Rate limiter | Per-worker (bypassable) | Shared (accurate) |
| SSE progress | asyncio.Queue (local) | pub/sub (cross-worker) |
| Cache hit rate | ~50% potential | 100% potential |

---

## 2. Monitoring

### Health Endpoint

```bash
# Check Redis status via health endpoint
curl -s https://api.smartlic.tech/health | python -m json.tool

# Expected response includes:
# "dependencies": { "redis": "healthy" }
# "redis_metrics": { "connected": true, "latency_ms": 0.5, "memory_used_mb": 1.2 }
```

### Railway Logs

```bash
# Stream backend logs (look for Redis messages)
railway logs --service bidiq-backend

# Successful startup:
# "Redis pool connected: redis-hejg.railway.internal:6379 (max_connections=20)"

# Fallback mode:
# "REDIS_URL not set — Redis disabled, using InMemoryCache fallback"
# "Redis connection failed: ... — using InMemoryCache fallback"
```

### Redis Service Metrics

Railway provides built-in metrics for the Redis service:
- Memory usage
- Connected clients
- Commands processed/sec
- Network I/O

Access via: Railway Dashboard > bidiq-uniformes > Redis-hejG > Metrics

### Key Indicators

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Latency (ping) | < 5ms | 5-50ms | > 50ms |
| Memory | < 50MB | 50-200MB | > 200MB |
| Connected clients | 1-40 | 40-80 | > 80 |
| Health endpoint | `"redis": "healthy"` | — | `"redis": "unavailable"` |

---

## 3. Failover

### Automatic Failover (Built-In)

The backend has automatic Redis failover built into `redis_pool.py`:

1. **Startup**: If Redis is unavailable, logs warning and uses `InMemoryCache`
2. **Runtime**: All Redis operations have try/except — failures log warnings, never crash
3. **SSE**: Falls back to `asyncio.Queue` for progress events (single-worker only)

### Manual Failover

If Redis is causing issues in production:

```bash
# Option 1: Disable Redis (zero downtime)
railway variables --set "REDIS_URL=" --service bidiq-backend
# Railway auto-redeploys. Backend falls back to InMemoryCache.

# Option 2: Restart Redis service
# Via Railway Dashboard: Redis-hejG > Restart

# Option 3: Re-enable Redis after fix
railway variables --set "REDIS_URL=redis://default:<password>@redis-hejg.railway.internal:6379" --service bidiq-backend
```

### Rollback Verification

After disabling Redis:
1. Health endpoint should show `"redis": "not_configured"`
2. Searches should still work (InMemoryCache fallback)
3. SSE progress may be limited to same-worker events

---

## 4. Manual Cache Operations

### Clear All Cache

```bash
# Connect via public URL (from local machine)
redis-cli -u "redis://default:<password>@yamanote.proxy.rlwy.net:40978"

# Or via Railway run (from backend context)
railway run --service bidiq-backend python -c "
import asyncio
from redis_pool import get_redis_pool
async def flush():
    r = await get_redis_pool()
    if r:
        await r.flushdb()
        print('Cache cleared')
    else:
        print('Redis not available')
asyncio.run(flush())
"
```

### Clear Specific Keys

```bash
# Clear all search cache entries
redis-cli -u "<url>" KEYS "bidiq:search:*" | xargs redis-cli -u "<url>" DEL

# Clear all progress tracking entries
redis-cli -u "<url>" KEYS "bidiq:progress:*" | xargs redis-cli -u "<url>" DEL

# Clear specific search cache
redis-cli -u "<url>" DEL "bidiq:search:<hash>"
```

### Inspect Cache Contents

```bash
# Count keys by prefix
redis-cli -u "<url>" KEYS "bidiq:*" | wc -l

# Check memory usage for a key
redis-cli -u "<url>" MEMORY USAGE "bidiq:search:<hash>"

# Check TTL for a key
redis-cli -u "<url>" TTL "bidiq:search:<hash>"

# Get Redis info
redis-cli -u "<url>" INFO memory
redis-cli -u "<url>" INFO clients
redis-cli -u "<url>" INFO stats
```

### Key Naming Convention

| Pattern | Purpose | TTL |
|---------|---------|-----|
| `bidiq:search:<hash>` | Search result cache | 24h |
| `bidiq:progress:<search_id>` | SSE progress metadata | 5min |
| `bidiq:progress:<search_id>:events` | SSE pub/sub channel | N/A |

---

## Security Notes

- `REDIS_URL` contains credentials — never commit to repository
- Railway manages the URL as a service environment variable (secure by default)
- Connection is internal (same Railway private network, no public exposure needed)
- Public URL (`yamanote.proxy.rlwy.net:40978`) exists but should only be used for debugging
