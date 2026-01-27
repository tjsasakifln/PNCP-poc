# BidIQ Uniformes - Frontend Specification & Audit

**Project:** BidIQ Uniformes - POC v0.2
**Date:** January 2026
**Version:** 1.0
**Status:** BROWNFIELD DISCOVERY - PHASE 3
**Documented by:** @ux-design-expert

---

## Executive Summary

The BidIQ frontend is designed as a **single-page application (SPA)** using Next.js 14+ with App Router. Current status: **Partial implementation** - dependencies configured but application structure incomplete. This specification documents the intended architecture, components, and current gaps.

**Key Characteristics:**
- Minimal, focused UI for B2B procurement search
- Multi-select UF (state) filter with 27 options
- Date range picker with smart defaults (last 7 days)
- Results display with GPT-powered summaries
- Direct Excel export to browser
- Mobile-responsive design via Tailwind CSS

**Current Status:** Package dependencies configured, but Next.js app structure not yet created (Issue #21)

---

## 1. Frontend Technology Stack

### 1.1 Core Framework

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| Next.js | 14+ | Full-stack React framework, App Router | ✅ Configured (Issue #21) |
| React | 18+ | UI component library | ✅ Configured |
| TypeScript | 5.3+ | Type-safe development | ✅ Configured |
| Tailwind CSS | 3.4+ | Utility-first styling | ✅ Configured |
| Node.js | 18+ | Runtime | ✅ Required |

### 1.2 Development Dependencies

```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.4",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "prettier": "^3.0.3",
    "eslint": "^8",
    "eslint-config-next": "^14"
  }
}
```

### 1.3 Build & Deployment

- **Build Tool:** Next.js built-in
- **Output:** Standalone server + static assets
- **Target:** Vercel or self-hosted Node.js
- **Bundle Optimization:** Next.js automatic code splitting

---

## 2. Application Structure (Intended)

### 2.1 Directory Layout

```
frontend/
├── app/                          # App Router directory
│   ├── layout.tsx                # Root layout (global styles, providers)
│   ├── page.tsx                  # Main search page (/)
│   ├── api/                      # API route handlers
│   │   ├── buscar/
│   │   │   └── route.ts          # POST /api/buscar → proxy to backend
│   │   └── download/
│   │       └── route.ts          # GET /api/download → serve Excel
│   └── [components]/             # (To be created)
│       ├── UFSelector.tsx        # Multi-select UF buttons
│       ├── DateRangePicker.tsx   # Date range input
│       ├── ResultsTable.tsx      # Results display
│       ├── SummaryCard.tsx       # GPT summary display
│       ├── LoadingSkeletons.tsx  # Loading states
│       └── ErrorBoundary.tsx     # Error handling
│
├── styles/                       # (Optional if needed beyond Tailwind)
│   └── globals.css               # Global Tailwind imports
│
├── hooks/                        # Custom React hooks
│   ├── useSearch.ts              # Encapsulate search logic
│   └── usePagination.ts          # Pagination state (future)
│
├── lib/                          # Utilities
│   ├── api-client.ts             # API communication
│   ├── constants.ts              # UFs, defaults, colors
│   └── utils.ts                  # Helper functions
│
├── types/                        # TypeScript type definitions
│   ├── api.ts                    # API response types
│   └── domain.ts                 # Domain models
│
├── __tests__/                    # Test files
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   └── integration/
│
├── public/                       # Static assets
│   └── favicon.ico
│
├── next.config.js                # Next.js configuration
├── tsconfig.json                 # TypeScript configuration
├── jest.config.js                # Jest testing configuration
├── tailwind.config.js            # Tailwind configuration
└── package.json
```

---

## 3. Component Architecture

### 3.1 Page Structure: Main Search Page (`page.tsx`)

```typescript
// Main SPA with all search functionality on single page

export default function SearchPage() {
  const [ufs, setUfs] = useState<Set<string>>(new Set());
  const [dateRange, setDateRange] = useState({
    start: getLastNDays(7), // Default: last 7 days
    end: new Date().toISOString().split('T')[0]
  });
  const [results, setResults] = useState<Licitacao[]>([]);
  const [summary, setSummary] = useState<ResumoLicitacoes | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadId, setDownloadId] = useState<string | null>(null);

  const handleSearch = async () => {
    // POST to /api/buscar
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <h1>BidIQ Uniformes</h1>
        <p>Descoberta Automática de Oportunidades de Compra Pública</p>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Filters Section */}
        <section className="bg-white rounded-lg shadow p-6 mb-6">
          <UFSelector ufs={ufs} onChange={setUfs} />
          <DateRangePicker dateRange={dateRange} onChange={setDateRange} />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? "Buscando..." : "Buscar Oportunidades"}
          </button>
        </section>

        {/* Summary Card (if results) */}
        {summary && <SummaryCard resumo={summary} />}

        {/* Results Section */}
        {results.length > 0 && (
          <section className="mt-6">
            <h2>Resultados ({results.length})</h2>
            <ResultsTable results={results} downloadId={downloadId} />
          </section>
        )}

        {/* Loading State */}
        {loading && <LoadingSkeletons count={5} />}

        {/* Error State */}
        {error && <ErrorAlert message={error} />}
      </main>
    </div>
  );
}
```

### 3.2 Component: UF Selector

```typescript
interface UFSelectorProps {
  ufs: Set<string>;
  onChange: (ufs: Set<string>) => void;
}

export function UFSelector({ ufs, onChange }: UFSelectorProps) {
  const UFS = [
    // 27 Brazilian states
    { code: 'AC', name: 'Acre' },
    { code: 'AL', name: 'Alagoas' },
    { code: 'AP', name: 'Amapá' },
    { code: 'AM', name: 'Amazonas' },
    { code: 'BA', name: 'Bahia' },
    // ... 22 more states
    { code: 'TO', name: 'Tocantins' }
  ];

  const toggleUF = (code: string) => {
    const newUFs = new Set(ufs);
    if (newUFs.has(code)) {
      newUFs.delete(code);
    } else {
      newUFs.add(code);
    }
    onChange(newUFs);
  };

  return (
    <div className="mb-6">
      <label className="block text-sm font-medium mb-2">
        Estados (Selecione um ou mais)
      </label>
      <div className="grid grid-cols-9 gap-2">
        {UFS.map(uf => (
          <button
            key={uf.code}
            onClick={() => toggleUF(uf.code)}
            className={`
              px-3 py-2 rounded text-sm font-medium transition-colors
              ${ufs.has(uf.code)
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }
            `}
            title={uf.name}
          >
            {uf.code}
          </button>
        ))}
      </div>
    </div>
  );
}
```

### 3.3 Component: Date Range Picker

```typescript
interface DateRangePickerProps {
  dateRange: { start: string; end: string };
  onChange: (range: { start: string; end: string }) => void;
}

export function DateRangePicker({ dateRange, onChange }: DateRangePickerProps) {
  return (
    <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium mb-1">Data Inicial</label>
        <input
          type="date"
          value={dateRange.start}
          onChange={e => onChange({ ...dateRange, start: e.target.value })}
          className="w-full px-3 py-2 border rounded"
        />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Data Final</label>
        <input
          type="date"
          value={dateRange.end}
          onChange={e => onChange({ ...dateRange, end: e.target.value })}
          className="w-full px-3 py-2 border rounded"
        />
      </div>
    </div>
  );
}
```

### 3.4 Component: Results Table

```typescript
interface ResultsTableProps {
  results: Licitacao[];
  downloadId: string | null;
}

export function ResultsTable({ results, downloadId }: ResultsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-100 border-b">
          <tr>
            <th className="px-4 py-2 text-left">Código</th>
            <th className="px-4 py-2 text-left">Objeto</th>
            <th className="px-4 py-2 text-left">Órgão</th>
            <th className="px-4 py-2 text-left">UF</th>
            <th className="px-4 py-2 text-right">Valor</th>
            <th className="px-4 py-2 text-left">Status</th>
            <th className="px-4 py-2 text-left">Link</th>
          </tr>
        </thead>
        <tbody>
          {results.map(licitacao => (
            <tr key={licitacao.codigo} className="border-b hover:bg-gray-50">
              <td className="px-4 py-2 font-mono text-xs">{licitacao.codigo}</td>
              <td className="px-4 py-2">{licitacao.objeto}</td>
              <td className="px-4 py-2">{licitacao.orgao}</td>
              <td className="px-4 py-2 font-semibold">{licitacao.uf}</td>
              <td className="px-4 py-2 text-right font-semibold">
                R$ {(licitacao.valor / 1000).toFixed(1)}k
              </td>
              <td className="px-4 py-2">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                  {licitacao.status}
                </span>
              </td>
              <td className="px-4 py-2">
                <a
                  href={licitacao.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  PNCP ↗
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {downloadId && (
        <button
          onClick={() => window.location.href = `/api/download?id=${downloadId}`}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
        >
          📥 Baixar Excel
        </button>
      )}
    </div>
  );
}
```

### 3.5 Component: Summary Card

```typescript
export function SummaryCard({ resumo }: { resumo: ResumoLicitacoes }) {
  return (
    <div className="bg-blue-50 border-l-4 border-blue-600 p-6 rounded mb-6">
      <h2 className="font-bold text-lg mb-3">📊 Resumo Executivo (IA)</h2>

      <p className="text-gray-700 mb-4">{resumo.resumo_executivo}</p>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {resumo.total_oportunidades}
          </div>
          <div className="text-sm text-gray-600">Oportunidades</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            R$ {(resumo.valor_total / 1_000_000).toFixed(1)}M
          </div>
          <div className="text-sm text-gray-600">Valor Total</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {(resumo.valor_total / resumo.total_oportunidades / 1000).toFixed(0)}k
          </div>
          <div className="text-sm text-gray-600">Valor Médio</div>
        </div>
      </div>

      <div className="mb-4">
        <h3 className="font-semibold text-sm mb-2">🎯 Destaques:</h3>
        <ul className="list-disc list-inside text-sm text-gray-700">
          {resumo.destaques.map((destaque, i) => (
            <li key={i}>{destaque}</li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="font-semibold text-sm mb-2">💡 Recomendações:</h3>
        <ul className="list-disc list-inside text-sm text-gray-700">
          {resumo.recomendacoes.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

---

## 4. API Integration

### 4.1 API Route: `/api/buscar` (POST)

```typescript
// frontend/app/api/buscar/route.ts

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const response = await fetch('http://localhost:8000/api/buscar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    return NextResponse.json(
      { error: 'Backend unavailable' },
      { status: 500 }
    );
  }
}
```

### 4.2 API Route: `/api/download` (GET)

```typescript
// frontend/app/api/download/route.ts

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const downloadId = searchParams.get('id');

  if (!downloadId) {
    return NextResponse.json({ error: 'Missing id' }, { status: 400 });
  }

  try {
    const response = await fetch(
      `http://localhost:8000/api/download?id=${downloadId}`
    );

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const buffer = await response.arrayBuffer();

    return new NextResponse(buffer, {
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': `attachment; filename="licitacoes-${downloadId}.xlsx"`
      }
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Download failed' },
      { status: 500 }
    );
  }
}
```

---

## 5. State Management

### 5.1 Component-Level State (React Hooks)

```typescript
// No Redux or Context API used (keep simple for POC)
// All state co-located in page.tsx

