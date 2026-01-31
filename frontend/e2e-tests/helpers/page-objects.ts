/**
 * Page Object Model (POM) for BidIQ Uniformes E2E Tests
 *
 * Provides reusable selectors and actions for common UI interactions
 * following the Page Object pattern for better maintainability.
 */

import { Page, Locator, expect } from '@playwright/test';

/**
 * Main Page Object for the home/search page
 */
export class SearchPage {
  readonly page: Page;

  // Header elements
  readonly logo: Locator;
  readonly themeToggle: Locator;
  readonly savedSearchesButton: Locator;
  readonly onboardingButton: Locator;

  // Search mode
  readonly searchModeSetor: Locator;
  readonly searchModeTermos: Locator;
  readonly setorSelector: Locator;
  readonly termosInput: Locator;

  // UF selection
  readonly ufGrid: Locator;
  readonly selectAllButton: Locator;
  readonly clearButton: Locator;
  readonly ufCounter: Locator;

  // Date inputs
  readonly dataInicial: Locator;
  readonly dataFinal: Locator;

  // Search button
  readonly searchButton: Locator;
  readonly saveSearchButton: Locator;

  // Results
  readonly resultsSection: Locator;
  readonly executiveSummary: Locator;
  readonly downloadButton: Locator;
  readonly emptyState: Locator;
  readonly errorMessage: Locator;

  // Loading state
  readonly loadingProgress: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.logo = page.locator('img[alt="DescompLicita"]');
    this.themeToggle = page.getByRole('button', { name: /Alternar tema/i });
    this.savedSearchesButton = page.getByRole('button', { name: /Buscas salvas/i });
    this.onboardingButton = page.locator('button[title="Ver tutorial novamente"]');

    // Search mode
    this.searchModeSetor = page.getByRole('button', { name: 'Setor', exact: true });
    this.searchModeTermos = page.getByRole('button', { name: 'Termos Específicos', exact: true });
    this.setorSelector = page.locator('select#setor');
    this.termosInput = page.locator('input#termos-busca');

    // UF selection
    this.ufGrid = page.locator('.grid').filter({ hasText: /^[A-Z]{2}$/ });
    this.selectAllButton = page.getByRole('button', { name: /Selecionar todos/i });
    this.clearButton = page.getByRole('button', { name: /Limpar/i });
    this.ufCounter = page.locator('text=/\\d+ estados? selecionados?/i');

    // Date inputs
    this.dataInicial = page.locator('input#data-inicial');
    this.dataFinal = page.locator('input#data-final');

    // Buttons
    this.searchButton = page.getByRole('button', { name: /Buscar/i });
    this.saveSearchButton = page.getByRole('button', { name: /Salvar Busca/i });

    // Results
    this.resultsSection = page.locator('text=/Resumo Executivo/i').locator('..');
    this.executiveSummary = page.locator('text=/Resumo Executivo:/i');
    this.downloadButton = page.getByRole('button', { name: /Baixar Excel/i });
    this.emptyState = page.locator('text=/Nenhuma licitação encontrada/i');
    this.errorMessage = page.locator('[role="alert"]').filter({ hasText: /Erro/i });

