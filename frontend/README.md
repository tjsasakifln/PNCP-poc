# BidIQ Uniformes - Frontend

Frontend application for BidIQ Uniformes POC.

## Status

⚠️ **Next.js Setup Pending** - Issue #21

The frontend structure and test configuration are ready, but Next.js has not been installed yet.

## Test Configuration

Jest is configured and ready for use when Next.js is installed.

### Running Tests

```bash
# Install dependencies first (when Next.js is set up)
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# CI mode (for GitHub Actions)
npm run test:ci
```

### Coverage Requirements

- **Minimum Coverage:** 60% (branches, functions, lines, statements)
- **Reports:** HTML report generated in `coverage/` directory
- **Threshold Enforcement:** Tests fail if coverage < 60%

### Configuration Files

- `jest.config.js` - Jest configuration with Next.js support
- `jest.setup.js` - Test environment setup (mocks, global config)
- `__tests__/` - Test files location

### Test File Patterns

Jest will discover test files matching:
- `**/__tests__/**/*.[jt]s?(x)`
- `**/?(*.)+(spec|test).[jt]s?(x)`

### Examples

```typescript
// Component test example (when Next.js is installed)
import { render, screen } from '@testing-library/react'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

## Next Steps

1. **Issue #21:** Set up Next.js 14 with App Router
2. **Issue #22:** Implement UF selection interface
3. **Issue #23:** Implement results display
4. **Issue #24:** Create API routes

## Development

Once Next.js is installed (Issue #21):

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint
```

## Dependencies

Will be installed in Issue #21:
- Next.js 14+
- React 18+
- TypeScript 5.3+
- Tailwind CSS 3.4+

Test dependencies are already configured in `package.json`:
- Jest 29+
- @testing-library/react 14+
- @testing-library/jest-dom 6+
- @swc/jest (for fast TypeScript transpilation)
