import os
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Define a model client. You can use other model client that implements
# the `ChatCompletionClient` interface.
model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4o",
    model="gpt-4o",
    api_version="2024-10-21",
    azure_endpoint="https://agentic-or-foundry.openai.azure.com/",
    api_key="[YOUR FOUNDRY API KEY HERE]",
)


# Define a simple function tool that the agent can use.
# For this example, we use a fake weather tool for demonstration purposes.
async def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is 73 degrees and Sunny."


# Agent 1: gets the weather
weather_agent = AssistantAgent(
    name="weather_agent",
    model_client=model_client,
    tools=[get_weather],
    system_message="""
You are a weather assistant.
Your job is to answer weather questions by using the get_weather tool.
After you get the weather, share the result clearly.
""",
    reflect_on_tool_use=True, # After using a tool, the agent sends the tool result back to the model so it can produce a final, natural-language response.
    model_client_stream=True, # Streams the model's response token-by-token instead of waiting for the full response before displaying it.
)


# Agent 2: uses the weather result and gives advice
travel_advisor_agent = AssistantAgent(
    name="travel_advisor_agent",
    model_client=model_client,
    system_message="""
You are a travel advisor.
When the weather agent provides weather information, give practical advice.
Mention what the user should wear or carry.
End your final answer with the word TERMINATE.
""",
    model_client_stream=True,
)


# Stop the conversation when the advisor says TERMINATE
termination = TextMentionTermination("TERMINATE")

# Multi-agent team
team = RoundRobinGroupChat(
    participants=[weather_agent, travel_advisor_agent],
    termination_condition=termination,
    max_turns=4,
)

# Run the agent team and stream the messages to the console.
async def main() -> None:
    await Console(
        team.run_stream(
            task="What is the weather in New York, and what should I wear?"
        )
    )

    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
