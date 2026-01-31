# Keyboard Shortcuts - BidIQ Uniformes

Power user keyboard shortcuts for faster navigation and interaction.

## Available Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+K` (Windows/Linux) <br> `⌘+K` (Mac) | Execute Search | Triggers the search with current form parameters |
| `Ctrl+A` (Windows/Linux) <br> `⌘+A` (Mac) | Select All States | Selects all 27 Brazilian states |
| `Esc` | Clear Selection | Clears all selected UFs |
| `/` or `?` | Show Shortcuts Help | Opens keyboard shortcuts help dialog |

## Form Navigation

### Custom Select Component
- **Arrow Down**: Open dropdown / Move to next option
- **Arrow Up**: Open dropdown / Move to previous option
- **Enter** or **Space**: Select highlighted option
- **Escape**: Close dropdown
- **Home**: Jump to first option
- **End**: Jump to last option
- **Tab**: Close dropdown and move to next field

### Custom Date Input
- **Click** or **Tab**: Focus input and open native date picker
- **Arrow Keys**: Navigate through calendar (native behavior)
- **Enter**: Confirm selected date (native behavior)
- **Escape**: Close date picker (native behavior)

## Region Selector

### Keyboard Accessibility
- **Tab**: Navigate between region buttons
- **Enter** or **Space**: Toggle region selection
- **Shift+Tab**: Navigate backwards

### Visual Feedback
- **Hover**: Scale animation (1.05x)
- **Click**: Press animation (0.95x scale)
- **Focus**: Visible focus ring

## Accessibility Features

All keyboard shortcuts respect:
- ✅ WCAG 2.1 Level AA compliance
- ✅ Screen reader compatibility
- ✅ Reduced motion preferences (`prefers-reduced-motion: reduce`)
- ✅ Focus management and visible focus indicators
- ✅ Proper ARIA attributes (role, aria-label, aria-expanded, etc.)

## Implementation Details

### Hook: `useKeyboardShortcuts`

Located in: `frontend/hooks/useKeyboardShortcuts.ts`

Features:
- Event delegation
- Input field awareness (doesn't trigger in text inputs except Escape)
- Cross-platform modifier key support (Ctrl/Cmd)
- Event prevention to avoid browser defaults
- Automatic cleanup on unmount

### Custom Components

**CustomSelect** (`frontend/app/components/CustomSelect.tsx`):
- Full keyboard navigation
- ARIA compliant (role="combobox", role="listbox", role="option")
- Scroll-into-view for highlighted options
- Mouse and keyboard interaction parity

**CustomDateInput** (`frontend/app/components/CustomDateInput.tsx`):
- Native date picker integration
- Styled overlay with calendar icon
- Visual feedback on focus
- Brazilian date format display (DD/MM/YYYY)

**RegionSelector** (`frontend/app/components/RegionSelector.tsx`):
- Click animations (scale transforms)
- Hover effects
- State tracking for animation timing
- Accessible button interactions

## Analytics Tracking

All keyboard shortcuts trigger analytics events:
- Event name: `keyboard_shortcut_used`
- Properties: `{ shortcut: string, action: string }`

This allows monitoring of power user behavior and shortcut adoption.

## Browser Compatibility

Tested and working on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Future Enhancements

Potential additions (not currently implemented):
- `Ctrl+/`: Toggle between search modes (Setor vs Termos)
- `Ctrl+S`: Save current search
- `Ctrl+D`: Download results (when available)
- `Ctrl+L`: Load saved search dropdown
- `Ctrl+T`: Toggle theme (dark/light mode)

## Related Issues

- Issue #122 [P3] No keyboard shortcuts for power users
- Issue #123 [P3] RegionSelector has no click animation
- Issue #89 feat(frontend): substituir native form controls por custom
