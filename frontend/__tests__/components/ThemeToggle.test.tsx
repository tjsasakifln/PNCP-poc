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

  it('should open dropdown when clicked', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggleButton = screen.getByRole('button', { name: /Alternar tema/i });

    // Initially dropdown should not be visible
    expect(screen.queryByText('Light')).not.toBeInTheDocument();

    // Click to open dropdown
    fireEvent.click(toggleButton);

    // Dropdown should now be visible
    expect(screen.getByText('Light')).toBeInTheDocument();
    expect(screen.getByText('Dark')).toBeInTheDocument();
    expect(screen.getByText('Paperwhite')).toBeInTheDocument();
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
    const darkOption = screen.getByText('Dark');
    fireEvent.click(darkOption);

    // Check localStorage
    await waitFor(() => {
      expect(localStorage.getItem('theme')).toBe('dark');
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
    expect(screen.getByText('Light')).toBeInTheDocument();

    // Click outside
    const outside = screen.getByTestId('outside');
    fireEvent.mouseDown(outside);

    // Dropdown should close
    await waitFor(() => {
      expect(screen.queryByText('Light')).not.toBeInTheDocument();
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
