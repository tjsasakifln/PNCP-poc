/**
 * useKeyboardShortcuts Hook Tests
 *
 * Tests keyboard shortcut functionality for power users
 * Issue #122 [P3] No keyboard shortcuts for power users
 */

import { renderHook } from '@testing-library/react';
import { useKeyboardShortcuts, getShortcutDisplay } from '@/hooks/useKeyboardShortcuts';

describe('useKeyboardShortcuts Hook', () => {
  let actionMock: jest.Mock;

  beforeEach(() => {
    actionMock = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Keyboard Event Handling', () => {
    it('should trigger action when matching key is pressed', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalledTimes(1);
    });

    it('should work with Cmd key on Mac (metaKey)', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', metaKey: true, action: actionMock, description: 'Test' }]
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', metaKey: true });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalled();
    });

    it('should handle Escape key without modifiers', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'Escape', action: actionMock, description: 'Clear' }]
      }));

      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalled();
    });

    it('should not trigger when modifier keys dont match', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      // Press 'k' without Ctrl
      const event = new KeyboardEvent('keydown', { key: 'k' });
      window.dispatchEvent(event);

      expect(actionMock).not.toHaveBeenCalled();
    });

    it('should be case insensitive', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'K', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalled();
    });
  });

  describe('Input Element Handling', () => {
    it('should not trigger shortcuts when typing in input field', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      const input = document.createElement('input');
      document.body.appendChild(input);

      const event = new KeyboardEvent('keydown', {
        key: 'k',
        ctrlKey: true,
        bubbles: true
      });

      Object.defineProperty(event, 'target', { value: input, enumerable: true });
      window.dispatchEvent(event);

      expect(actionMock).not.toHaveBeenCalled();

      document.body.removeChild(input);
    });

    it('should allow Escape even in input fields', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'Escape', action: actionMock, description: 'Clear' }]
      }));

      const input = document.createElement('input');
      document.body.appendChild(input);

      const event = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true
      });

      Object.defineProperty(event, 'target', { value: input, enumerable: true });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalled();

      document.body.removeChild(input);
    });

    it('should not trigger when typing in textarea', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'a', ctrlKey: true, action: actionMock, description: 'Select All' }]
      }));

      const textarea = document.createElement('textarea');
      document.body.appendChild(textarea);

      const event = new KeyboardEvent('keydown', {
        key: 'a',
        ctrlKey: true,
        bubbles: true
      });

      Object.defineProperty(event, 'target', { value: textarea, enumerable: true });
      window.dispatchEvent(event);

      expect(actionMock).not.toHaveBeenCalled();

      document.body.removeChild(textarea);
    });
  });

  describe('Multiple Shortcuts', () => {
    it('should handle multiple shortcuts', () => {
      const action1 = jest.fn();
      const action2 = jest.fn();

      renderHook(() => useKeyboardShortcuts({
        shortcuts: [
          { key: 'k', ctrlKey: true, action: action1, description: 'Search' },
          { key: 'Escape', action: action2, description: 'Clear' }
        ]
      }));

      const event1 = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event1);

      expect(action1).toHaveBeenCalled();
      expect(action2).not.toHaveBeenCalled();

      action1.mockClear();

      const event2 = new KeyboardEvent('keydown', { key: 'Escape' });
      window.dispatchEvent(event2);

      expect(action1).not.toHaveBeenCalled();
      expect(action2).toHaveBeenCalled();
    });

    it('should trigger first matching shortcut only', () => {
      const action1 = jest.fn();
      const action2 = jest.fn();

      renderHook(() => useKeyboardShortcuts({
        shortcuts: [
          { key: 'k', ctrlKey: true, action: action1, description: 'First' },
          { key: 'k', ctrlKey: true, action: action2, description: 'Second' }
        ]
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(action1).toHaveBeenCalled();
      expect(action2).not.toHaveBeenCalled();
    });
  });

  describe('Enabled/Disabled State', () => {
    it('should not trigger shortcuts when disabled', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }],
        enabled: false
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(actionMock).not.toHaveBeenCalled();
    });

    it('should work when enabled is true', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }],
        enabled: true
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalled();
    });

    it('should default to enabled when not specified', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(actionMock).toHaveBeenCalled();
    });
  });

  describe('Event Prevention', () => {
    it('should preventDefault when shortcut matches', () => {
      renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      window.dispatchEvent(event);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Cleanup', () => {
    it('should remove event listener on unmount', () => {
      const { unmount } = renderHook(() => useKeyboardShortcuts({
        shortcuts: [{ key: 'k', ctrlKey: true, action: actionMock, description: 'Test' }]
      }));

      unmount();

      const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
      window.dispatchEvent(event);

      expect(actionMock).not.toHaveBeenCalled();
    });
  });
});

describe('getShortcutDisplay Utility', () => {
  // Mock navigator.platform
  const originalPlatform = navigator.platform;

  afterEach(() => {
    Object.defineProperty(navigator, 'platform', {
      value: originalPlatform,
      writable: true
    });
  });

  it('should show Cmd symbol on Mac', () => {
    Object.defineProperty(navigator, 'platform', {
      value: 'MacIntel',
      writable: true
    });

    const display = getShortcutDisplay({
      key: 'k',
      ctrlKey: true,
      action: () => {},
      description: ''
    });

    expect(display).toBe('⌘+K');
  });

  it('should show Ctrl on Windows/Linux', () => {
    Object.defineProperty(navigator, 'platform', {
      value: 'Win32',
      writable: true
    });

    const display = getShortcutDisplay({
      key: 'k',
      ctrlKey: true,
      action: () => {},
      description: ''
    });

    expect(display).toBe('Ctrl+K');
  });

  it('should include Shift modifier', () => {
    const display = getShortcutDisplay({
      key: 'K',
      ctrlKey: true,
      shiftKey: true,
      action: () => {},
      description: ''
    });

    expect(display).toContain('Shift');
  });

  it('should handle key without modifiers', () => {
    const display = getShortcutDisplay({
      key: 'Escape',
      action: () => {},
      description: ''
    });

    expect(display).toBe('Escape');
  });

  it('should capitalize single letter keys', () => {
    const display = getShortcutDisplay({
      key: 'k',
      ctrlKey: true,
      action: () => {},
      description: ''
    });

    expect(display).toContain('K');
  });

  it('should handle special keys', () => {
    const display = getShortcutDisplay({
      key: ' ',
      action: () => {},
      description: ''
    });

    expect(display).toBe('Space');
  });
});
