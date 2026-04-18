/**
 * Jest configuration for SmartLic Frontend
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
    '^@/(.*)$': '<rootDir>/$1',
    '\\.css$': '<rootDir>/__mocks__/styleMock.js',
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

  // Coverage thresholds — recalibrado para baseline medido (CI run 24593094865)
  // EPIC-CI-GREEN-MAIN-2026Q2: fn=52.05%, stmt=54.97% medidos; headroom ~1% abaixo do real
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 51,
      lines: 55,
      statements: 54,
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
    '/__tests__/utils/',      // Shared test utilities (not test files) — STORY-368
    '/tests/chromatic/', // Playwright spec — roda via chromatic.yml, não Jest (CIG-FE-10)
  ],

  // Transform node_modules that use ES modules (uuid, etc.)
  transformIgnorePatterns: [
    'node_modules/(?!(uuid|shepherd\\.js)/)',
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
