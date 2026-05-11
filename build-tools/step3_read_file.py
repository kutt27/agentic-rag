"""
Step 3: read_file - pull the full body of one file.
"""

from pathlib import Path

NOTES_DIR = (Path(__file__).parent.parent / "notes").resolve()

print("\n1. Resolve the requested path:")
requested = "04-architecture-decisions.md"
target = (NOTES_DIR / requested).resolve()
print(target)

print("\n2. Check that it stayed inside notes/:")
print(target.is_relative_to(NOTES_DIR))

print("\n3. Read the text:")
print(target.read_text()[:200])


def read_file(path: str) -> str:
    """Read one markdown file by relative path."""
    target = (NOTES_DIR / path).resolve()
    if not target.is_relative_to(NOTES_DIR):
        raise ValueError(f"Path {path} is outside the notes directory")
    return target.read_text()


if __name__ == "__main__":
    print("\nread_file('04-architecture-decisions.md')[:200]:")
    print(read_file("04-architecture-decisions.md")[:200])