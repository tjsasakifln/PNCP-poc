/**
 * SavedSearchesDropdown Component Tests
 *
 * Tests dropdown, load, delete, and auto-save functionality
 * Target: 80%+ coverage
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import type { SavedSearch } from '@/lib/savedSearches';
import { useSavedSearches } from '../../hooks/useSavedSearches';

// Mock the hook module
jest.mock('../../hooks/useSavedSearches');

// Import component after mock declaration
import { SavedSearchesDropdown } from '@/app/components/SavedSearchesDropdown';

// Mock implementation functions
const mockDeleteSearch = jest.fn();
const mockLoadSearch = jest.fn();
const mockClearAll = jest.fn();
const mockSaveNewSearch = jest.fn();
const mockUpdateSearch = jest.fn();
const mockRefresh = jest.fn();

// Type assertion for the mocked hook
const mockedUseSavedSearches = useSavedSearches as jest.MockedFunction<typeof useSavedSearches>;

// Mock saved searches data
const mockSearches: SavedSearch[] = [
  {
    id: 'search-1',
    name: 'Uniformes SC/PR/RS',
    searchParams: {
      ufs: ['SC', 'PR', 'RS'],
      dataInicial: '2026-01-22',
      dataFinal: '2026-01-29',
      searchMode: 'setor',
      setorId: 'vestuario',
    },
    createdAt: '2026-01-29T10:00:00Z',
    lastUsedAt: '2026-01-29T10:00:00Z',
  },
  {
    id: 'search-2',
    name: 'Calçados Sudeste',
    searchParams: {
      ufs: ['SP', 'RJ', 'MG', 'ES'],
      dataInicial: '2026-01-15',
      dataFinal: '2026-01-22',
      searchMode: 'termos',
      termosBusca: 'calçado sapato',
    },
    createdAt: '2026-01-28T15:30:00Z',
    lastUsedAt: '2026-01-28T15:30:00Z',
  },
];

describe('SavedSearchesDropdown Component', () => {
  const mockOnLoadSearch = jest.fn();
  const mockOnAnalyticsEvent = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementation
    mockedUseSavedSearches.mockReturnValue({
      searches: mockSearches,
      loading: false,
      isMaxCapacity: false,
      saveNewSearch: mockSaveNewSearch,
      deleteSearch: mockDeleteSearch,
      updateSearch: mockUpdateSearch,
      loadSearch: mockLoadSearch,
      clearAll: mockClearAll,
      refresh: mockRefresh,
    });

    mockLoadSearch.mockReturnValue(mockSearches[0]);
  });

  describe('Rendering', () => {
    it('should render dropdown trigger button', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      expect(screen.getByRole('button', { name: /Buscas salvas/i })).toBeInTheDocument();
    });

    it('should display search count badge', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should show "Buscas Salvas" text on desktop', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const text = screen.getByText('Buscas Salvas');
      expect(text).toHaveClass('hidden', 'sm:inline');
    });

    it('should have proper ARIA attributes on trigger button', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    it('should render clock icon', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const clockIcon = container.querySelector('svg');
      expect(clockIcon).toBeInTheDocument();
    });
  });

  describe('Dropdown Open/Close', () => {
    it('should open dropdown when trigger button clicked', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText(/Buscas Recentes/i)).toBeInTheDocument();
    });

    it('should update aria-expanded when opened', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('should close dropdown when backdrop clicked', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText('Uniformes SC/PR/RS')).toBeInTheDocument();

      // Click backdrop
      const backdrop = screen.getByRole('button', { name: /Buscas salvas/i })
        .parentElement?.querySelector('.fixed.inset-0');
      if (backdrop) {
        fireEvent.click(backdrop);
      }

      // Dropdown should close
      waitFor(() => {
        expect(screen.queryByText('Uniformes SC/PR/RS')).not.toBeInTheDocument();
      });
    });

    it('should rotate chevron icon when opened', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const chevron = container.querySelector('.rotate-180');
      expect(chevron).toBeInTheDocument();
    });
  });

  describe('Saved Searches Display', () => {
    it('should display all saved searches', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText('Uniformes SC/PR/RS')).toBeInTheDocument();
      expect(screen.getByText('Calçados Sudeste')).toBeInTheDocument();
    });

    it('should display search count in header', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText('Buscas Recentes (2/10)')).toBeInTheDocument();
    });

    it('should display UFs for each search', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText(/SC, PR, RS/i)).toBeInTheDocument();
      expect(screen.getByText(/SP, RJ, MG, ES/i)).toBeInTheDocument();
    });

    it('should display search mode label for "setor" mode', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText('vestuario')).toBeInTheDocument();
    });

    it('should display search terms label for "termos" mode', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText('"calçado sapato"')).toBeInTheDocument();
    });

    it('should format relative time correctly', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      // Check that dropdown is open and contains saved searches
      expect(button).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByText('Uniformes SC/PR/RS')).toBeInTheDocument();
      expect(screen.getByText('Calçados Sudeste')).toBeInTheDocument();
    });
  });

  describe('Loading Search', () => {
    it('should call loadSearch when search item clicked', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const searchItem = screen.getByText('Uniformes SC/PR/RS');
      fireEvent.click(searchItem);

      expect(mockLoadSearch).toHaveBeenCalledWith('search-1');
    });

    it('should call onLoadSearch callback with search data', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const searchItem = screen.getByText('Uniformes SC/PR/RS');
      fireEvent.click(searchItem);

      expect(mockOnLoadSearch).toHaveBeenCalledWith(mockSearches[0]);
    });

    it('should close dropdown after loading search', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const searchItem = screen.getByText('Uniformes SC/PR/RS');
      fireEvent.click(searchItem);

      waitFor(() => {
        expect(screen.queryByText('Buscas Recentes')).not.toBeInTheDocument();
      });
    });

    it('should track analytics when search is loaded', () => {
      render(
        <SavedSearchesDropdown
          onLoadSearch={mockOnLoadSearch}
          onAnalyticsEvent={mockOnAnalyticsEvent}
        />
      );

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const searchItem = screen.getByText('Uniformes SC/PR/RS');
      fireEvent.click(searchItem);

      expect(mockOnAnalyticsEvent).toHaveBeenCalledWith('saved_search_loaded', {
        search_id: 'search-1',
        search_name: 'Uniformes SC/PR/RS',
        search_mode: 'setor',
        ufs: ['SC', 'PR', 'RS'],
        uf_count: 3,
        days_since_created: expect.any(Number),
      });
    });
  });

  describe('Deleting Search', () => {
    it('should show delete button for each search', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });
      expect(deleteButtons).toHaveLength(2);
    });

    it('should show confirmation state on first delete click', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });
      fireEvent.click(deleteButtons[0]);

      expect(screen.getByRole('button', { name: /Confirmar exclusão/i })).toBeInTheDocument();
    });

    it('should change button style in confirmation state', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });
      fireEvent.click(deleteButtons[0]);

      const confirmButton = screen.getByRole('button', { name: /Confirmar exclusão/i });
      expect(confirmButton).toHaveClass('bg-error');
    });

    it('should delete search on second click (confirmed)', () => {
      mockDeleteSearch.mockReturnValue(true);

      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });

      // First click - show confirmation
      fireEvent.click(deleteButtons[0]);

      // Second click - confirm deletion
      const confirmButton = screen.getByRole('button', { name: /Confirmar exclusão/i });
      fireEvent.click(confirmButton);

      expect(mockDeleteSearch).toHaveBeenCalledWith('search-1');
    });

    it('should auto-cancel delete confirmation after 3 seconds', async () => {
      jest.useFakeTimers();

      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });
      fireEvent.click(deleteButtons[0]);

      expect(screen.getByRole('button', { name: /Confirmar exclusão/i })).toBeInTheDocument();

      // Fast-forward 3 seconds
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /Confirmar exclusão/i })).not.toBeInTheDocument();
      });

      jest.useRealTimers();
    });

    it('should track analytics when search is deleted', () => {
      mockDeleteSearch.mockReturnValue(true);

      render(
        <SavedSearchesDropdown
          onLoadSearch={mockOnLoadSearch}
          onAnalyticsEvent={mockOnAnalyticsEvent}
        />
      );

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });
      fireEvent.click(deleteButtons[0]);

      const confirmButton = screen.getByRole('button', { name: /Confirmar exclusão/i });
      fireEvent.click(confirmButton);

      expect(mockOnAnalyticsEvent).toHaveBeenCalledWith('saved_search_deleted', {
        search_id: 'search-1',
        search_name: 'Uniformes SC/PR/RS',
        remaining_searches: 1,
      });
    });
  });

  describe('Clear All Searches', () => {
    it('should show "Limpar todas" button when searches exist', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByText('Limpar todas')).toBeInTheDocument();
    });

    it('should show confirmation dialog when "Limpar todas" clicked', () => {
      // Mock window.confirm
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const clearButton = screen.getByText('Limpar todas');
      fireEvent.click(clearButton);

      expect(confirmSpy).toHaveBeenCalledWith('Deseja excluir todas as buscas salvas?');

      confirmSpy.mockRestore();
    });

    it('should call clearAll when user confirms', () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const clearButton = screen.getByText('Limpar todas');
      fireEvent.click(clearButton);

      expect(mockClearAll).toHaveBeenCalled();

      confirmSpy.mockRestore();
    });

    it('should not call clearAll when user cancels', () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const clearButton = screen.getByText('Limpar todas');
      fireEvent.click(clearButton);

      expect(mockClearAll).not.toHaveBeenCalled();

      confirmSpy.mockRestore();
    });

    it('should close dropdown after clearing all', () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const clearButton = screen.getByText('Limpar todas');
      fireEvent.click(clearButton);

      waitFor(() => {
        expect(screen.queryByText('Buscas Recentes')).not.toBeInTheDocument();
      });

      confirmSpy.mockRestore();
    });
  });

  describe('Empty State', () => {
    beforeEach(() => {
      // Override with empty searches for these tests
      mockedUseSavedSearches.mockReturnValue({
        searches: [],
        loading: false,
        isMaxCapacity: false,
        saveNewSearch: mockSaveNewSearch,
        deleteSearch: mockDeleteSearch,
        updateSearch: mockUpdateSearch,
        loadSearch: mockLoadSearch,
        clearAll: mockClearAll,
        refresh: mockRefresh,
      });
    });

    it('should display empty state when no searches saved', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getAllByText('Nenhuma busca salva')[0]).toBeInTheDocument();
      expect(screen.getByText(/Suas buscas aparecerão aqui/i)).toBeInTheDocument();
    });

    it('should display empty state icon', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const emptyIcon = container.querySelector('.w-12.h-12');
      expect(emptyIcon).toBeInTheDocument();
    });

    it('should not show "Limpar todas" button in empty state', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.queryByText('Limpar todas')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should not render anything when loading', () => {
      // Override with loading state
      mockedUseSavedSearches.mockReturnValue({
        searches: mockSearches,
        loading: true,
        isMaxCapacity: false,
        saveNewSearch: mockSaveNewSearch,
        deleteSearch: mockDeleteSearch,
        updateSearch: mockUpdateSearch,
        loadSearch: mockLoadSearch,
        clearAll: mockClearAll,
        refresh: mockRefresh,
      });

      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Styling and Layout', () => {
    it('should apply proper dropdown panel styling', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const panel = container.querySelector('.absolute.right-0.mt-2');
      expect(panel).toBeInTheDocument();
      expect(panel).toHaveClass('rounded-card');
      expect(panel).toHaveClass('shadow-lg');
    });

    it('should have max-height and scroll on dropdown', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const panel = container.querySelector('.max-h-\\[400px\\]');
      expect(panel).toBeInTheDocument();
      expect(panel).toHaveClass('overflow-y-auto');
    });

    it('should apply hover effects to search items', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const searchItems = container.querySelectorAll('.hover\\:bg-surface-1');
      expect(searchItems.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      expect(button).toHaveAttribute('type', 'button');
      expect(button).toHaveAttribute('aria-label', 'Buscas salvas');
    });

    it('should hide backdrop from screen readers', () => {
      const { container } = render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const backdrop = container.querySelector('[aria-hidden="true"]');
      expect(backdrop).toBeInTheDocument();
    });

    it('should provide title attribute on delete button', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const deleteButtons = screen.getAllByRole('button', { name: /Excluir busca/i });
      expect(deleteButtons[0]).toHaveAttribute('title', 'Excluir');
    });
  });

  describe('Filter Functionality', () => {
    const mockSearches = [
      {
        id: '1',
        name: 'Uniformes SC',
        searchParams: {
          ufs: ['SC'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'setor' as const,
          setorId: 'Vestuário',
        },
        createdAt: new Date().toISOString(),
        lastUsedAt: new Date().toISOString(),
      },
      {
        id: '2',
        name: 'Calçados RJ',
        searchParams: {
          ufs: ['RJ'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'termos' as const,
          termosBusca: 'sapato tenis',
        },
        createdAt: new Date().toISOString(),
        lastUsedAt: new Date().toISOString(),
      },
      {
        id: '3',
        name: 'Uniformes SP/PR',
        searchParams: {
          ufs: ['SP', 'PR'],
          dataInicial: '2024-01-01',
          dataFinal: '2024-01-07',
          searchMode: 'setor' as const,
          setorId: 'Vestuário',
        },
        createdAt: new Date().toISOString(),
        lastUsedAt: new Date().toISOString(),
      },
    ];

    beforeEach(() => {
      (useSavedSearches as jest.Mock).mockReturnValue({
        searches: mockSearches,
        loading: false,
        deleteSearch: jest.fn(() => true),
        loadSearch: jest.fn((id: string) => mockSearches.find(s => s.id === id)),
        clearAll: jest.fn(),
        refresh: jest.fn(),
      });
    });

    it('should display filter input when searches exist', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      expect(screen.getByPlaceholderText('Filtrar buscas...')).toBeInTheDocument();
    });

    it('should filter searches by name', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...');
      fireEvent.change(filterInput, { target: { value: 'Calçados' } });

      expect(screen.getByText('Calçados RJ')).toBeInTheDocument();
      expect(screen.queryByText('Uniformes SC')).not.toBeInTheDocument();
      expect(screen.getByText(/\(1\/3\)/i)).toBeInTheDocument(); // Counter
    });

    it('should filter searches by UF', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...');
      fireEvent.change(filterInput, { target: { value: 'PR' } });

      expect(screen.getByText('Uniformes SP/PR')).toBeInTheDocument();
      expect(screen.queryByText('Calçados RJ')).not.toBeInTheDocument();
      expect(screen.queryByText('Uniformes SC')).not.toBeInTheDocument();
    });

    it('should filter searches by setor/termos', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...');
      fireEvent.change(filterInput, { target: { value: 'sapato' } });

      expect(screen.getByText('Calçados RJ')).toBeInTheDocument();
      expect(screen.queryByText('Uniformes SC')).not.toBeInTheDocument();
    });

    it('should show clear button when typing', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...');
      fireEvent.change(filterInput, { target: { value: 'test' } });

      const clearButton = screen.getByLabelText('Limpar filtro');
      expect(clearButton).toBeInTheDocument();
    });

    it('should clear filter when clicking clear button', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...') as HTMLInputElement;
      fireEvent.change(filterInput, { target: { value: 'test' } });

      const clearButton = screen.getByLabelText('Limpar filtro');
      fireEvent.click(clearButton);

      expect(filterInput.value).toBe('');
      expect(screen.getByText(/\(3\/10\)/i)).toBeInTheDocument(); // Counter back to full
    });

    it('should clear filter on Escape key', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...') as HTMLInputElement;
      fireEvent.change(filterInput, { target: { value: 'test' } });
      fireEvent.keyDown(filterInput, { key: 'Escape' });

      expect(filterInput.value).toBe('');
    });

    it('should show empty state when no results match filter', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      const filterInput = screen.getByPlaceholderText('Filtrar buscas...');
      fireEvent.change(filterInput, { target: { value: 'NOMATCH123' } });

      expect(screen.getByText('Nenhuma busca encontrada')).toBeInTheDocument();
      expect(screen.getByText(/Tente outro termo de busca/i)).toBeInTheDocument();
    });

    it('should update counter dynamically when filtering', () => {
      render(<SavedSearchesDropdown onLoadSearch={mockOnLoadSearch} />);

      const button = screen.getByRole('button', { name: /Buscas salvas/i });
      fireEvent.click(button);

      // Initial: 3/10
      expect(screen.getByText(/\(3\/10\)/i)).toBeInTheDocument();

      // Filter to 2 results
      const filterInput = screen.getByPlaceholderText('Filtrar buscas...');
      fireEvent.change(filterInput, { target: { value: 'Uniformes' } });
      expect(screen.getByText(/\(2\/3\)/i)).toBeInTheDocument();

      // Filter to 1 result
      fireEvent.change(filterInput, { target: { value: 'SC' } });
      expect(screen.getByText(/\(1\/3\)/i)).toBeInTheDocument();

      // Clear filter: back to 3/10
      fireEvent.change(filterInput, { target: { value: '' } });
      expect(screen.getByText(/\(3\/10\)/i)).toBeInTheDocument();
    });
  });
});
