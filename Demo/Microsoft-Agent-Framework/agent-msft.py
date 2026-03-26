import asyncio

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

credential = AzureCliCredential()
client = AzureOpenAIResponsesClient(
    project_endpoint="https://dp100psdemo-foundry.services.ai.azure.com/api/projects/proj-default",
    deployment_name="gpt-4o-mini",
    credential=credential,
)

agent = client.as_agent(
    name="HelloAgent",
    instructions="You are a friendly assistant. Keep your answers brief.",
)

async def main():
    result = await agent.run("What is the largest city in France?")
    print(f"Agent: {result}")

asyncio.run(main())