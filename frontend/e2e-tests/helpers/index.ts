/**
 * E2E Test Helpers - Central Export
 *
 * Exports all page objects and test utilities for easy importing
 */

// Page Objects
export { SearchPage, ThemeSelector, SavedSearchesDropdown } from './page-objects';

// Test Utilities
export {
  mockSuccessfulSearch,
  mockEmptySearch,
  mockAPIError,
  mockSearchAPI,
  mockDownloadAPI,
  mockSetoresAPI,
  getDateString,
  waitForNetworkIdle,
  clearTestData,
  takeTimestampedScreenshot,
  simulateNetworkFailure,
  simulateSlowNetwork,
  getCSSVariable,
  getLocalStorageItem,
  setLocalStorageItem,
  generateMockSavedSearches,
  mockAuthAPI,
  mockMeAPI,
  mockAdminUsersAPI,
} from './test-utils';
