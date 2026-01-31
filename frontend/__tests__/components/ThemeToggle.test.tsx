/**
 * ThemeToggle Component Tests
 *
 * Tests theme switching functionality and rendering
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeToggle } from '@/app/components/ThemeToggle';
import { ThemeProvider } from '@/app/components/ThemeProvider';

describe('ThemeToggle Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should render theme toggle button with aria-label', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /Alternar tema/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', 'Alternar tema');
  });

  it('should open dropdown when clicked', async () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggleButton = screen.getByRole('button', { name: /Alternar tema/i });

    // Initially dropdown should not be visible (check aria-expanded)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

    // Click to open dropdown
    fireEvent.click(toggleButton);

    // Dropdown should now be visible (aria-expanded true)
    await waitFor(() => {
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });

    // All theme options should be visible
    const themeButtons = screen.getAllByRole('button');
    expect(themeButtons.length).toBeGreaterThan(1); // Toggle button + theme options
  });

  it('should switch theme when option clicked', async () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggleButton = screen.getByRole('button', { name: /Alternar tema/i });

    // Open dropdown
    fireEvent.click(toggleButton);

    // Click on "Dark" theme
    const darkOption = screen.getByText('Dark');
    fireEvent.click(darkOption);

    // Check that theme was applied
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    // Dropdown should close after selection
    await waitFor(() => {
      expect(screen.queryByText('Light')).not.toBeInTheDocument();
    });
  });

  it('should persist theme preference to localStorage', async () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggleButton = screen.getByRole('button', { name: /Alternar tema/i });

    // Open dropdown and select dark theme
    fireEvent.click(toggleButton);

    // Wait for dropdown to be visible, then find the Dark button
    await waitFor(() => {
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });

    const darkOption = screen.getAllByRole('button').find(btn => btn.textContent === 'Dark');
    fireEvent.click(darkOption!);

    // Check localStorage (correct key is 'descomplicita-theme')
    await waitFor(() => {
      expect(localStorage.getItem('descomplicita-theme')).toBe('dark');
    });
  });

  it('should close dropdown when clicking outside', async () => {
    render(
      <ThemeProvider>
        <div>
          <ThemeToggle />
          <div data-testid="outside">Outside</div>
        </div>
      </ThemeProvider>
    );

    const toggleButton = screen.getByRole('button', { name: /Alternar tema/i });

    // Open dropdown
    fireEvent.click(toggleButton);

    // Wait for dropdown to open
    await waitFor(() => {
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });

    // Click outside
    const outside = screen.getByTestId('outside');
    fireEvent.mouseDown(outside);

    // Dropdown should close (check aria-expanded)
    await waitFor(() => {
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
    });
  });

  it('should display current theme preview color', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggleButton = screen.getByRole('button', { name: /Alternar tema/i });

    // Should have a color preview element
    const preview = toggleButton.querySelector('.rounded-full');
    expect(preview).toBeInTheDocument();
  });
});
