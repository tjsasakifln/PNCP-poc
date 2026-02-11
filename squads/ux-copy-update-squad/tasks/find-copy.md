---
task: Find Copy in Codebase
responsavel: "@copy-editor"
responsavel_type: agent
atomic_layer: task
elicit: false
Entrada: |
  - search_text: Text to search for
  - file_pattern: Optional glob pattern for files
  - search_scope: Optional directory scope
Saida: |
  - matching_files: List of files containing the text
  - line_numbers: Line numbers for each match
  - preview: Context preview around each match
  - total_matches: Total number of matches found
Checklist:
  - "[ ] Parse search parameters"
  - "[ ] Execute search across codebase"
  - "[ ] Group results by file"
  - "[ ] Show context for each match"
  - "[ ] Provide location details"
  - "[ ] Suggest next actions"
---

# *find-copy

Searches for text content across the codebase to locate all instances before making changes.

## Usage

```bash
@copy-editor

*find-copy "text to search"
*find-copy "text to search" --files "*.tsx"
*find-copy "text to search" --scope frontend/app
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_text` | string | Yes | Text to search for (supports regex) |
| `--files` | string | No | File pattern (e.g., "*.tsx", "*.md") |
| `--scope` | string | No | Directory to search in |
| `--exact` | flag | No | Exact match only (no partial) |
| `--case-sensitive` | flag | No | Case-sensitive search |
| `--context` | number | No | Lines of context (default: 2) |

## Examples

### Example 1: Simple search

```bash
*find-copy "Encontre oportunidades de contratação pública"
```

### Example 2: Search in specific files

```bash
*find-copy "O PNCP está mais lento" --files "*.tsx"
```

### Example 3: Search in directory with context

```bash
*find-copy "Aguarde" --scope frontend/app --context 3
```

### Example 4: Exact match only

```bash
*find-copy "PNCP" --exact
```

## Implementation Steps

1. **Parse Parameters**
   - Extract search_text
   - Parse optional flags
   - Validate search scope

2. **Execute Search**
   - Use Grep tool for efficient search
   - Apply file patterns if specified
   - Search within scope directory

3. **Process Results**
   - Group matches by file
   - Extract line numbers
   - Capture context lines

4. **Format Output**
   - Display file paths
   - Show line numbers and context
   - Highlight matched text
   - Provide summary statistics

## Output Format

```
🔍 Search Results: "Encontre oportunidades de contratação pública"

📁 frontend/app/buscar/page.tsx
   Line 142:
   140 |     <div className="welcome-section">
   141 |       <h2 className="welcome-title">
 → 142 |         Encontre oportunidades de contratação pública no Portal Nacional (PNCP)
   143 |       </h2>
   144 |     </div>

📁 docs/ux/welcome-message-spec.md
   Line 23:
   21 | ## Welcome Message
   22 |
 → 23 | "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)"
   24 |
   25 | This message appears when users first enter the search page.

📊 Summary:
  Total matches: 2
  Files: 2
  - frontend/app/buscar/page.tsx (1 match)
  - docs/ux/welcome-message-spec.md (1 match)

✅ Next steps:
  1. Review each match to understand context
  2. Use *update-copy to replace text in each file
  3. Update documentation files separately
```

## Search Tips

### Finding Loading Messages
```bash
*find-copy "Aguarde" --files "*.tsx"
*find-copy "loading\|carregando" --files "*.tsx"  # Regex
```

### Finding Welcome Messages
```bash
*find-copy "Bem-vindo\|Olá\|Encontre" --scope frontend/app
```

### Finding Error Messages
```bash
*find-copy "erro\|falha\|não foi possível" --files "*.tsx,*.ts"
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `NO_MATCHES` | Text not found | Check spelling, try partial search |
| `TOO_MANY_RESULTS` | Query too broad | Add file pattern or scope |
| `INVALID_REGEX` | Malformed regex | Check regex syntax |
| `PERMISSION_DENIED` | Cannot read files | Check file permissions |

## Related Tasks

- `update-copy.md` - Update text after finding
- `validate-text.md` - Validate found text
- `validate-ux.md` - Review UX quality

## Notes

- Use this task BEFORE *update-copy to locate all instances
- Check documentation files separately
- Consider i18n files if text is translated
- Regex is useful for finding variations
