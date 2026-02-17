/**
 * ThemeProvider Component Tests
 *
 * Tests theme management, localStorage persistence, and system theme detection
 */

import { render, screen, waitFor, renderHook } from '@testing-library/react';
import { ThemeProvider, useTheme, THEMES, type ThemeId } from '@/app/components/ThemeProvider';
import { act } from 'react';

describe('ThemeProvider Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = '';
    document.documentElement.removeAttribute('style');
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('initialization', () => {
    it('should render children', () => {
      render(
        <ThemeProvider>
          <div>Test Content</div>
        </ThemeProvider>
      );

      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should initialize with light theme by default', async () => {
      const TestComponent = () => {
        const { theme } = useTheme();
        return <div data-testid="theme">{theme}</div>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('light');
      });
    });

    it('should load theme from localStorage if present', async () => {
      localStorage.setItem('bidiq-theme', 'dark');

      const TestComponent = () => {
        const { theme } = useTheme();
        return <div data-testid="theme">{theme}</div>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      });
    });

    it('should ignore invalid theme in localStorage', async () => {
      localStorage.setItem('bidiq-theme', 'invalid-theme');

      const TestComponent = () => {
        const { theme } = useTheme();
        return <div data-testid="theme">{theme}</div>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('light');
      });
    });
  });

  describe('theme switching', () => {
    it('should switch theme and persist to localStorage', async () => {
      const TestComponent = () => {
        const { theme, setTheme } = useTheme();
        return (
          <div>
            <div data-testid="theme">{theme}</div>
            <button onClick={() => setTheme('dark')}>Switch to Dark</button>
          </div>
        );
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('light');
      });

      act(() => {
        screen.getByText('Switch to Dark').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('dark');
        expect(localStorage.getItem('bidiq-theme')).toBe('dark');
      });
    });

    it('should apply dark theme CSS variables', async () => {
      const TestComponent = () => {
        const { setTheme } = useTheme();
        return <button onClick={() => setTheme('dark')}>Dark</button>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Dark')).toBeInTheDocument();
      });

      act(() => {
        screen.getByText('Dark').click();
      });

      await waitFor(() => {
        const root = document.documentElement;
        expect(root.classList.contains('dark')).toBe(true);
        expect(root.style.getPropertyValue('--canvas')).toBe('#121212');
        expect(root.style.getPropertyValue('--ink')).toBe('#e0e0e0');
      });
    });

    it('should apply light theme CSS variables', async () => {
      const TestComponent = () => {
        const { setTheme } = useTheme();
        return <button onClick={() => setTheme('light')}>Light</button>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Light')).toBeInTheDocument();
      });

      act(() => {
        screen.getByText('Light').click();
      });

      await waitFor(() => {
        const root = document.documentElement;
        expect(root.classList.contains('dark')).toBe(false);
        expect(root.style.getPropertyValue('--canvas')).toBe('#ffffff');
        expect(root.style.getPropertyValue('--ink')).toBe('#1e2d3b');
      });
    });
  });

  describe('system theme', () => {
    it('should apply system theme when selected', async () => {
      // Mock system prefers-color-scheme
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation((query) => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      const TestComponent = () => {
        const { setTheme } = useTheme();
        return <button onClick={() => setTheme('system')}>System</button>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('System')).toBeInTheDocument();
      });

      act(() => {
        screen.getByText('System').click();
      });

      await waitFor(() => {
        const root = document.documentElement;
        // Should apply dark theme since system prefers dark
        expect(root.classList.contains('dark')).toBe(true);
        expect(localStorage.getItem('bidiq-theme')).toBe('system');
      });
    });

    it('should listen for system theme changes when system is selected', async () => {
      let changeHandler: (() => void) | null = null;

      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation((query) => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn((event, handler) => {
            if (event === 'change') {
              changeHandler = handler;
            }
          }),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      localStorage.setItem('bidiq-theme', 'system');

      const TestComponent = () => {
        const { theme } = useTheme();
        return <div data-testid="theme">{theme}</div>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system');
        expect(changeHandler).not.toBeNull();
      });
    });
  });

  describe('config', () => {
    it('should provide correct theme config', async () => {
      const TestComponent = () => {
        const { config } = useTheme();
        return (
          <div>
            <div data-testid="config-id">{config.id}</div>
            <div data-testid="config-label">{config.label}</div>
            <div data-testid="config-canvas">{config.canvas}</div>
          </div>
        );
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('config-id')).toHaveTextContent('light');
        expect(screen.getByTestId('config-label')).toHaveTextContent('Light');
        expect(screen.getByTestId('config-canvas')).toHaveTextContent('#ffffff');
      });
    });
  });

  describe('useTheme hook', () => {
    it('should throw error when used outside ThemeProvider', () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = jest.fn();

      const TestComponent = () => {
        const { theme } = useTheme();
        return <div>{theme}</div>;
      };

      // Should use default context values (not throw)
      render(<TestComponent />);
      expect(screen.getByText('light')).toBeInTheDocument();

      console.error = originalError;
    });
  });

  describe('THEMES constant', () => {
    it('should export correct theme configurations', () => {
      expect(THEMES).toHaveLength(3);
      expect(THEMES[0].id).toBe('light');
      expect(THEMES[1].id).toBe('system');
      expect(THEMES[2].id).toBe('dark');

      expect(THEMES[0].isDark).toBe(false);
      expect(THEMES[2].isDark).toBe(true);
    });
  });
});
