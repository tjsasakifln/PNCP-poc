# Source Tree - UX Error Fix Squad

## Repository Structure

```
licitacoes/
├── frontend/                      # Next.js frontend application
│   ├── app/                       # App Router pages and layouts
│   │   ├── auth/                  # Authentication pages
│   │   │   ├── callback/          # OAuth callback
│   │   │   └── login/             # Login page
│   │   ├── buscar/                # Search page (CRITICAL)
│   │   │   └── page.tsx           # Main search interface
│   │   ├── components/            # React components
│   │   │   ├── AuthProvider.tsx   # Auth context provider
│   │   │   ├── SearchForm.tsx     # Search form component
│   │   │   └── ResultsList.tsx    # Search results display
│   │   ├── profile/               # User profile
│   │   └── layout.tsx             # Root layout
│   ├── lib/                       # Utility libraries
│   │   ├── api/                   # API client functions
│   │   │   ├── auth.ts            # Auth API calls
│   │   │   ├── buscar.ts          # Search API calls (CRITICAL)
│   │   │   └── plans.ts           # Plans API calls
│   │   ├── hooks/                 # Custom React hooks
│   │   │   ├── useAuth.ts         # Auth hook
│   │   │   ├── useBalance.ts      # Balance tracking hook
│   │   │   └── useSearchState.ts  # Search state persistence (CRITICAL)
│   │   ├── utils/                 # Utility functions
│   │   │   ├── errors.ts          # Error handling utilities
│   │   │   └── storage.ts         # LocalStorage utilities
│   │   └── supabase.ts            # Supabase client config
│   ├── middleware.ts              # Next.js middleware (auth check)
│   ├── .env.local                 # Environment variables
│   ├── next.config.js             # Next.js configuration
│   ├── package.json               # Dependencies
│   └── tsconfig.json              # TypeScript config
│
├── backend/                       # FastAPI backend application
│   ├── api/                       # API routes
│   │   ├── auth.py                # Auth endpoints
│   │   ├── buscar.py              # Search endpoints (CRITICAL)
│   │   └── plans.py               # Plans endpoints
│   ├── models/                    # Database models
│   │   ├── user.py                # User model
│   │   ├── search_history.py     # SearchHistory model (CRITICAL)
│   │   ├── user_balance.py       # UserBalance model (CRITICAL)
│   │   └── plan.py                # Plan model
│   ├── schemas/                   # Pydantic schemas
│   │   ├── auth.py                # Auth request/response schemas
│   │   ├── buscar.py              # Search schemas
│   │   └── user.py                # User schemas
│   ├── services/                  # Business logic
│   │   ├── auth_service.py        # Auth operations
│   │   ├── search_service.py      # Search operations (CRITICAL)
│   │   └── balance_service.py     # Balance operations (CRITICAL)
│   ├── utils/                     # Utility functions
│   │   ├── database.py            # Database connection
│   │   ├── logging.py             # Logging configuration
│   │   └── errors.py              # Error handling
│   ├── middleware/                # Middleware
│   │   └── auth_middleware.py     # JWT validation (CRITICAL)
│   ├── migrations/                # Alembic migrations
│   │   └── versions/              # Migration scripts
│   ├── tests/                     # Test suite
│   │   ├── test_auth.py           # Auth tests
│   │   ├── test_buscar.py         # Search tests (CRITICAL)
│   │   └── test_balance.py        # Balance tests (CRITICAL)
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration
│   ├── requirements.txt           # Python dependencies
│   └── .env                       # Environment variables
│
├── database/                      # Database scripts
│   ├── schema.sql                 # Database schema
│   └── seeds/                     # Seed data
│       ├── users.sql              # Test users
│       └── plans.sql              # Plan data
│
├── docs/                          # Documentation
│   ├── stories/                   # User stories
│   ├── architecture/              # Architecture docs
│   └── api/                       # API documentation
│
├── squads/                        # AIOS squads
│   └── ux-error-fix-squad/        # This squad
│       ├── agents/                # Agent definitions
│       ├── tasks/                 # Task definitions
│       ├── config/                # Squad configuration
│       ├── squad.yaml             # Squad manifest
│       └── README.md              # Squad documentation
│
└── .github/                       # GitHub configuration
    └── workflows/                 # CI/CD workflows
```

## Critical Files for This Squad

### Frontend Files (State Persistence Issues)

#### `/frontend/app/buscar/page.tsx`
**Purpose**: Main search interface
**Key Functions**:
- `handleSearch()` - Executes search
- `handleStateRestore()` - Restores state on mount
- `handleNavigation()` - Persists state before navigation

**Issues to Investigate**:
- State not persisted to localStorage
- State cleared on navigation
- Search results lost

#### `/frontend/lib/hooks/useSearchState.ts`
**Purpose**: Custom hook for search state persistence
**Key Functions**:
- `persistState()` - Save state to localStorage
- `restoreState()` - Load state from localStorage
- `clearState()` - Clear persisted state

**Issues to Investigate**:
- localStorage write failures
- State serialization issues
- Timing issues with state save

#### `/frontend/lib/api/buscar.ts`
**Purpose**: Search API client
**Key Functions**:
- `searchLicitacoes()` - Call search API
- `getSearchHistory()` - Fetch search history
- `handleApiError()` - Error handling

**Issues to Investigate**:
- Error responses not handled correctly
- History API not called after search
- Balance not tracked properly

#### `/frontend/middleware.ts`
**Purpose**: Authentication middleware
**Key Functions**:
- `verifyAuth()` - Check auth token
- `redirectToLogin()` - Redirect unauthenticated users

