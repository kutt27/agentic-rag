"""
Structured output: the agent must return a SearchAnswer with citations,
not free-text. Downstream code can rely on the schema.
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
import nest_asyncio

from build_tools import grep, list_files, read_file

nest_asyncio.apply()


class Citation(BaseModel):
    """One source backing a claim in the answer."""

    file: str = Field(
        description="Relative path to the markdown file, e.g. '03-incident-2024-q3.md'"
    )
    quote: str = Field(
        description="The exact line(s) from the file that support the claim"
    )
    line_number: int = Field(description="The line number of the quote")


class SearchAnswer(BaseModel):
    """Structured answer with at least one citation per claim."""

    answer: str = Field(description="The answer in plain English")
    citations: list[Citation] = Field(
        description="Files and quotes that support the answer"
    )


agent = Agent(
    "openai:gpt-5.5",
    tools=[list_files, grep, read_file],
    output_type=SearchAnswer,
    instructions=(
        "Search notes with list_files, grep, read_file. Cite files. "
        "If evidence is missing, say so."
    ),
)


if __name__ == "__main__":
    result = agent.run_sync(
        "Why does our nightly deploy job run at 03:47 UTC specifically?"
    )
    answer = result.output

    print(f"Answer: {answer.answer}")
    print("Citations:")
    for c in answer.citations:
        print(f"  - {c.file}:{c.line_number}")
        print(f"      {c.quote}")