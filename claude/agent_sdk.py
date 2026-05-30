import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, query


async def main():
    async for message in query(
        prompt="Review buggy.py for bugs that would crash the program, fix issue you find, after done, try running the program and report any errors you find.",  # noqa: E501
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob", "Bash"],
            permission_mode="acceptEdits",
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)  # noqa: T201
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")  # noqa: T201
        elif isinstance(message, ResultMessage):
            print(f"Done : {message.subtype} - {message.result}")  # noqa: T201


asyncio.run(main())