const [ufs, setUfs] = useState<Set<string>>(new Set());
const [dateRange, setDateRange] = useState({ ... });
const [results, setResults] = useState<Licitacao[]>([]);
const [summary, setSummary] = useState<ResumoLicitacoes | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

### 5.2 Download Cache Strategy

**Current:** Implicit via API backend (10min TTL)
**Future:** React SWR or TanStack Query for client-side caching

---

## 6. Styling & Design System

### 6.1 Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        // BidIQ color palette
        'bidiq-green': '#2E7D32',  // Primary (from AIOS standard)
        'bidiq-blue': '#1976D2',   // Secondary
      }
    }
  }
};
```

### 6.2 Global Styles

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-bidiq-green text-white rounded hover:bg-green-700 transition-colors;
  }

  .btn-secondary {
    @apply px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors;
  }
}
```

### 6.3 Design Principles

- **Minimalist:** Focus on functionality over decoration
- **Data-driven:** Tables > visualizations (better for procurement data)
- **Accessible:** WCAG 2.1 AA compliance
- **Responsive:** Mobile-first approach
- **Performance:** No heavy libraries (Tailwind only)

---

## 7. Type Safety (TypeScript)

### 7.1 API Types

```typescript
// types/api.ts

export interface BuscaRequest {
  ufs: string[];
  data_inicio: string;  // YYYY-MM-DD
  data_fim: string;     // YYYY-MM-DD
  valor_minimo?: number;
  valor_maximo?: number;
}

export interface Licitacao {
  codigo: string;
  objeto: string;
  orgao: string;
  uf: string;
  municipio: string;
  valor: number;
  status: string;
  link: string;
}

export interface ResumoLicitacoes {
  resumo_executivo: string;
  total_oportunidades: number;
  valor_total: number;
  destaques: string[];
  recomendacoes: string[];
}

export interface BuscaResponse {
  id: string;
  total: int;
  resultados: Licitacao[];
  resumo: ResumoLicitacoes | null;
  gerado_em: string;
}
```

