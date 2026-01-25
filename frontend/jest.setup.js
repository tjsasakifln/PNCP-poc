/**
 * Jest setup file - runs after Jest is initialized
 *
 * This file imports custom matchers and configurations needed for testing.
 */

// Polyfill for Next.js 14+ compatibility
import { TextEncoder, TextDecoder } from 'util'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Import jest-dom matchers (when @testing-library/jest-dom is installed)
// These provide custom matchers like .toBeInTheDocument(), .toHaveClass(), etc.
try {
  require('@testing-library/jest-dom')
} catch (error) {
  console.warn('⚠️  @testing-library/jest-dom not installed yet.')
  console.warn('   Install with: npm install --save-dev @testing-library/jest-dom')
}

// Mock Next.js router (when Next.js is installed)
try {
  const { useRouter } = require('next/router')
  jest.mock('next/router', () => ({
    useRouter: jest.fn(),
  }))
} catch (error) {
  // Next.js not installed yet (Issue #21)
}

// Mock Next.js navigation (App Router - Next.js 14+)
try {
  jest.mock('next/navigation', () => ({
    useRouter: jest.fn(() => ({
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
    })),
    usePathname: jest.fn(() => '/'),
    useSearchParams: jest.fn(() => new URLSearchParams()),
  }))
} catch (error) {
  // Next.js not installed yet (Issue #21)
}

// Global test timeout (default: 5000ms)
jest.setTimeout(10000)

// Suppress console warnings/errors in tests (optional)
// Uncomment if you want cleaner test output
// const originalError = console.error
// beforeAll(() => {
//   console.error = (...args) => {
//     if (
//       typeof args[0] === 'string' &&
//       args[0].includes('Warning: ReactDOM.render')
//     ) {
//       return
//     }
//     originalError.call(console, ...args)
//   }
// })
//
// afterAll(() => {
//   console.error = originalError
// })