**Issues to Investigate**:
- Auth failures causing state loss
- Token expiration mid-operation
- Session inconsistency

### Backend Files (Balance & History Issues)

#### `/backend/api/buscar.py`
**Purpose**: Search API endpoints
**Key Endpoints**:
- `POST /api/buscar` - Execute search
- `GET /api/buscar/history` - Get history

**Issues to Investigate**:
- Transaction not committed
- Balance deducted but search fails
- History not saved

#### `/backend/services/search_service.py`
**Purpose**: Search business logic
**Key Functions**:
- `execute_search()` - Main search logic
- `save_to_history()` - Save search history
- `consume_balance()` - Deduct balance

**Issues to Investigate**:
- Missing transaction management
- Rollback not working
- Atomicity issues

#### `/backend/services/balance_service.py`
**Purpose**: Balance management
**Key Functions**:
- `deduct_balance()` - Deduct search credits
- `refund_balance()` - Refund on failure
- `get_balance()` - Get current balance

**Issues to Investigate**:
- Balance deducted without rollback
- Concurrent deduction issues
- Inconsistent balance tracking

#### `/backend/models/search_history.py`
**Purpose**: SearchHistory database model
**Key Fields**:
- `user_id` - User identifier
- `query` - Search query
- `results_count` - Number of results
- `balance_deducted` - Credits used
- `created_at` - Timestamp

**Issues to Investigate**:
- Records not inserted
- Transaction not committed
- Foreign key issues

#### `/backend/middleware/auth_middleware.py`
**Purpose**: JWT validation middleware
**Key Functions**:
- `validate_token()` - Verify JWT
- `get_current_user()` - Extract user from token
- `refresh_token()` - Refresh expired token

**Issues to Investigate**:
- Token validation failures
- User context not set
- Auth state inconsistency

### Database Tables (Critical)

#### `users`
```sql
id, email, created_at, plan_id
```

#### `user_balance` (CRITICAL)
```sql
id, user_id, searches_remaining, updated_at
```
**Issues**: Balance deducted but not committed

#### `search_history` (CRITICAL)
```sql
id, user_id, query, results_count, balance_deducted, created_at
```
**Issues**: Records not inserted or committed

#### `plans`
```sql
id, name, searches_per_month, price_monthly, is_free
```

### Configuration Files

#### Frontend
- `/frontend/.env.local` - API URL, Supabase config
- `/frontend/next.config.js` - Next.js settings
- `/frontend/tsconfig.json` - TypeScript config

#### Backend
- `/backend/.env` - Database URL, JWT secret, Supabase config
- `/backend/config.py` - Application config
- `/backend/requirements.txt` - Dependencies

## Investigation Checklist

### Frontend Investigation
- [ ] Check `/frontend/app/buscar/page.tsx` for state persistence
- [ ] Review `/frontend/lib/hooks/useSearchState.ts` implementation
- [ ] Analyze `/frontend/lib/api/buscar.ts` error handling
- [ ] Verify `/frontend/middleware.ts` auth flow
- [ ] Check localStorage writes in browser DevTools
- [ ] Review React DevTools for state changes

### Backend Investigation
- [ ] Check `/backend/api/buscar.py` transaction management
- [ ] Review `/backend/services/search_service.py` atomicity
- [ ] Analyze `/backend/services/balance_service.py` deduction logic
- [ ] Verify `/backend/models/search_history.py` commits
- [ ] Check `/backend/middleware/auth_middleware.py` validation
- [ ] Review database transaction logs

### Database Investigation
- [ ] Query `user_balance` table for consistency
- [ ] Query `search_history` table for missing records
- [ ] Check database transaction logs
- [ ] Verify foreign key constraints
- [ ] Analyze query performance with EXPLAIN

### Logs to Check
- **Frontend**: Browser console, Network tab
- **Backend**: `/backend/logs/app.log`
- **Database**: PostgreSQL logs
- **Supabase**: Auth logs, Database logs

## Common Bug Patterns

### Pattern 1: State Loss on Navigation
```typescript
// Bad: State not persisted
const [results, setResults] = useState([]);
// Navigates away -> state lost

// Good: State persisted
useEffect(() => {
  localStorage.setItem('results', JSON.stringify(results));
}, [results]);
```

### Pattern 2: Missing Transaction Commit
```python
# Bad: Transaction not committed
async def save_history(db, data):
    record = SearchHistory(**data)
    db.add(record)
    # Missing: await db.commit()

# Good: Explicit commit
async def save_history(db, data):
    async with db.begin():
        record = SearchHistory(**data)
        db.add(record)
        await db.commit()
```

### Pattern 3: Balance Without Rollback
```python
# Bad: Balance deducted without rollback
await deduct_balance(user_id, 1)
try:
    result = await search()
except Exception:
    # Balance not refunded!
    raise

# Good: Atomic transaction
async with db.begin():
    await deduct_balance(user_id, 1)
    result = await search()
    # Automatically rolls back on error
```

## Testing Locations

### Unit Tests
- `/frontend/lib/hooks/__tests__/useSearchState.test.ts`
- `/backend/tests/test_buscar.py`
- `/backend/tests/test_balance.py`

### Integration Tests
- `/frontend/__tests__/buscar.integration.test.tsx`
- `/backend/tests/integration/test_search_flow.py`

### E2E Tests
- `/tests/e2e/free-user-search.spec.ts`

## References

- [Project README](/README.md)
- [Architecture Documentation](/docs/architecture/)
- [API Documentation](/docs/api/)
- [Database Schema](/database/schema.sql)
