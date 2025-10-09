using Azure;
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using System.Diagnostics;

var projectEndpoint = "[ FOUNDRY PORTAL]";
var modelDeploymentName = "gpt-35-turbo";

//Create a PersistentAgentsClient and PersistentAgent.
PersistentAgentsClient client = new(projectEndpoint, new DefaultAzureCredential());

//Give PersistentAgent a tool to execute code using CodeInterpreterToolDefinition.
PersistentAgent agent = client.Administration.CreateAgent(
    model: modelDeploymentName,
    name: "My Test Agent",
    instructions: "You politely help with astronomy questions.",
    tools: [new CodeInterpreterToolDefinition()]
);

//Create a thread to establish a session between Agent and a User.
PersistentAgentThread thread = client.Threads.CreateThread();

//Ask a question of the Agent.
client.Messages.CreateMessage(
    thread.Id,
    MessageRole.User,
    "Hi, Agent! what is Ursa Minor?");

//Have Agent begin processing user's question with some additional instructions associated with the ThreadRun.
ThreadRun run = client.Runs.CreateRun(
    thread.Id,
    agent.Id,
    additionalInstructions: "Please address the user as Jane Doe. The user has a premium account.");

//Poll for completion.
do
{
    Thread.Sleep(TimeSpan.FromMilliseconds(500));
    run = client.Runs.GetRun(thread.Id, run.Id);
}
while (run.Status == RunStatus.Queued
    || run.Status == RunStatus.InProgress
    || run.Status == RunStatus.RequiresAction);

//Get the messages in the PersistentAgentThread. Includes Agent (Assistant Role) and User (User Role) messages.
Pageable<PersistentThreadMessage> messages = client.Messages.GetMessages(
    threadId: thread.Id,
    order: ListSortOrder.Ascending);

//Display each message and open the image generated using CodeInterpreterToolDefinition.
foreach (PersistentThreadMessage threadMessage in messages)
{
    foreach (MessageContent content in threadMessage.ContentItems)
    {
        switch (content)
        {
            case MessageTextContent textItem:
                Console.WriteLine($"[{threadMessage.Role}]: {textItem.Text}");
                break;
            case MessageImageFileContent imageFileContent:
                Console.WriteLine($"[{threadMessage.Role}]: Image content file ID = {imageFileContent.FileId}");
                BinaryData imageContent = client.Files.GetFileContent(imageFileContent.FileId);
                string tempFilePath = Path.Combine(AppContext.BaseDirectory, $"{Guid.NewGuid()}.png");
                File.WriteAllBytes(tempFilePath, imageContent.ToArray());
                client.Files.DeleteFile(imageFileContent.FileId);

                ProcessStartInfo psi = new()
                {
                    FileName = tempFilePath,
                    UseShellExecute = true
                };
                Process.Start(psi);
                break;
        }
    }
}

//If you want to delete your agent, uncomment the following lines:
//client.Threads.DeleteThread(threadId: thread.Id);
//client.Administration.DeleteAgent(agentId: agent.Id);