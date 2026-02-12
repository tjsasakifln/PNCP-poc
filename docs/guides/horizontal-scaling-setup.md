# Horizontal Scaling Setup Guide

**Prerequisites:** STORY-202 Track 3 implementation complete

This guide walks through enabling horizontal scaling for the SmartLic/BidIQ backend.

---

## Quick Start (Local Development)

### Option 1: Single Instance (No Setup Required)
```bash
# Just run the backend as usual
cd backend
uvicorn main:app --reload
```

**What happens:**
- Progress tracking uses in-memory mode
- Excel files saved to filesystem (tmpdir)
- Works perfectly for single-instance deployments
- **No Redis or storage setup needed**

---

### Option 2: Multi-Instance with Redis

**Step 1: Start Redis**
```bash
# Using Docker
docker run -d --name bidiq-redis -p 6379:6379 redis:7-alpine

# Or install Redis locally (Windows)
# Download from https://github.com/microsoftarchive/redis/releases
# Run redis-server.exe
```

**Step 2: Configure Backend**
```bash
# Add to backend/.env
echo "REDIS_URL=redis://localhost:6379" >> backend/.env
```

**Step 3: Start Multiple Backend Instances**
```bash
# Terminal 1: Backend on port 8000
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Backend on port 8001
cd backend
uvicorn main:app --reload --port 8001

# Terminal 3: Backend on port 8002
cd backend
uvicorn main:app --reload --port 8002
```

**Step 4: Configure Load Balancer**
Create `nginx.conf` (or use HAProxy):
```nginx
upstream backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 8080;
    location / {
        proxy_pass http://backend;
    }
}
```

**Step 5: Point Frontend to Load Balancer**
```bash
# frontend/.env.local
BACKEND_URL=http://localhost:8080
```

**Step 6: Test**
```bash
# Start frontend
cd frontend
npm run dev

# Open http://localhost:3000
# Run a search with multiple states
# Observe backend logs — requests distributed across instances
```

**Verify Redis Mode:**
```bash
# Check backend logs for:
✅ Redis connected successfully: localhost:6379
✅ Created progress tracker: abc123 (5 UFs) [mode: Redis]
```

---

## Production Deployment (Railway)

### Step 1: Add Redis Service
```bash
# Using Railway CLI
railway add redis

# Or via Railway Dashboard:
# 1. Click "New Service"
# 2. Select "Database" → "Redis"
# 3. Note the REDIS_URL in Variables tab
```

### Step 2: Set Environment Variable
```bash
# Automatically set by Railway if you added Redis via dashboard
# Or manually:
railway variables set REDIS_URL=redis://default:PASSWORD@redis.railway.internal:6379
```

### Step 3: Scale Backend
```bash
# Railway automatically scales when you add replicas
railway up backend --replicas 3

# Or via Dashboard:
# 1. Select backend service
# 2. Settings → Replicas → Set to 3
```

### Step 4: Deploy
```bash
railway up
```

**Verify Deployment:**
```bash
# Check logs for all replicas
railway logs backend

# Should see:
✅ Redis connected successfully: redis.railway.internal:6379
✅ Created progress tracker: xyz (3 UFs) [mode: Redis]
```

---

## Object Storage (Already Enabled)

**No setup required!** The system automatically uses Supabase Storage if credentials are set.

**Verify Storage is Active:**
```bash
# Run a search
# Check backend logs:
✅ Excel uploaded to storage: 20260211_143022_abc123.xlsx (TTL=3600s)

# Check frontend logs:
✅ Excel available via signed URL (TTL: 60min)
```

**If you see fallback mode:**
```bash
# Backend log:
⚠️ Storage upload failed, falling back to base64 encoding

# Possible causes:
# 1. SUPABASE_SERVICE_ROLE_KEY is invalid
# 2. Service role lacks storage permissions
# 3. Network issue connecting to Supabase

# Fix:
# 1. Check .env has correct SUPABASE_SERVICE_ROLE_KEY
# 2. Verify key has storage.buckets.* permissions in Supabase dashboard
# 3. Check network connectivity to Supabase
```

---

## Monitoring & Debugging

### Check Current Mode
```bash
# Look for log lines during search:
Created progress tracker: abc123 (5 UFs) [mode: Redis]
# or
Created progress tracker: abc123 (5 UFs) [mode: in-memory]

Excel uploaded to storage: ... (TTL=3600s)
# or
Excel saved to filesystem: /tmp/bidiq_xyz.xlsx (fallback mode)
```