    // Loading
    this.loadingProgress = page.locator('text=/Buscando.../i').or(page.locator('[aria-busy="true"]'));
  }

  /**
   * Navigate to the home page
   */
  async goto() {
    await this.page.goto('/');
    await expect(this.page).toHaveTitle(/BidIQ|DescompLicita/i);
  }

  /**
   * Select a UF by clicking its button
   */
  async selectUF(uf: string) {
    const ufButton = this.page.getByRole('button', { name: uf, exact: true });
    await ufButton.click();
    await expect(ufButton).toHaveClass(/bg-brand-navy/);
  }

  /**
   * Select multiple UFs
   */
  async selectUFs(ufs: string[]) {
    for (const uf of ufs) {
      await this.selectUF(uf);
    }
  }

  /**
   * Clear all UF selections
   */
  async clearUFSelection() {
    // Only click if button is visible (may not be visible if already empty)
    if (await this.clearButton.isVisible()) {
      await this.clearButton.click();
      // Wait for selections to clear
      await this.page.waitForTimeout(300);
    }
  }

  /**
   * Set date range
   */
  async setDateRange(inicial: string, final: string) {
    await this.dataInicial.fill(inicial);
    await this.dataFinal.fill(final);
  }

  /**
   * Execute search and wait for results or error
   */
  async executeSearch() {
    await this.searchButton.click();

    // Wait for either results, empty state, or error
    await Promise.race([
      this.resultsSection.waitFor({ state: 'visible', timeout: 30000 }),
      this.emptyState.waitFor({ state: 'visible', timeout: 30000 }),
      this.errorMessage.waitFor({ state: 'visible', timeout: 30000 }),
    ]).catch(() => {
      // Timeout - check if still loading
    });
  }

  /**
   * Download Excel file
   */
  async downloadExcel() {
    const downloadPromise = this.page.waitForEvent('download', { timeout: 10000 });
    await this.downloadButton.click();
    return await downloadPromise;
  }

  /**
   * Get theme from localStorage
   */
  async getStoredTheme(): Promise<string | null> {
    return await this.page.evaluate(() => localStorage.getItem('theme'));
  }

  /**
   * Get saved searches from localStorage
   */
  async getSavedSearches(): Promise<any> {
    const stored = await this.page.evaluate(() => localStorage.getItem('saved-searches'));
    return stored ? JSON.parse(stored) : null;
  }

  /**
   * Clear localStorage
   */
  async clearLocalStorage() {
    await this.page.evaluate(() => localStorage.clear());
  }

  /**
   * Wait for loading to complete
   */
  async waitForSearchComplete() {
    // Wait for loading spinner to appear (if present)
    await this.loadingProgress.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});

    // Wait for loading to disappear
    await this.loadingProgress.waitFor({ state: 'hidden', timeout: 60000 });
  }
}

/**
 * Theme Selector Page Object
 */
export class ThemeSelector {
  readonly page: Page;
  readonly toggleButton: Locator;
  readonly dropdown: Locator;

  constructor(page: Page) {
    this.page = page;
    this.toggleButton = page.getByRole('button', { name: /Alternar tema/i });
    this.dropdown = page.locator('div[class*="absolute"]').filter({ hasText: /Azul Descomplicita|Oceano|Floresta/i });
  }

  /**
   * Open theme dropdown
   */
  async open() {
    await this.toggleButton.click();
    await expect(this.dropdown).toBeVisible();
  }

  /**
   * Select a theme by label
   */
  async selectTheme(themeLabel: string) {
    await this.open();
    const themeButton = this.page.getByRole('button', { name: themeLabel, exact: true });
    await themeButton.click();
    await expect(this.dropdown).not.toBeVisible();
  }

  /**
   * Get currently active theme label
   */
  async getActiveTheme(): Promise<string> {
    await this.open();
    const activeTheme = this.dropdown.locator('button').filter({ hasText: /✓|checkmark/i });
    const label = await activeTheme.textContent();
    // Close dropdown
    await this.toggleButton.click();
    return label?.trim() || '';
  }
}

/**
 * Saved Searches Dropdown Page Object
 */
export class SavedSearchesDropdown {
  readonly page: Page;
  readonly toggleButton: Locator;
  readonly dropdown: Locator;
  readonly emptyState: Locator;
  readonly clearAllButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.toggleButton = page.getByRole('button', { name: /Buscas salvas/i });
    this.dropdown = page.locator('div.absolute').filter({ hasText: /Buscas Recentes|Nenhuma busca salva/i });
    this.emptyState = page.locator('text=/Nenhuma busca salva/i');
    this.clearAllButton = page.getByRole('button', { name: /Limpar todas/i });
  }

  /**
   * Open dropdown
   */
  async open() {
    await this.toggleButton.click();
    await expect(this.dropdown).toBeVisible();
  }

  /**
   * Load a saved search by name
   */
  async loadSearch(searchName: string) {
    await this.open();
    const searchButton = this.dropdown.getByRole('button').filter({ hasText: searchName });
    await searchButton.click();
    await expect(this.dropdown).not.toBeVisible();
  }

  /**
   * Delete a saved search
   */
  async deleteSearch(searchName: string) {
    await this.open();
    const searchRow = this.dropdown.locator('div').filter({ hasText: searchName }).first();
    const deleteButton = searchRow.locator('button[aria-label*="Excluir"]');

    // First click - confirm
    await deleteButton.click();
    // Second click - execute
    await deleteButton.click();
  }

  /**
   * Get count of saved searches
   */
  async getSearchCount(): Promise<number> {
    const badge = this.toggleButton.locator('span.bg-brand-navy');
    if (await badge.isVisible()) {
      const text = await badge.textContent();
      return parseInt(text || '0', 10);
    }
    return 0;
  }
}
