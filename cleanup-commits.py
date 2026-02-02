#!/usr/bin/env python3
"""Remove Co-Authored-By and Squad lines from commit messages"""
import re
import sys

def clean_message(commit_message):
    """Clean commit message by removing co-author lines"""
    message = commit_message.decode('utf-8')

    # Remove Co-Authored-By lines (case insensitive)
    message = re.sub(r'^Co-[Aa]uthored-[Bb]y:.*\n?', '', message, flags=re.MULTILINE)

    # Remove Squad lines
    message = re.sub(r'^Squad:.*\n?', '', message, flags=re.MULTILINE)

    # Remove empty lines at the end
    message = message.strip()

    # Ensure single newline at end
    return (message + '\n').encode('utf-8')

if __name__ == '__main__':
    # Read from stdin (git-filter-repo passes message via stdin)
    message = sys.stdin.buffer.read()
    cleaned = clean_message(message)
    sys.stdout.buffer.write(cleaned)
