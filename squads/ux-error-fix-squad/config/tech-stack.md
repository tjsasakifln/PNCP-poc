# Tech Stack - UX Error Fix Squad

## Overview

This document describes the technology stack used in the investigation and resolution of free user search persistence bugs.

## Architecture

```
┌─────────────────────────────────────────────┐
│            Frontend (Next.js)               │
│  - React Components                         │
│  - State Management (React hooks)           │
│  - API Client (Axios)                       │
│  - Local Storage / Session Storage          │
└─────────────────┬───────────────────────────┘
                  │ HTTPS/REST
┌─────────────────▼───────────────────────────┐
│          Backend (FastAPI)                  │
│  - API Routes                               │
│  - Auth Middleware                          │
│  - Business Logic                           │
│  - Database ORM (SQLAlchemy)                │
└─────────────────┬───────────────────────────┘
                  │ PostgreSQL Protocol
┌─────────────────▼───────────────────────────┐
│       Database (Supabase/PostgreSQL)        │
│  - User accounts                            │
│  - Search history                           │
│  - Balance tracking                         │
│  - Auth tokens                              │
└─────────────────────────────────────────────┘
```

## Frontend Stack

### Core Framework
- **Next.js 14+**: React framework with App Router
- **React 18+**: UI library with hooks and context
- **TypeScript 5+**: Type-safe JavaScript

### State Management
- **React Hooks**: useState, useEffect, useContext
- **React Context**: Global state management
- **localStorage**: Client-side persistence
- **sessionStorage**: Temporary session data

### HTTP Client
- **Axios**: Promise-based HTTP client
  - Interceptors for auth
  - Error handling
  - Request/response transformation

### UI Components
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Component library
- **Lucide Icons**: Icon set

### Development Tools
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **TypeScript Compiler**: Type checking

## Backend Stack

### Core Framework
- **FastAPI**: Modern Python web framework
  - Async support
  - Auto-generated OpenAPI docs
  - Pydantic validation
  - Dependency injection

### Database
- **SQLAlchemy 2.0**: ORM and query builder
  - Async support
  - Transaction management
  - Relationship mapping
- **Alembic**: Database migrations
- **asyncpg**: PostgreSQL async driver

### Authentication
- **Supabase Auth**: Authentication service
  - JWT tokens
  - Session management
  - OAuth providers
- **python-jose**: JWT handling
- **passlib**: Password hashing

### Validation
- **Pydantic V2**: Data validation
  - Request/response models
  - Settings management
  - Type coercion

### Utilities
- **python-dotenv**: Environment variables
- **loguru**: Enhanced logging
- **httpx**: Async HTTP client

## Database

### Primary Database
- **Supabase (PostgreSQL)**: Cloud PostgreSQL
  - Version: 15+
  - Extensions: pgvector, uuid-ossp
  - Real-time subscriptions
  - Row-level security

### Key Tables

#### users
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  plan_id UUID REFERENCES plans(id)
);
```

#### user_balance
```sql
CREATE TABLE user_balance (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  searches_remaining INTEGER NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### search_history
```sql
CREATE TABLE search_history (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  query TEXT NOT NULL,
  results_count INTEGER,
  balance_deducted INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### plans
```sql
CREATE TABLE plans (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  searches_per_month INTEGER,
  price_monthly DECIMAL(10,2),
  is_free BOOLEAN DEFAULT FALSE
);
```

## API Endpoints

### Authentication
```
POST   /auth/login          - User login
POST   /auth/logout         - User logout
GET    /auth/me             - Get current user
POST   /auth/refresh        - Refresh token
```

### Search
```
POST   /api/buscar          - Perform search
GET    /api/buscar/history  - Get search history
```

### User & Balance
```
GET    /api/plans           - Get available plans
GET    /api/balance         - Get user balance
```

### Messages
```
GET    /api/messages/unread-count  - Get unread message count
```

## Development Environment

### Prerequisites
```bash
# Node.js
node >= 18.0.0
npm >= 9.0.0

# Python
python >= 3.11
pip >= 23.0

# Database
postgresql >= 15.0
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev         # Development server
npm run build       # Production build
npm run lint        # Linting
npm run test        # Run tests
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload  # Development server
pytest                     # Run tests
```

## Testing Stack

### Frontend Testing
- **Jest**: Unit testing framework
- **React Testing Library**: Component testing
- **Playwright**: E2E testing
- **MSW**: API mocking

### Backend Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **httpx**: API testing

### E2E Testing
```typescript
// Playwright test example
test('free user search flow', async ({ page }) => {
  await page.goto('/login');
  await login(page, 'test@example.com', 'password');

  await page.goto('/buscar');
  await performSearch(page, 'licitacao');

  await expect(page.locator('.results')).toBeVisible();
  await expect(page.locator('.balance')).toHaveText('9');
});
```

## Monitoring & Debugging

### Logging
- **Frontend**: Browser console, Sentry
- **Backend**: Loguru, structured logging
- **Database**: PostgreSQL logs

### Error Tracking
- **Sentry**: Error monitoring (optional)
- **Console logging**: Development
- **Log files**: Production

### Performance
- **Next.js Analytics**: Web vitals
- **FastAPI profiling**: Request timing
- **Database EXPLAIN**: Query optimization

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
```

### Backend (.env)
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
JWT_SECRET=xxx
LOG_LEVEL=INFO
```

## Dependencies

### Frontend Key Packages
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "typescript": "^5.3.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

### Backend Key Packages
```python
# requirements.txt
fastapi==0.108.0
uvicorn[standard]==0.25.0
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
alembic==1.13.0
loguru==0.7.2
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

## Security Considerations

### Authentication
- JWT tokens with expiration
- Secure cookie storage
- Token refresh mechanism
- Session validation

### Database
- Row-level security (RLS)
- Prepared statements
- Connection pooling
- Transaction isolation

### API
- CORS configuration
- Rate limiting
- Input validation
- SQL injection prevention

## Performance Optimization

### Frontend
- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization

### Backend
- Connection pooling
- Query optimization
- Caching strategies
- Async operations

### Database
- Indexes on frequently queried columns
- Query planning and optimization
- Connection pooling
- Read replicas (if needed)

## Deployment

### Frontend (Vercel)
```bash
# Production build
npm run build

# Deploy
vercel deploy --prod
```

### Backend (Railway/Heroku)
```bash
# Using Docker
docker build -t backend .
docker run -p 8000:8000 backend

# Direct deployment
railway up
```

### Database (Supabase)
- Managed PostgreSQL instance
- Automatic backups
- Connection pooling
- Point-in-time recovery

## References

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
