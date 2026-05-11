"""
Step 1: list_files - discover what's in the notes folder.
"""

from pathlib import Path

NOTES_DIR = (Path(__file__).parent.parent / "notes").resolve()

print("\n1. Start from the notes directory:")
print(NOTES_DIR)

print("\n2. Find markdown files:")
paths = sorted(NOTES_DIR.glob("*.md"))
print(paths[:4]) # print the first 4 of them

print("\n3. Return paths relative to notes/:")
relative_paths = [str(path.relative_to(NOTES_DIR)) for path in paths]
print(relative_paths[:4]) # relative notes ("/notes")


def list_files(pattern: str = "*.md") -> list[str]:
    """List markdown files in notes/ matching a glob pattern."""
    return sorted(str(path.relative_to(NOTES_DIR)) for path in NOTES_DIR.glob(pattern))


if __name__ == "__main__":
    print("\nlist_files():")
    print(list_files())