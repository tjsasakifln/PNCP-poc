import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  ContextualTutorialTooltip,
  useContextualTutorial,
} from '@/app/components/ContextualTutorialTooltip';
import { renderHook } from '@testing-library/react';

describe('ContextualTutorialTooltip', () => {
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    // Create a target element for the tooltip
    const targetElement = document.createElement('div');
    targetElement.setAttribute('data-testid', 'target-element');
    targetElement.style.position = 'absolute';
    targetElement.style.top = '100px';
    targetElement.style.left = '200px';
    targetElement.style.width = '100px';
    targetElement.style.height = '50px';
    document.body.appendChild(targetElement);
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('renders when isActive is true and target exists', () => {
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );
    expect(screen.getByText('Test tooltip message')).toBeInTheDocument();
  });

  it('does not render when isActive is false', () => {
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={false}
        onDismiss={mockOnDismiss}
      />
    );
    expect(screen.queryByText('Test tooltip message')).not.toBeInTheDocument();
  });

  it('shows dismiss button', () => {
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );
    expect(screen.getByLabelText('Dispensar dica')).toBeInTheDocument();
  });

  it('calls onDismiss when dismiss button is clicked', async () => {
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );

    const dismissButton = screen.getByLabelText('Dispensar dica');
    fireEvent.click(dismissButton);

    await waitFor(() => {
      expect(mockOnDismiss).toHaveBeenCalled();
    }, { timeout: 500 });
  });

  it('calls onDismiss when backdrop is clicked', async () => {
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );

    const backdrop = document.querySelector('.fixed.inset-0') as HTMLElement;
    fireEvent.click(backdrop);

    await waitFor(() => {
      expect(mockOnDismiss).toHaveBeenCalled();
    }, { timeout: 500 });
  });

  it('auto-dismisses after autoDismiss time', async () => {
    jest.useFakeTimers();
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
        autoDismiss={100}
      />
    );

    act(() => {
      jest.advanceTimersByTime(400);
    });

    await waitFor(() => {
      expect(mockOnDismiss).toHaveBeenCalled();
    });

    jest.useRealTimers();
  });

  it('uses default autoDismiss of 8000ms', async () => {
    jest.useFakeTimers();
    render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );

    act(() => {
      jest.advanceTimersByTime(7999);
    });
    expect(mockOnDismiss).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(400);
    });

    await waitFor(() => {
      expect(mockOnDismiss).toHaveBeenCalled();
    });

    jest.useRealTimers();
  });

  it('logs warning when target element not found', () => {
    const consoleWarn = jest.spyOn(console, 'warn').mockImplementation();

    render(
      <ContextualTutorialTooltip
        target="[data-testid='non-existent']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );

    expect(consoleWarn).toHaveBeenCalledWith(
      expect.stringContaining('Target element "[data-testid=\'non-existent\']" not found')
    );

    consoleWarn.mockRestore();
  });

  it('positions tooltip above target element', () => {
    const { container } = render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );

    const tooltip = container.querySelector('.fixed.z-50') as HTMLElement;
    expect(tooltip).toBeInTheDocument();
    expect(tooltip.style.transform).toContain('translate(-50%, -100%)');
  });

  it('renders backdrop with correct classes', () => {
    const { container } = render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
      />
    );

    const backdrop = container.querySelector('.fixed.inset-0.z-40');
    expect(backdrop).toBeInTheDocument();
  });

  it('cleans up timer on unmount', () => {
    jest.useFakeTimers();
    const { unmount } = render(
      <ContextualTutorialTooltip
        target="[data-testid='target-element']"
        message="Test tooltip message"
        isActive={true}
        onDismiss={mockOnDismiss}
        autoDismiss={100}
      />
    );

    unmount();

    act(() => {
      jest.advanceTimersByTime(400);
    });

    expect(mockOnDismiss).not.toHaveBeenCalled();
    jest.useRealTimers();
  });
});

describe('useContextualTutorial', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('initializes with no active tooltip', () => {
    const { result } = renderHook(() => useContextualTutorial());
    expect(result.current.activeTooltip).toBeNull();
  });

  it('loads onboarding step from localStorage', () => {
    localStorage.setItem('onboarding_step', '2');
    const { result } = renderHook(() => useContextualTutorial());
    expect(result.current.onboardingStep).toBe(2);
  });

  it('tracks time on page', () => {
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      jest.advanceTimersByTime(3000);
    });

    // Time tracking is internal, but we can verify it doesn't crash
    expect(result.current.activeTooltip).toBeDefined();
  });

  it('triggers hesitation tooltip after 8 seconds', () => {
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      jest.advanceTimersByTime(8000);
    });

    expect(result.current.activeTooltip).toBe('hesitation');
  });

  it('does not trigger hesitation if onboarding completed', () => {
    localStorage.setItem('onboarding_step', '3');
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      jest.advanceTimersByTime(8000);
    });

    expect(result.current.activeTooltip).toBeNull();
  });

  it('triggers search without filters tooltip', () => {
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      result.current.triggerSearchWithoutFilters();
    });

    expect(result.current.activeTooltip).toBe('no-filters');
  });

  it('triggers help tooltip', () => {
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      result.current.triggerHelpClick();
    });

    expect(result.current.activeTooltip).toBe('help');
  });

  it('dismisses tooltip and advances onboarding step', () => {
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      result.current.triggerHelpClick();
    });

    expect(result.current.activeTooltip).toBe('help');
    expect(result.current.onboardingStep).toBe(0);

    act(() => {
      result.current.dismissTooltip();
    });

    expect(result.current.activeTooltip).toBeNull();
    expect(result.current.onboardingStep).toBe(1);
    expect(localStorage.getItem('onboarding_step')).toBe('1');
  });

  it('does not advance onboarding beyond step 3', () => {
    localStorage.setItem('onboarding_step', '3');
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      result.current.triggerHelpClick();
    });

    act(() => {
      result.current.dismissTooltip();
    });

    expect(result.current.onboardingStep).toBe(3);
  });

  it('resets onboarding progress', () => {
    localStorage.setItem('onboarding_step', '2');
    const { result } = renderHook(() => useContextualTutorial());

    act(() => {
      result.current.triggerHelpClick();
    });

    expect(result.current.activeTooltip).toBe('help');
    expect(result.current.onboardingStep).toBe(2);

    act(() => {
      result.current.resetOnboarding();
    });

    expect(result.current.activeTooltip).toBeNull();
    expect(result.current.onboardingStep).toBe(0);
    expect(localStorage.getItem('onboarding_step')).toBe('0');
  });
});
