#!/usr/bin/env python3
"""Clean Co-Authored-By lines from markdown files"""
import re
from pathlib import Path

def clean_markdown_file(filepath):
    """Remove Co-Authored-By and Squad lines from a markdown file"""
    try:
        content = filepath.read_text(encoding='utf-8')

        # Remove Co-Authored-By lines (case insensitive)
        content = re.sub(r'^Co-[Aa]uthored-[Bb]y:.*\n?', '', content, flags=re.MULTILINE)

        # Remove Squad lines
        content = re.sub(r'^Squad:.*\n?', '', content, flags=re.MULTILINE)

        # Write back
        filepath.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Clean all markdown files in the repository"""
    base_path = Path('.')
    cleaned_count = 0

    for md_file in base_path.rglob('*.md'):
        # Skip node_modules and other ignored directories
        if any(part in md_file.parts for part in ['node_modules', '.next', 'dist', 'build', '.git']):
            continue

        if clean_markdown_file(md_file):
            cleaned_count += 1
            print(f"OK Cleaned: {md_file}")

    print(f"\nCleaned {cleaned_count} markdown files")

if __name__ == '__main__':
    main()
