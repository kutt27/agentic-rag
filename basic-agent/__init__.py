"""
Basic Agentic RAG: a Pydantic AI agent with three tools (list_files, grep, read_file).
The agent picks tools to call iteratively until it has enough context to answer.
No vector database, no embeddings, no chunking. Just an LLM that knows how to grep.
"""

from pydantic_ai import Agent
import nest_asyncio

from build_tools import grep, list_files, read_file

nest_asyncio.apply()

# For OpenAI integration, use this:
# agent = Agent(
#     "openai:gpt-5.5",
#     tools=[list_files, grep, read_file],
#     instructions=(
#         "Search notes with list_files, grep, read_file. Cite files. "
#         "If evidence is missing, say so."
#     ),
# )

# For this project I will be using groq
agent = Agent(
    "groq:llama-3.3-70b-versatile",
    tools=[list_files, grep, read_file],
    instructions=(
        "Search notes with list_files, grep, read_file. Cite files. "
        "If evidence is missing, say so."
    ),
)


if __name__ == "__main__":
    question = "Why does our nightly deploy job run at 03:47 UTC specifically?"

    result = agent.run_sync(question)

    print(f"\nQ: {question}\n")
    print("A:", result.output)
    print(f"\nUsage: {result.usage()}")