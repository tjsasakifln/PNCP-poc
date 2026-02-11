---
task: Update Copy in Code Files
responsavel: "@copy-editor"
responsavel_type: agent
atomic_layer: task
elicit: false
Entrada: |
  - file_path: Path to the file containing the text
  - old_text: Exact text to be replaced
  - new_text: New text to replace with
  - context: Optional context about the change
Saida: |
  - updated_files: List of files updated
  - diff_summary: Summary of changes made
  - backup_path: Path to backup (if created)
  - success: Boolean indicating success/failure
Checklist:
  - "[ ] Validate file exists"
  - "[ ] Locate exact text match"
  - "[ ] Create backup if needed"
  - "[ ] Perform text replacement"
  - "[ ] Verify syntax remains valid"
  - "[ ] Show diff of changes"
  - "[ ] Confirm update successful"
---

# *update-copy

Updates text content in code files with exact string replacement.

## Usage

```bash
@copy-editor

*update-copy <file_path> <old_text> <new_text>
*update-copy <file_path> <old_text> <new_text> --context "reason for change"
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Path to file (absolute or relative) |
| `old_text` | string | Yes | Exact text to find and replace |
| `new_text` | string | Yes | New text to replace with |
| `--context` | string | No | Context or reason for the change |
| `--backup` | flag | No | Create backup before change (default: true) |
| `--dry-run` | flag | No | Preview changes without applying |

## Examples

### Example 1: Simple text replacement

```bash
*update-copy frontend/app/buscar/page.tsx "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)" "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio."
```

### Example 2: With context

```bash
*update-copy frontend/app/buscar/page.tsx "O PNCP está mais lento" "Estamos trabalhando nisso" --context "Improve user messaging"
```

### Example 3: Dry run (preview)

```bash
*update-copy frontend/app/buscar/page.tsx "old text" "new text" --dry-run
```

## Implementation Steps

1. **Validate Inputs**
   - Check file exists
   - Validate old_text is not empty
   - Validate new_text is different from old_text

2. **Locate Text**
   - Search for exact match of old_text
   - If not found, report error with suggestions
   - If multiple matches, list all locations

3. **Create Backup** (if --backup=true)
   - Copy file to `.backup/` directory
   - Timestamp the backup file

4. **Replace Text**
   - Use Edit tool with exact string matching
   - Preserve formatting and indentation
   - Maintain file encoding

5. **Verify Changes**
   - Check file syntax is still valid
   - Ensure no unintended changes
   - Generate diff summary

6. **Report Results**
   - Show before/after comparison
   - Display file location and line number
   - Provide backup path if created

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `FILE_NOT_FOUND` | File doesn't exist | Check path, use *find-copy first |
| `TEXT_NOT_FOUND` | old_text not in file | Verify text is exact, check case |
| `MULTIPLE_MATCHES` | Text appears multiple times | Use more specific text or update manually |
| `SYNTAX_ERROR` | Invalid replacement breaks code | Restore from backup, adjust new_text |
| `PERMISSION_DENIED` | Cannot write to file | Check file permissions |

## Safety Features

- ✅ **Exact matching** - Only replaces exact strings
- ✅ **Backups** - Creates timestamped backups
- ✅ **Dry-run mode** - Preview before applying
- ✅ **Syntax validation** - Checks code remains valid
- ✅ **Diff display** - Shows exact changes made

## Output Format

```
✅ Copy updated successfully!

📁 File: frontend/app/buscar/page.tsx
📍 Line: 142

📝 Changes:
  - OLD: "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)"
  + NEW: "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio."

💾 Backup: .backup/page.tsx.2026-02-10_160530.bak

📊 Summary:
  Files updated: 1
  Lines changed: 1
  Characters: 89 → 102 (+13)

✅ Next steps:
  1. *validate-ux to review UX quality
  2. *test-ui-changes to verify rendering
```

## Related Tasks

- `find-copy.md` - Locate text before updating
- `validate-text.md` - Validate text quality
- `validate-ux.md` - Review UX impact
- `test-ui-changes.md` - Test visual changes

## Notes

- Always use *find-copy first to locate all instances
- Consider i18n keys if updating translated content
- Coordinate with @ux-validator for tone approval
- Test changes with @frontend-tester before committing
