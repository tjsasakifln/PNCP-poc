# Redis Setup Instructions (Manual - Railway CLI Requires Interaction)

## Quick Setup (Railway CLI)

```bash
# Run this command and select "Database" when prompted:
railway add -d redis

# Then select "Redis" from the database options
```

## Alternative: Railway Dashboard

1. Go to https://railway.app/project/[your-project-id]
2. Click "New" → "Database" → "Redis"
3. Wait for provisioning (~30 seconds)
4. Click on Redis service → "Variables" tab
5. Copy the `REDIS_URL` variable

## Add to .env

```bash
# Backend .env
REDIS_URL=redis://default:[password]@[host]:[port]

# Or individual variables (Railway provides these):
REDIS_HOST=containers-us-west-xxx.railway.app
REDIS_PORT=6379
REDIS_PASSWORD=xxxxxxxxxxxxx
```

## Test Connection

```bash
cd backend
python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping(); print('✅ Redis connected!')"
```

## Story 171 Usage

Redis is used for:
- Feature flags caching (5min TTL)
- Key format: `features:{user_id}`
- Invalidation on: billing_period update, Stripe webhook

**Cache strategy implemented in:** `backend/routes/features.py`
