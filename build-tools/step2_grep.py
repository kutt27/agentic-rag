"""
Step 2: grep - find lines matching a pattern across all files.
"""

import re # regular expression module
from pathlib import Path

NOTES_DIR = (Path(__file__).parent.parent / "notes").resolve()

print("\n1. Compile a case-insensitive regex:")
pattern: str = "connection pool"
rx = re.compile(pattern, re.IGNORECASE)
print(rx)

r = rx.search("This strings contains connection pool")
if r:
    print("Found a match!")
r = rx.search("This strings does not contain our regex pattern")
if not r:
    print("No match found!")

print("\n2. Search one file line by line:")
file = NOTES_DIR / "02-billing-runbook.md"
text = file.read_text()
lines = text.splitlines()
one_file_hits = []

for i, line in enumerate(lines, start=1):
    if rx.search(line):
        rel = file.relative_to(NOTES_DIR)
        one_file_hits.append(f"{rel}:{i}: {line.strip()}")

print(one_file_hits)

print("\n3. Search every markdown file:")


def grep(pattern: str, max_results: int = 30) -> list[str]:
    """Search markdown files for matching lines."""
    rx = re.compile(pattern, re.IGNORECASE)
    hits: list[str] = []
    for file in sorted(NOTES_DIR.rglob("*.md")):
        for i, line in enumerate(file.read_text().splitlines(), start=1):
            if rx.search(line):
                rel = file.relative_to(NOTES_DIR)
                hits.append(f"{rel}:{i}: {line.strip()}")
                if len(hits) >= max_results:
                    return hits
    return hits


if __name__ == "__main__":
    print("\ngrep('connection pool'):")
    print(grep("connection pool"))