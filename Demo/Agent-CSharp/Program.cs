// dotnet add package Azure.AI.Projects --version 2.0.0-beta.2
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Azure.AI.Extensions.OpenAI;
using Azure.Identity;
using OpenAI.Responses;

#pragma warning disable OPENAI001

const string endpoint = "https://agentic-or-foundry.services.ai.azure.com/api/projects/proj-default";
const string agentName = "agent01";
const string agentVersion = "3";

// Connect to your project using the endpoint from your project page
// The AzureCliCredential will use your logged-in Azure CLI identity, make sure to run `az login` first
AIProjectClient projectClient = new(endpoint: new Uri(endpoint), tokenProvider: new DefaultAzureCredential());

AgentReference agentReference = new(name: agentName, version: agentVersion);
ProjectResponsesClient responseClient = projectClient.OpenAI.GetProjectResponsesClientForAgent(agentReference);
// Use the agent to generate a response
ResponseResult response = responseClient.CreateResponse(
    "Hello! Tell me a joke."
);

Console.WriteLine(response.GetOutputText());