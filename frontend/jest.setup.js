/**
 * Jest setup file - runs after Jest is initialized
 *
 * This file imports custom matchers and configurations needed for testing.
 */

// Mock uuid module FIRST (before any imports)
// This must be at the top level for Jest hoisting to work properly
jest.mock('uuid', () => ({
  v4: () => 'test-uuid-12345',
}));

// Polyfill for Next.js 14+ compatibility
import { TextEncoder, TextDecoder } from 'util'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Polyfill crypto.randomUUID for jsdom (used by SSE search progress)
if (typeof globalThis.crypto === 'undefined') {
  globalThis.crypto = {};
}
if (!globalThis.crypto.randomUUID) {
  globalThis.crypto.randomUUID = () => 'test-uuid-0000-0000-0000-000000000000';
}

// Mock EventSource for jsdom (used by SSE progress tracking)
if (typeof globalThis.EventSource === 'undefined') {
  globalThis.EventSource = class MockEventSource {
    constructor(url) {
      this.url = url;
      this.readyState = 0;
      this.onopen = null;
      this.onmessage = null;
      this.onerror = null;
      // Simulate connection error after a tick (triggers fallback to simulated progress)
      setTimeout(() => {
        if (this.onerror) this.onerror(new Event('error'));
      }, 0);
    }
    close() { this.readyState = 2; }
    addEventListener() {}
    removeEventListener() {}
  };
}

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

// Mock window.matchMedia (not available in jsdom)
// Uses beforeAll + beforeEach to survive jest.clearAllMocks()
if (typeof window !== 'undefined') {
  const matchMediaMock = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  });
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: jest.fn().mockImplementation(matchMediaMock),
  });
  beforeEach(() => {
    window.matchMedia = jest.fn().mockImplementation(matchMediaMock);
  });
}

// Mock IntersectionObserver (not available in jsdom)
// Required for useInView hook and landing page animations
class MockIntersectionObserver {
  constructor(callback) {
    this.callback = callback;
  }
  observe(element) {
    // Trigger immediately as if element is in view
    this.callback([{ isIntersecting: true, target: element }]);
  }
  unobserve() {}
  disconnect() {}
}

if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'IntersectionObserver', {
    writable: true,
    configurable: true,
    value: MockIntersectionObserver,
  });
  Object.defineProperty(global, 'IntersectionObserver', {
    writable: true,
    configurable: true,
    value: MockIntersectionObserver,
  });
}

// Mock Element.prototype.scrollIntoView (not available in jsdom)
// Required for components that scroll elements into view (MunicipioFilter, OrgaoFilter, etc.)
if (typeof window !== 'undefined' && typeof Element.prototype.scrollIntoView === 'undefined') {
  Element.prototype.scrollIntoView = jest.fn();
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