### Redis Health Check
```bash
# Connect to Redis
redis-cli

# Check keys
KEYS bidiq:progress:*

# Monitor events
PSUBSCRIBE bidiq:progress:*:events

# Check memory usage
INFO memory
```

### Storage Health Check
```bash
# Check Supabase Storage via dashboard
# https://app.supabase.com/project/{PROJECT_ID}/storage/buckets

# Or via API
curl -H "Authorization: Bearer SERVICE_ROLE_KEY" \
  https://fqqyovlzdzimiwfofdjk.supabase.co/storage/v1/bucket/excel-reports
```

---

## Performance Tuning

### Redis Connection Pooling
```python
# backend/redis_client.py
# Already configured with:
# - socket_connect_timeout=3s
# - socket_timeout=3s
# - decode_responses=True

# For production, consider:
# - max_connections=50
# - retry_on_timeout=True
```

### Storage Upload Concurrency
```python
# backend/storage.py
# Current: Sequential upload after Excel generation

# Future optimization:
# - Upload in background task (asyncio.create_task)
# - Return search results immediately
# - Stream signed URL to client when ready
```

---

## Troubleshooting

### Issue: SSE events not received across instances

**Symptoms:**
- Search runs on instance A
- SSE connection on instance B
- No progress updates in frontend

**Debug:**
```bash
# Check Redis mode is enabled
grep "mode: Redis" backend/logs/*.log

# Check Redis pub/sub is working
redis-cli
> PSUBSCRIBE bidiq:progress:*:events
# Trigger search, verify events published
```

**Fix:**
```bash
# Ensure REDIS_URL is set on ALL backend instances
railway variables set REDIS_URL=redis://...

# Restart all instances
railway restart backend
```

---

### Issue: Excel download fails with 404

**Symptoms:**
- Search completes successfully
- Download button shows error: "Download expirado ou inválido"

**Debug:**
```bash
# Check download mode in frontend logs
# Should see one of:
✅ Excel available via signed URL (TTL: 60min)
# or
✅ Excel saved to filesystem: /tmp/bidiq_xyz.xlsx (fallback mode)

# If neither appears, check backend response
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/buscar \
  -d '{"ufs":["SP"],...}' | jq '.download_url, .download_id'
```

**Fix:**
```bash
# Option 1: Enable storage (preferred)
# Check SUPABASE_SERVICE_ROLE_KEY in .env

# Option 2: Use filesystem fallback
# Ensure tmpdir is writable
# Check backend has write permissions
```

---

### Issue: High memory usage with Redis

**Symptoms:**
- Redis memory grows over time
- Old progress trackers not cleaned up

**Debug:**
```bash
redis-cli
> KEYS bidiq:progress:*
> TTL bidiq:progress:abc123
# Should be < 300 seconds (5 minutes)
```

**Fix:**
```bash
# Check TTL is set correctly
# backend/progress.py line ~140:
await redis.expire(key, _TRACKER_TTL)  # Should be 300

# Manually cleanup if needed
redis-cli
> DEL bidiq:progress:old-search-id
```

---

## Cost Estimation

### Redis (Railway)
- **Tier:** Redis 7 Starter
- **Cost:** ~$5/month (512MB RAM)
- **Capacity:** ~5000 concurrent searches

### Supabase Storage
- **Free Tier:** 1GB storage
- **Excel file size:** ~50KB average
- **Capacity:** ~20,000 files
- **TTL:** 60 minutes (auto-cleanup)
- **Expected usage:** < 100MB/month

**Total additional cost:** $5-10/month for horizontal scaling capability

---

## Next Steps

1. ✅ Enable Redis in staging
2. ✅ Scale to 2 instances
3. ✅ Run load test (100+ concurrent searches)
4. ✅ Monitor Redis memory usage
5. ✅ Monitor Supabase Storage quota
6. ✅ Enable in production
7. ✅ Scale to 3+ instances based on load

---

**For questions or issues, see:**
- `STORY-202-TRACK-3-IMPLEMENTATION.md` (technical details)
- `backend/redis_client.py` (Redis implementation)
- `backend/storage.py` (Storage implementation)
