"""
Streaming the agent's intermediate steps with agent.iter().
This is where 'agentic' becomes visible. Every grep, every read, printed live.
"""

import asyncio

import nest_asyncio
from pydantic_ai import Agent
from pydantic_ai.messages import FunctionToolCallEvent, FunctionToolResultEvent

from build_tools import grep, list_files, read_file

nest_asyncio.apply()


async def format_tool_result(event: FunctionToolResultEvent, tool_names: dict[str, str]) -> str:
    name = tool_names.get(event.tool_call_id, "unknown")
    result = event.part.content
    text = result if isinstance(result, str) else str(result)
    return f"<- {name}() = {text[:100]}..."


agent = Agent(
    "openai:gpt-5.5",
    tools=[list_files, grep, read_file],
    instructions=(
        "Search notes with list_files, grep, read_file. Cite files. "
        "If evidence is missing, say so."
    ),
)


async def run_with_visible_steps(question: str, debug: bool = False) -> str:
    print(f"\nQ: {question}\n")
    print("--- agent steps ---")
    tool_names: dict[str, str] = {}

    async with agent.iter(question) as run:
        async for node in run:
            if Agent.is_call_tools_node(node):
                async with node.stream(run.ctx) as tool_stream:
                    async for event in tool_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            tool_names[event.tool_call_id] = event.part.tool_name
                            print(
                                f"-> {event.part.tool_name}({event.part.args_as_json_str()})"
                            )
                        elif debug and isinstance(event, FunctionToolResultEvent):
                            print(await format_tool_result(event, tool_names))

    print("--- done ---\n")
    return run.result.output


if __name__ == "__main__":
    answer = asyncio.run(
        run_with_visible_steps(
            "Why does our nightly deploy job run at 03:47 UTC specifically?",
            debug=False,
        )
    )
    print("A:", answer)