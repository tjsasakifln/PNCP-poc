/**
 * E2E Test: Saved Searches
 *
 * Critical User Flow #3: Search persistence and reload
 *
 * Steps:
 * 1. Execute search
 * 2. Verify auto-save to localStorage
 * 3. Reload page
 * 4. Load saved search
 * 5. Verify form populated
 *
 * Reference: docs/reviews/qa-testing-analysis.md (lines 413-414)
 */

import { test, expect } from '@playwright/test';
import { SearchPage, SavedSearchesDropdown } from './helpers/page-objects';
import {
  mockSearchAPI,
  mockSetoresAPI,
  clearTestData,
  getLocalStorageItem,
  setLocalStorageItem,
  generateMockSavedSearches,
} from './helpers/test-utils';

test.describe('Saved Searches E2E', () => {
  let searchPage: SearchPage;
  let savedSearches: SavedSearchesDropdown;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    savedSearches = new SavedSearchesDropdown(page);

    // Setup API mocks first (before navigation)
    await mockSetoresAPI(page);
    await mockSearchAPI(page, 'success');

    // Navigate to home
    await searchPage.goto();

    // Clear test data after navigation
    await clearTestData(page);
  });

  test('AC1: should save search after execution', async ({ page }) => {
    // Clear selections and select UFs
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');
    await searchPage.selectUF('PR');

    // Execute search
    await searchPage.executeSearch();

    // Verify results displayed
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Click save search button
    await expect(searchPage.saveSearchButton).toBeVisible();
    await searchPage.saveSearchButton.click();

    // Fill in search name in dialog
    const nameInput = page.locator('input#save-search-name');
    await expect(nameInput).toBeVisible();
    await nameInput.fill('Teste Sul do Brasil');

    // Confirm save
    const confirmButton = page.getByRole('button', { name: /^Salvar$/i });
    await confirmButton.click();

    // Wait for dialog to close
    await expect(nameInput).not.toBeVisible();

    // Verify saved to localStorage
    const stored = await getLocalStorageItem(page, 'saved-searches');
    expect(stored).toBeTruthy();

    const searches = JSON.parse(stored!);
    expect(searches.searches).toHaveLength(1);
    expect(searches.searches[0].name).toBe('Teste Sul do Brasil');
    expect(searches.searches[0].searchParams.ufs).toEqual(['SC', 'PR']);
  });

  test('AC2: should display saved searches in dropdown', async ({ page }) => {
    // Pre-populate localStorage with saved searches
    const mockSearches = generateMockSavedSearches(3);
    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches: mockSearches, version: 1 })
    );

    // Reload to pick up localStorage
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Open saved searches dropdown
    await savedSearches.open();

    // Verify searches are displayed
    await expect(savedSearches.dropdown).toContainText('Busca Teste 1');
    await expect(savedSearches.dropdown).toContainText('Busca Teste 2');
    await expect(savedSearches.dropdown).toContainText('Busca Teste 3');

    // Verify count badge
    const count = await savedSearches.getSearchCount();
    expect(count).toBe(3);
  });

  test('AC3: should load saved search and populate form', async ({ page }) => {
    // Pre-populate localStorage
    const mockSearches = generateMockSavedSearches(1);
    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches: mockSearches, version: 1 })
    );

    // Reload
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Clear current selections
    await searchPage.clearUFSelection();

    // Load saved search
    await savedSearches.loadSearch('Busca Teste 1');

    // Verify form populated with saved parameters
    const scButton = page.getByRole('button', { name: 'SC', exact: true });
    const prButton = page.getByRole('button', { name: 'PR', exact: true });

    await expect(scButton).toHaveClass(/bg-brand-navy/);
    await expect(prButton).toHaveClass(/bg-brand-navy/);

    // Verify date range
    const dataInicial = await searchPage.dataInicial.inputValue();
    const dataFinal = await searchPage.dataFinal.inputValue();

    expect(dataInicial).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(dataFinal).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  test('AC4: should persist saved searches after reload', async ({ page }) => {
    // Save a search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SP');
    await searchPage.executeSearch();
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    await searchPage.saveSearchButton.click();
    const nameInput = page.locator('input#save-search-name');
    await nameInput.fill('São Paulo');
    await page.getByRole('button', { name: /^Salvar$/i }).click();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify search persisted
    await savedSearches.open();
    await expect(savedSearches.dropdown).toContainText('São Paulo');
  });

  test('AC5: should delete saved search', async ({ page }) => {
    // Pre-populate with 2 searches
    const mockSearches = generateMockSavedSearches(2);
    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches: mockSearches, version: 1 })
    );

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Open dropdown
    await savedSearches.open();

    // Delete first search (requires 2 clicks for confirmation)
    await savedSearches.deleteSearch('Busca Teste 1');

    // Verify search removed
    await expect(savedSearches.dropdown).not.toContainText('Busca Teste 1');

    // Verify count updated
    const count = await savedSearches.getSearchCount();
    expect(count).toBe(1);
  });

  test('AC6: should clear all saved searches', async ({ page }) => {
    // Pre-populate with multiple searches
    const mockSearches = generateMockSavedSearches(5);
    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches: mockSearches, version: 1 })
    );

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Open dropdown
    await savedSearches.open();

    // Click clear all
    page.on('dialog', (dialog) => dialog.accept()); // Accept confirmation
    await savedSearches.clearAllButton.click();

    // Wait for dropdown to close
    await page.waitForTimeout(300);

    // Verify all cleared
    const count = await savedSearches.getSearchCount();
    expect(count).toBe(0);

    // Verify localStorage cleared
    const stored = await getLocalStorageItem(page, 'saved-searches');
    const searches = JSON.parse(stored!);
    expect(searches.searches).toHaveLength(0);
  });

  test('AC7: should show empty state when no searches', async ({ page }) => {
    // Open dropdown with no saved searches
    await savedSearches.open();

    // Verify empty state
    await expect(savedSearches.emptyState).toBeVisible();
    await expect(savedSearches.dropdown).toContainText(/Nenhuma busca salva/i);
  });

  test('AC8: should enforce 10 search limit', async ({ page }) => {
    // Pre-populate with 10 searches (max capacity)
    const mockSearches = generateMockSavedSearches(10);
    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches: mockSearches, version: 1 })
    );

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Execute a new search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RJ');
    await searchPage.executeSearch();
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Verify save button is disabled
    await expect(searchPage.saveSearchButton).toBeDisabled();
    await expect(searchPage.saveSearchButton).toContainText(/Limite de buscas atingido/i);
  });

  test('AC9: should update lastUsedAt when loading search', async ({ page }) => {
    // Pre-populate with a search
    const mockSearches = generateMockSavedSearches(1);
    const originalTimestamp = mockSearches[0].lastUsedAt;

    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches: mockSearches, version: 1 })
    );

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Wait a bit to ensure timestamp difference
    await page.waitForTimeout(1000);

    // Load the search
    await savedSearches.loadSearch('Busca Teste 1');

    // Verify lastUsedAt updated in localStorage
    const stored = await getLocalStorageItem(page, 'saved-searches');
    const searches = JSON.parse(stored!);
    const updatedTimestamp = searches.searches[0].lastUsedAt;

    expect(new Date(updatedTimestamp).getTime()).toBeGreaterThan(
      new Date(originalTimestamp).getTime()
    );
  });

  test('AC10: should display relative timestamps', async ({ page }) => {
    // Pre-populate with searches at different times
    const now = Date.now();
    const searches = [
      {
        id: 'recent',
        name: 'Busca Recente',
        createdAt: new Date(now - 5 * 60 * 1000).toISOString(), // 5 minutes ago
        lastUsedAt: new Date(now - 5 * 60 * 1000).toISOString(),
        searchParams: {
          ufs: ['SC'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'setor' as const,
          setorId: 'vestuario',
        },
      },
      {
        id: 'old',
        name: 'Busca Antiga',
        createdAt: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
        lastUsedAt: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(),
        searchParams: {
          ufs: ['SP'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'setor' as const,
          setorId: 'alimentos',
        },
      },
    ];

    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches, version: 1 })
    );

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Open dropdown
    await savedSearches.open();

    // Verify relative timestamps
    await expect(savedSearches.dropdown).toContainText(/há \d+ min/i);
    await expect(savedSearches.dropdown).toContainText(/há \d+ dias/i);
  });

  test('AC11: should handle search mode in saved searches', async ({ page }) => {
    // Save search with custom terms mode
    await searchPage.searchModeTermos.click();

    // Add custom terms
    await searchPage.termosInput.fill('uniforme escolar ');
    await page.waitForTimeout(200);

    // Select UFs
    await searchPage.clearUFSelection();
    await searchPage.selectUF('MG');

    // Execute search
    await searchPage.executeSearch();
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Save search
    await searchPage.saveSearchButton.click();
    const nameInput = page.locator('input#save-search-name');
    await nameInput.fill('Uniformes Personalizados');
    await page.getByRole('button', { name: /^Salvar$/i }).click();

    // Reload and load search
    await page.reload();
    await page.waitForLoadState('networkidle');

    await savedSearches.loadSearch('Uniformes Personalizados');

    // Verify search mode is "termos"
    await expect(searchPage.searchModeTermos).toHaveClass(/bg-brand-navy/);
    await expect(searchPage.searchModeSetor).not.toHaveClass(/bg-brand-navy/);
  });

  test('AC12: should sort searches by most recently used', async ({ page }) => {
    // Create searches with different timestamps
    const searches = [
      {
        id: '1',
        name: 'Antiga',
        createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        lastUsedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        searchParams: {
          ufs: ['SC'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'setor' as const,
          setorId: 'vestuario',
        },
      },
      {
        id: '2',
        name: 'Recente',
        createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        lastUsedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        searchParams: {
          ufs: ['PR'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'setor' as const,
          setorId: 'alimentos',
        },
      },
    ];

    await setLocalStorageItem(
      page,
      'saved-searches',
      JSON.stringify({ searches, version: 1 })
    );

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Open dropdown
    await savedSearches.open();

    // Get all search items
    const searchItems = savedSearches.dropdown.locator('button').filter({ hasText: /Antiga|Recente/i });

    // Verify "Recente" appears before "Antiga"
    const firstSearch = searchItems.first();
    await expect(firstSearch).toContainText('Recente');
  });
});
