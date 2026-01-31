# UX Enhancements Implementation Plan

## Completed
✅ **Issue #108** - Offline fallback UI with Service Worker
- Created `/public/sw.js` service worker
- Created `/public/offline.html` offline fallback page
- Created `/hooks/useServiceWorker.ts` hook

✅ **Issue #116** - Dark mode preview before selection
- Enhanced `ThemeToggle.tsx` with hover preview
- Added visual preview indicator
- Shows preview banner when hovering

## Remaining Issues

### Issue #120 - Saved searches dropdown search/filter [P3] (3h)

**Changes Required:**
1. Add `searchQuery` state to `SavedSearchesDropdown.tsx`
2. Add search input field after header
3. Filter searches by name, UFs, or search terms
4. Show "No results" state when filter yields no matches
5. Clear filter when dropdown closes

**Implementation:**
```typescript
// Add state
const [searchQuery, setSearchQuery] = useState('');

// Add filter logic
const filteredSearches = searches.filter((search) => {
  if (!searchQuery.trim()) return true;
  const query = searchQuery.toLowerCase();
  return (
    search.name.toLowerCase().includes(query) ||
    getSearchLabel(search).toLowerCase().includes(query) ||
    search.searchParams.ufs.some((uf) => uf.toLowerCase().includes(query))
  );
});

// Add search input in dropdown (after header, before list)
<div className="px-4 py-2 border-b border-strong">
  <input
    type="text"
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    placeholder="Filtrar buscas..."
    className="w-full px-3 py-2 text-sm border border-strong rounded bg-surface-0"
  />
</div>
```

### Issue #118 - Mobile-optimized date picker [P3] (4h)

**Options:**
1. Use native `<input type="date">` on mobile (already implemented)
2. Add react-datepicker for desktop with mobile fallback
3. Add touch-friendly calendar overlay

**Recommended:** Keep native date input (already mobile-optimized), add better visual feedback

**Changes Required:**
1. Enhance visual design of date inputs
2. Add calendar icon
3. Ensure touch-friendly tap targets (48x48px minimum)
4. Add helper text for format

### Issue #119 - Pull-to-refresh gesture [P3] (3h)

**Implementation:**
1. Add `usePullToRefresh` hook
2. Detect pull gesture with touchstart/touchmove/touchend
3. Show loading indicator during pull
4. Trigger search refresh on release
5. Add visual feedback (arrow/spinner)

**Package Options:**
- react-use-gesture (7KB)
- react-pull-to-refresh (3KB)
- Custom implementation (recommended for control)

**Custom Implementation:**
```typescript
// hooks/usePullToRefresh.ts
export function usePullToRefresh(onRefresh: () => Promise<void>) {
  const [pulling, setPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);

  useEffect(() => {
    let startY = 0;
    let currentY = 0;

    const handleTouchStart = (e: TouchEvent) => {
      if (window.scrollY === 0) {
        startY = e.touches[0].clientY;
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (startY > 0) {
        currentY = e.touches[0].clientY;
        const distance = currentY - startY;
        if (distance > 0 && distance < 150) {
          setPullDistance(distance);
          setPulling(true);
        }
      }
    };

    const handleTouchEnd = async () => {
      if (pullDistance > 80) {
        await onRefresh();
      }
      setPullDistance(0);
      setPulling(false);
      startY = 0;
    };

    document.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [onRefresh, pullDistance]);

  return { pulling, pullDistance };
}
```

### Issue #121 - Excel auto-open [P3] (2h)

**Implementation:**
1. Detect if download succeeded
2. Create object URL for downloaded blob
3. Use `window.open()` to open in new tab
4. Add "Open Excel" button as alternative
5. Show notification with both options

**Changes to `page.tsx`:**
```typescript
const handleDownload = async () => {
  // ... existing download logic ...

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);

  // Option 1: Auto-open in new tab (may be blocked by popup blocker)
  const newWindow = window.open(url, '_blank');

  // Option 2: If popup blocked, show manual open button
  if (!newWindow || newWindow.closed) {
    setDownloadUrl(url); // Store for manual open
    setShowOpenButton(true);
  }

  // Also trigger download as usual
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
};
```

## Testing Plan

### Unit Tests
- [ ] ThemeToggle preview functionality
- [ ] SavedSearchesDropdown filter logic
- [ ] Pull-to-refresh hook
- [ ] Service Worker registration

### E2E Tests
- [ ] Offline page displays on network failure
- [ ] Theme preview shows correct colors
- [ ] Saved search filter works correctly
- [ ] Pull-to-refresh triggers search
- [ ] Excel auto-open attempts
- [ ] Mobile date picker behavior

## Accessibility Checklist
- [ ] Service Worker: Announce offline status to screen readers
- [ ] Theme preview: Keyboard navigation support
- [ ] Search filter: Focus management
- [ ] Pull-to-refresh: ARIA live region for status
- [ ] Date picker: Label association
- [ ] Excel download: Clear success/error messages

## Browser Compatibility
- Service Worker: Chrome 40+, Firefox 44+, Safari 11.1+, Edge 17+
- Pull-to-refresh: Touch events supported on all mobile browsers
- Native date input: Full support on iOS Safari, Android Chrome
- Blob URLs: Universal support

## Performance Considerations
- Service Worker caches only offline page (minimal storage)
- Pull-to-refresh debounced to prevent excessive triggers
- Search filter uses memo/debounce for large lists
- Excel auto-open cleanup: revoke object URLs after use

## Next Steps
1. Implement SavedSearchesDropdown filter (#120)
2. Add pull-to-refresh gesture (#119)
3. Implement Excel auto-open (#121)
4. Enhance date picker styling (#118)
5. Write E2E tests for all features
6. Update documentation
7. Create PR with all enhancements
