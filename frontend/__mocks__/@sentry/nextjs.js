// Jest manual mock for @sentry/nextjs (STORY-211)
// Prevents Sentry SDK initialization in test environment
module.exports = {
  init: jest.fn(),
  captureException: jest.fn(),
  captureMessage: jest.fn(),
  captureRequestError: jest.fn(),
  setUser: jest.fn(),
  setContext: jest.fn(),
  setTag: jest.fn(),
  addBreadcrumb: jest.fn(),
  withScope: jest.fn((cb) => cb({ setTag: jest.fn(), setExtra: jest.fn() })),
  startSpan: jest.fn(),
  Scope: jest.fn(),
};
