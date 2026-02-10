# Coding Standards - UX Error Fix Squad

## Overview

This squad follows the project-wide coding standards with specific emphasis on debugging, logging, and data integrity practices.

## General Principles

1. **Code Quality**
   - Write clean, readable, self-documenting code
   - Follow DRY (Don't Repeat Yourself)
   - KISS (Keep It Simple, Stupid)
   - YAGNI (You Aren't Gonna Need It)

2. **Error Handling**
   - Always handle errors explicitly
   - Log errors with context
   - Provide meaningful error messages
   - Never swallow exceptions silently

3. **Testing**
   - Write tests for all bug fixes
   - Test edge cases thoroughly
   - Maintain test coverage above 80%
   - Use descriptive test names

## Language-Specific Standards

### TypeScript/JavaScript (Frontend)

#### Code Style
```typescript
// Use const/let, never var
const userName = 'John';
let userBalance = 10;

// Use arrow functions for callbacks
const handleSearch = async () => {
  try {
    const results = await api.search(query);
    setResults(results);
  } catch (error) {
    handleError(error);
  }
};

// Use optional chaining
const errorMsg = error.response?.data?.detail?.message || 'Unknown error';

// Use nullish coalescing
const balance = userBalance ?? 0;
```

#### Error Handling
```typescript
// Always catch and handle errors
try {
  const response = await api.call();
  // Handle success
} catch (error) {
  if (axios.isAxiosError(error)) {
    // Handle API errors
    const message = extractErrorMessage(error);
    showToast(message, 'error');
  } else {
    // Handle unexpected errors
    console.error('Unexpected error:', error);
    showToast('Erro inesperado', 'error');
  }
}
```

#### State Management
```typescript
// Use React hooks properly
const [results, setResults] = useState<SearchResult[]>([]);

// Clean up effects
useEffect(() => {
  const subscription = subscribe();
  return () => subscription.unsubscribe();
}, [dependency]);

// Persist important state
useEffect(() => {
  localStorage.setItem('searchState', JSON.stringify(state));
}, [state]);
```

### Python (Backend)

#### Code Style
```python
# Use type hints
def search_licitacoes(
    query: str,
    user_id: str,
    date_range: int
) -> List[SearchResult]:
    """
    Search for licitações with given parameters.

    Args:
        query: Search query string
        user_id: User identifier
        date_range: Number of days to search

    Returns:
        List of search results

    Raises:
        HTTPException: If validation fails or API error occurs
    """
    pass

# Use context managers for resources
with db.begin():
    # Database operations
    db.add(record)
    # Automatically commits or rolls back
```

#### Error Handling
```python
# Handle exceptions explicitly
try:
    result = perform_search(query)
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Database error")
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### Database Operations
```python
# Always use transactions
async def save_search_history(
    db: AsyncSession,
    user_id: str,
    search_data: dict
) -> SearchHistory:
    """Save search to history with transaction."""
    async with db.begin():
        record = SearchHistory(
            user_id=user_id,
            query=search_data['query'],
            results_count=len(search_data['results'])
        )
        db.add(record)
        await db.flush()  # Get ID before commit
        await db.commit()
        return record

# Handle concurrent operations
async with db.begin():
    # Use SELECT FOR UPDATE for critical reads
    balance = await db.execute(
        select(UserBalance)
        .where(UserBalance.user_id == user_id)
        .with_for_update()
    )
    # Update balance atomically
    balance.searches_remaining -= 1
```

## Debugging Standards

### Logging

#### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

#### Logging Best Practices
```python
# Frontend (JavaScript)
console.debug('User flow:', {step: 'search', state});
console.info('Search completed:', {query, resultsCount});
console.warn('Slow API response:', {duration: 5000});
console.error('API failure:', {error, endpoint, params});

# Backend (Python)
logger.debug(f"Processing search: query={query}, user={mask_user_id(user_id)}")
logger.info(f"Search completed: {results_count} results")
logger.warning(f"Slow query detected: {duration}ms")
logger.error(f"Search failed: {error}", exc_info=True)
```

#### Sensitive Data
```python
# NEVER log sensitive data
logger.error(f"Auth failed for user {user_id}")  # ❌ BAD

# Mask or omit sensitive data
logger.error(f"Auth failed for user {mask_user_id(user_id)}")  # ✅ GOOD

def mask_user_id(user_id: str) -> str:
    """Mask user ID for logging."""
    if len(user_id) > 8:
        return f"{user_id[:8]}***"
    return "***"
```

### Tracing

#### Request Tracing
```python
# Add request ID to all logs
request_id = str(uuid.uuid4())
logger.info(f"[{request_id}] Starting search", extra={'request_id': request_id})

# Frontend
const requestId = generateId();
console.log(`[${requestId}] API call started`);
```

#### State Tracing
```typescript
// Log state changes during debugging
useEffect(() => {
  console.debug('State changed:', {
    previous: previousState,
    current: currentState,
    trigger: 'navigation'
  });
}, [currentState]);
```

## Data Integrity Standards

### Transaction Management

```python
# Atomic operations
async def consume_balance_and_save(
    db: AsyncSession,
    user_id: str,
    search_data: dict
) -> tuple[UserBalance, SearchHistory]:
    """Atomically consume balance and save search."""
    async with db.begin():
        # Deduct balance
        balance = await deduct_balance(db, user_id, 1)

        # Save history
        history = await save_history(db, user_id, search_data)

        # Both succeed or both fail
        return balance, history
```

### Validation

```python
# Validate input
from pydantic import BaseModel, validator

class SearchRequest(BaseModel):
    query: str
    date_range: int

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

    @validator('date_range')
    def date_range_positive(cls, v):
        if v < 1:
            raise ValueError('Date range must be positive')
        return v
```

## Testing Standards

### Unit Tests
```python
# Test file naming: test_<module>.py
# Test function naming: test_<function>_<scenario>

def test_search_history_saved_on_success():
    """Test that search history is saved after successful search."""
    # Arrange
    user = create_test_user()
    query = "test query"

    # Act
    result = perform_search(user.id, query)

    # Assert
    assert result.success
    history = get_search_history(user.id)
    assert len(history) == 1
    assert history[0].query == query
```

### Integration Tests
```typescript
// E2E test naming: test_<feature>_<scenario>

test('search results persist after navigation', async ({ page }) => {
  // Arrange
  await login(page);
  await navigateTo(page, '/buscar');

  // Act
  await performSearch(page, 'licitacao');
  const resultsCount = await getResultsCount(page);
  await navigateTo(page, '/menu');
  await navigateTo(page, '/buscar');

  // Assert
  const persistedCount = await getResultsCount(page);
  expect(persistedCount).toBe(resultsCount);
});
```

## Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All errors handled explicitly
- [ ] Logs include sufficient context
- [ ] Sensitive data masked in logs
- [ ] Database operations use transactions
- [ ] Input validation implemented
- [ ] Tests cover edge cases
- [ ] No console.log in production code
- [ ] Error messages user-friendly
- [ ] State persistence verified

## Documentation Standards

### Code Comments
```typescript
// Good: Explain WHY, not WHAT
// Clear localStorage on logout to prevent state leak
localStorage.clear();

// Bad: Comments that restate the code
// Clear local storage
localStorage.clear();
```

### Function Documentation
```python
def consolidate_findings(
    ux_findings: dict,
    backend_findings: dict,
    qa_findings: dict
) -> dict:
    """
    Consolidate findings from all investigation teams.

    Analyzes findings from UX, backend, and QA teams to identify
    common patterns and root causes. Prioritizes issues by severity
    and user impact.

    Args:
        ux_findings: User experience investigation results
        backend_findings: Technical investigation results
        qa_findings: Quality assurance test results

    Returns:
        Dictionary containing:
        - consolidated_report: Combined analysis
        - root_causes: List of identified root causes
        - priority: Issue priority (P0-P3)

    Example:
        >>> findings = consolidate_findings(
        ...     ux_findings={'breakpoint': 'navigation'},
        ...     backend_findings={'issue': 'missing_commit'},
        ...     qa_findings={'failed': ['test_persistence']}
        ... )
        >>> findings['root_causes']
        ['Transaction not committed', 'State not persisted']
    """
    pass
```

## References

- [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Python PEP 8](https://pep8.org/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [React Best Practices](https://react.dev/learn/thinking-in-react)
