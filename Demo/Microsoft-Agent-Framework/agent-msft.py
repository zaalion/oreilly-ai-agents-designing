# py -m pip install agent-framework-foundry azure-identity

import asyncio

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


async def main() -> None:
    # This is your Azure AI Foundry project endpoint.
    # It usually looks like:
    # https://<your-foundry-resource>.services.ai.azure.com/api/projects/<project-name>
    client = FoundryChatClient(
        project_endpoint="https://agentic-or-foundry.services.ai.azure.com/api/projects/proj-default",
        model="gpt-4o",  # Your deployed model name/deployment name in Foundry
        credential=AzureCliCredential(),
    )

    agent = Agent(
        client=client,
        name="HelloAgent",
        instructions="You are a helpful Azure AI assistant. Keep answers clear and brief.",
    )

    # Non-streaming response
    result = await agent.run("Explain Microsoft Agent Framework in two sentences.")
    print(f"\nAgent:\n{result}\n")

    # Streaming response
    print("Agent streaming: ", end="", flush=True)

    async for chunk in agent.run(
        "Give me one practical use case for Microsoft Agent Framework.",
        stream=True,
    ):
        if chunk.text:
            print(chunk.text, end="", flush=True)

    print()


if __name__ == "__main__":
    asyncio.run(main())