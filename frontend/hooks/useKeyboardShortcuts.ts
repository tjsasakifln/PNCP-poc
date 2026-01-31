/**
 * useKeyboardShortcuts Hook
 *
 * Provides keyboard shortcuts for power users
 * Issue #122 [P3] No keyboard shortcuts for power users
 */

import { useEffect } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void;
  description: string;
}

export interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

/**
 * Hook to register keyboard shortcuts
 *
 * @example
 * ```tsx
 * useKeyboardShortcuts({
 *   shortcuts: [
 *     { key: 'k', ctrlKey: true, action: handleSearch, description: 'Quick search' },
 *     { key: 'Escape', action: handleClear, description: 'Clear selection' }
 *   ]
 * });
 * ```
 */
export function useKeyboardShortcuts({ shortcuts, enabled = true }: UseKeyboardShortcutsOptions) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatches = shortcut.ctrlKey ? event.ctrlKey : !event.ctrlKey;
        const metaMatches = shortcut.metaKey ? event.metaKey : !event.metaKey;
        const shiftMatches = shortcut.shiftKey ? event.shiftKey : !event.shiftKey;
        const altMatches = shortcut.altKey ? event.altKey : !event.altKey;

        // Handle Ctrl/Cmd modifier (Cmd on Mac, Ctrl on Windows/Linux)
        const modifierMatches = shortcut.ctrlKey || shortcut.metaKey
          ? (event.ctrlKey || event.metaKey)
          : (!event.ctrlKey && !event.metaKey);

        if (keyMatches && modifierMatches && shiftMatches && altMatches) {
          // Don't trigger if user is typing in an input/textarea
          const target = event.target as HTMLElement;
          const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

          // Allow Escape even in inputs
          if (isInput && event.key !== 'Escape') continue;

          event.preventDefault();
          shortcut.action();
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts, enabled]);
}

/**
 * Get keyboard shortcut display string (for UI hints)
 */
export function getShortcutDisplay(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  // Detect if user is on Mac
  const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().includes('MAC');

  if (shortcut.ctrlKey || shortcut.metaKey) {
    parts.push(isMac ? '⌘' : 'Ctrl');
  }
  if (shortcut.shiftKey) {
    parts.push('Shift');
  }
  if (shortcut.altKey) {
    parts.push(isMac ? '⌥' : 'Alt');
  }

  // Capitalize key for display
  const keyDisplay = shortcut.key === ' ' ? 'Space' : shortcut.key.charAt(0).toUpperCase() + shortcut.key.slice(1);
  parts.push(keyDisplay);

  return parts.join('+');
}
