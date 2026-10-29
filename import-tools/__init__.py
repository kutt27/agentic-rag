"""
Import the finished tools and show what each one returns.

The implementations live in build-tools. In basic-agent, we'll hand these
same three functions to an LLM as tools.
"""

from build_tools import grep, list_files, read_file

print("Files in notes/:")
for f in list_files():
    print(f"  {f}")

print("\nGrep for 'connection pool':")
for hit in grep("connection pool"):
    print(f"  {hit}")

print("\nFirst 200 chars of 04-architecture-decisions.md:")
print(read_file("04-architecture-decisions.md")[:200])