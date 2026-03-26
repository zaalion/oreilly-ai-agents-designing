from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint="https://dp100psdemo-foundry.services.ai.azure.com/api/projects/proj-default",
    credential=DefaultAzureCredential(),
)

openai = project.get_openai_client()

# Option A: create or update an agent version, then use its returned name
agent = project.agents.create_version(
    agent_name="agent196",
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions="You are a helpful assistant."
    )
)

print(f"Agent created/found: name={agent.name}, version={agent.version}")

conversation = openai.conversations.create()

response = openai.responses.create(
    conversation=conversation.id,
    input="Hi Agent196",
    extra_body={
        "agent_reference": {
            "name": agent.name,
            "type": "agent_reference",
            # optionally include version if needed:
            # "version": agent.version
        }
    }
)

print(response.output_text)