### 7.2 No `any` Types Policy

- ✅ Strict TypeScript enabled
- ✅ All function parameters typed
- ✅ All return types explicit
- ✅ No implicit `any`

---

## 8. Testing Strategy

### 8.1 Test Coverage Requirements

| Layer | Threshold | Status |
|-------|-----------|--------|
| Components | 60%+ | ⚠️ Not implemented (Issue #21) |
| Hooks | 60%+ | ⚠️ Not implemented |
| Pages | 60%+ | ⚠️ Not implemented |
| Integration | 40%+ | ⚠️ Not implemented |

### 8.2 Test Examples (To Be Implemented)

```typescript
// __tests__/components/UFSelector.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UFSelector } from '@/components/UFSelector';

describe('UFSelector', () => {
  it('renders all 27 states', () => {
    const mockOnChange = jest.fn();
    render(<UFSelector ufs={new Set()} onChange={mockOnChange} />);
    expect(screen.getAllByRole('button')).toHaveLength(27);
  });

  it('toggles UF on click', () => {
    const mockOnChange = jest.fn();
    render(<UFSelector ufs={new Set()} onChange={mockOnChange} />);

    const spButton = screen.getByText('SP');
    fireEvent.click(spButton);

    expect(mockOnChange).toHaveBeenCalledWith(new Set(['SP']));
  });

  it('highlights selected UFs', () => {
    const mockOnChange = jest.fn();
    const selected = new Set(['SP']);
    render(<UFSelector ufs={selected} onChange={mockOnChange} />);

    const spButton = screen.getByText('SP');
    expect(spButton).toHaveClass('bg-green-600');
  });
});
```

---

## 9. Performance Targets

### 9.1 Core Web Vitals

| Metric | Target | Status |
|--------|--------|--------|
| First Contentful Paint (FCP) | <1.5s | ⚠️ TBD |
| Largest Contentful Paint (LCP) | <2.5s | ⚠️ TBD |
| Cumulative Layout Shift (CLS) | <0.1 | ⚠️ TBD |
| First Input Delay (FID) | <100ms | ⚠️ TBD |

### 9.2 Bundle Size

| Chunk | Target | Status |
|-------|--------|--------|
| Main | <100KB | ⚠️ TBD |
| Tailwind CSS | <50KB | ✅ Likely (PurgeCSS active) |
| Total Initial | <200KB gzipped | ⚠️ TBD |

### 9.3 Optimization Strategies

- ✅ Code splitting (Next.js automatic)
- ✅ Image optimization (next/image)
- ✅ Lazy loading (React.lazy for components)
- ✅ CSS purging (Tailwind production mode)
- ⚠️ Font optimization (TBD)
- ⚠️ Prefetching (TBD)

---

## 10. UX/UI Debt & Gaps

### Current Gaps (POC)

#### CRITICAL
1. **Frontend Structure Missing**
   - Issue #21: Create Next.js app structure
   - Status: Not started
   - Impact: Cannot develop/test UI
   - Effort: 4-6 hours

2. **Components Not Implemented**
   - Missing: UFSelector, DateRangePicker, ResultsTable, SummaryCard
   - Status: Designed but not coded
   - Impact: No UI
   - Effort: 8-10 hours

3. **API Routes Missing**
   - Missing: /api/buscar, /api/download route handlers
   - Status: Not started
   - Impact: Cannot communicate with backend
   - Effort: 2-3 hours

#### HIGH

4. **Error Handling UI**
   - Missing: Error boundaries, error messages, retry buttons
   - Status: Not designed
   - Impact: Poor user experience on errors
   - Effort: 3-4 hours

5. **Loading States**
   - Missing: Skeleton loaders, progress indicators
   - Status: Not implemented
   - Impact: Unclear to users what's happening
   - Effort: 2-3 hours

6. **Form Validation**
   - Missing: Client-side validation feedback
   - Status: Not implemented
   - Impact: Users can submit invalid dates
   - Effort: 2-3 hours

7. **Mobile Responsiveness**
   - Missing: Mobile testing, responsive refinements
   - Status: Tailwind responsive classes planned but untested
   - Impact: Poor mobile experience
   - Effort: 4-5 hours

8. **Accessibility**
   - Missing: ARIA labels, keyboard navigation, screen reader testing
   - Status: Basic HTML semantics only
   - Impact: Not WCAG compliant
   - Effort: 4-5 hours

#### MEDIUM

9. **Help/Documentation UI**
   - Missing: Tooltips, help text, inline documentation
   - Status: Not implemented
   - Impact: Users unclear on how to use
   - Effort: 2-3 hours

10. **Download Management**
    - Missing: Download history, multiple simultaneous downloads
    - Status: Single download supported
    - Impact: Users can't track multiple searches
    - Effort: 4-5 hours (future)

11. **Advanced Filters**
    - Missing: Value range slider, keyword search, status filters
    - Status: Only UF and date range available
    - Impact: Limited filtering capability
    - Effort: 6-8 hours (future)

12. **Pagination/Virtualization**
    - Missing: Handling large result sets (100+ results)
    - Status: All results rendered at once
    - Impact: Performance degradation with many results
    - Effort: 4-6 hours (future)

---

## 11. Frontend Security Considerations

### 11.1 Input Validation

- ✅ Date validation (HTML5 date input)
- ⚠️ Missing: Client-side validation feedback
- ✅ UF validation (predefined list)
- ✅ No user-generated content displayed without sanitization

### 11.2 API Security

- ⚠️ No authentication (public API - acceptable for POC)
- ⚠️ CORS not configured (must fix for production)
- ✅ HTTPS required (production deployment)
- ⚠️ Missing: Rate limiting on frontend (backend handles)

### 11.3 Data Protection

- ✅ PNCP data is public (no privacy concerns)
- ✅ No sensitive user data stored
- ⚠️ Download cache TTL (10min should be fine)

---

## 12. Browser Support

### Minimum Requirements

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

**Note:** ES2020+ features used (requires transpilation via Next.js)

---

## 13. Accessibility Audit

### WCAG 2.1 AA Compliance Checklist

- [ ] Color contrast ≥4.5:1 for text
- [ ] Keyboard navigation fully functional
- [ ] ARIA labels on form inputs
- [ ] Alt text on images
- [ ] Focus indicators visible
- [ ] Semantic HTML (headings, lists, etc.)
- [ ] Page language declared
- [ ] Screen reader tested

**Status:** ⚠️ Not audited (Issue needed for a11y review)

---

## 14. Monitoring & Analytics (Future)

### Metrics to Track

- Page load time (CLS, FCP, LCP)
- Search frequency by UF
- Average results per search
- Excel download rate
- Error rates by endpoint
- User session duration

### Tools (Future)

- Google Analytics 4
- Sentry for error tracking
- Web Vitals Core measurement

---

## 15. UX/UI Debt Priority Matrix

| Item | Effort | Impact | Priority |
|------|--------|--------|----------|
| Frontend structure (Issue #21) | 4-6h | CRITICAL | 1 |
| Components implementation | 8-10h | CRITICAL | 2 |
| API routes | 2-3h | CRITICAL | 3 |
| Error handling UI | 3-4h | HIGH | 4 |
| Loading states | 2-3h | HIGH | 5 |
| Form validation | 2-3h | HIGH | 6 |
| Mobile responsiveness | 4-5h | HIGH | 7 |
| Accessibility | 4-5h | HIGH | 8 |

**Total MVP Effort:** ~30-40 hours

---

## 16. Frontend Architecture Strengths

✅ **Type-Safe**
- TypeScript strict mode
- No `any` types
- Interfaces for all API contracts

✅ **Minimal Dependencies**
- Tailwind only for styling
- No heavy UI libraries
- React hooks for state (no Redux)

✅ **Performance-Conscious**
- Code splitting automatic (Next.js)
- CSS purging (Tailwind)
- No render-blocking CSS

✅ **SEO-Friendly**
- Next.js server-side rendering capable
- Semantic HTML
- Meta tags configurable

---

## 17. Frontend Architecture Weaknesses

⚠️ **Incomplete Implementation**
- No components built yet
- No API routes implemented
- No tests written
- No error boundaries

⚠️ **Limited State Management**
- No global state (future: Context API or Zustand)
- No caching strategy (future: SWR or React Query)
- No persistence layer

⚠️ **Missing Error Handling**
- No error boundaries
- No retry logic UI
- No offline support

⚠️ **Accessibility Gaps**
- Not WCAG audited
- Missing ARIA labels
- Keyboard navigation untested

---

## 18. Roadmap: Frontend Development

### Phase 1: MVP (Weeks 1-2)
- [ ] Issue #21: Create Next.js app structure
- [ ] Build all core components
- [ ] Implement API routes (/api/buscar, /api/download)
- [ ] Basic error handling
- [ ] Mobile responsive layout
- **Result:** Functional SPA

### Phase 2: Polish (Week 3)
- [ ] Comprehensive error UI
- [ ] Loading states + skeletons
- [ ] Form validation feedback
- [ ] Help text + tooltips
- [ ] Issue #27: Write component tests
- **Result:** Production-ready UI

### Phase 3: Enhancement (Post-MVP)
- [ ] Advanced filters (value range, keywords)
- [ ] Pagination/virtualization for large result sets
- [ ] Download history
- [ ] User accounts + saved searches
- [ ] WCAG 2.1 AA compliance
- **Result:** Enterprise-grade frontend

---

## 19. Component Checklist

### Core Components (Must Have)

- [ ] UFSelector
- [ ] DateRangePicker
- [ ] ResultsTable
- [ ] SummaryCard
- [ ] LoadingSkeletons
- [ ] ErrorBoundary
- [ ] ErrorAlert
- [ ] Main page.tsx

### Future Components

- [ ] AdvancedFilters
- [ ] DownloadHistory
- [ ] Pagination
- [ ] UserProfile
- [ ] SavedSearches
- [ ] Analytics Dashboard

---

## 20. Frontend QA Checklist

### Functional Testing

- [ ] UF selection works
- [ ] Date picker validation
- [ ] Search submission
- [ ] Results display
- [ ] Excel download
- [ ] Error handling

### Non-Functional

- [ ] Responsive on mobile (320px, 768px, 1024px)
- [ ] Core Web Vitals: FCP <1.5s, LCP <2.5s
- [ ] Bundle size <200KB gzipped
- [ ] WCAG 2.1 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader compatible

---

## Document Information

**Created:** January 26, 2026
**Last Updated:** January 26, 2026
**Status:** APPROVED FOR TECHNICAL DEBT REVIEW
**Related Issue:** #21 (Frontend Setup)

---

**Next Step:** Implement Issue #21 - Create Next.js app structure and begin component development.
