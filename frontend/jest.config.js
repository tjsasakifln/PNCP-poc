/**
 * Jest configuration for BidIQ Uniformes Frontend
 *
 * This configuration is ready for Next.js 14+ with TypeScript.
 * Install required dependencies:
 *   npm install --save-dev jest @testing-library/react @testing-library/jest-dom
 *   npm install --save-dev @testing-library/user-event jest-environment-jsdom
 */

const nextJest = require('next/jest')

// Provide the path to your Next.js app to load next.config.js and .env files in your test environment
const createJestConfig = nextJest({
  // Path to Next.js app to load next.config.js and .env files
  dir: './',
})

/** @type {import('jest').Config} */
const customJestConfig = {
  // Test environment
  testEnvironment: 'jest-environment-jsdom',

  // Setup files to run after Jest is initialized
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Module paths
  moduleDirectories: ['node_modules', '<rootDir>/'],

  // Path aliases (sync with tsconfig.json paths)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/app/$1',
    '^@/components/(.*)$': '<rootDir>/app/components/$1',
    '^@/lib/(.*)$': '<rootDir>/lib/$1',
    // Fix relative imports from hooks/ to lib/
    '^\\.\\./lib/(.*)$': '<rootDir>/lib/$1',
  },

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/coverage/**',
    '!**/jest.config.js',
  ],

  // Coverage thresholds (target: 60% per CLAUDE.md, current: 49.45%)
  // Progress: 31% → 49.45% (+18.45% from test additions)
  // Next steps to reach 60%:
  //   - Add LoadingProgress component tests (0% → 70%+)
  //   - Add RegionSelector component tests (0% → 80%+)
  //   - Add SavedSearchesDropdown tests (22% → 70%+)
  //   - Add AnalyticsProvider tests (0% → 60%+)
  //   - Fix remaining ThemeToggle async tests (3 failing)
  //   - Add hooks/useAnalytics tests (currently not in coverage report)
  coverageThreshold: {
    global: {
      branches: 39,   // Current: 39.56%
      functions: 41,  // Current: 41.98%
      lines: 50,      // Current: 51.01%
      statements: 49, // Current: 49.45%
    },
  },

  // Coverage reporters
  coverageReporters: ['text', 'html', 'lcov'],

  // Test reporters (for CI/CD)
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: '.',
      outputName: 'junit.xml',
      ancestorSeparator: ' › ',
      uniqueOutputName: 'false',
      suiteNameTemplate: '{filepath}',
      classNameTemplate: '{classname}',
      titleTemplate: '{title}',
    }]
  ],

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/__tests__/e2e/', // E2E tests run via Playwright, not Jest
    '/e2e-tests/', // Playwright E2E tests directory
  ],

  // Transform node_modules that use ES modules (uuid, etc.)
  transformIgnorePatterns: [
    'node_modules/(?!(uuid)/)',
  ],

  // Transform files
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['@swc/jest', {
      jsc: {
        parser: {
          syntax: 'typescript',
          tsx: true,
        },
        transform: {
          react: {
            runtime: 'automatic',
          },
        },
      },
    }],
  },

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Reset mocks between tests
  resetMocks: true,

  // Restore mocks between tests
  restoreMocks: true,
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config
// which is async. If Next.js is not yet installed, this will gracefully fallback.
try {
  module.exports = createJestConfig(customJestConfig)
} catch (error) {
  // Fallback for when Next.js is not installed yet (Issue #21 not completed)
  console.warn('⚠️  Next.js not found. Using fallback Jest config.')
  console.warn('   Run `npm install next react react-dom` when setting up Next.js.')
  module.exports = customJestConfig
}
