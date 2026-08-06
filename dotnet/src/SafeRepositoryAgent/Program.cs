using GitHub.Copilot;
using Microsoft.Agents.AI;
using SafeRepositoryAgent;

const string instructions = """
    You are a repository maintenance agent. Work only inside the supplied working directory.
    Read AGENTS.md before making changes. Make the smallest change that satisfies the task.
    Do not access the network, install packages, commit, push, or create a pull request.
    Run the repository's focused validation and finish with a concise report containing the files
    changed, commands run, and validation result.
    """;

const string defaultTask = """
    First read AGENTS.md. Then fix the failing normalizeTitle behavior described by the tests.
    Inspect the repository, make the smallest coherent change, run the focused test command, and
    report the result.
    """;

if (args.Length == 0)
{
    Console.Error.WriteLine("Usage: dotnet run -- <repository-path> [task]");
    return 2;
}

string repositoryPath = Path.GetFullPath(args[0]);
if (!Directory.Exists(repositoryPath))
{
    Console.Error.WriteLine($"Repository directory does not exist: {repositoryPath}");
    return 2;
}

string task = args.Length > 1 ? string.Join(' ', args.Skip(1)) : defaultTask;

await using CopilotClient copilotClient = new(new CopilotClientOptions
{
    WorkingDirectory = repositoryPath,
});
await copilotClient.StartAsync();

SessionConfig sessionConfig = new()
{
    WorkingDirectory = repositoryPath,
    EnableConfigDiscovery = false,
    OnPermissionRequest = ConsolePermissionHandler.HandleAsync,
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Append,
        Content = instructions,
    },
};

AIAgent agent = copilotClient.AsAIAgent(sessionConfig);

Console.WriteLine($"Repository: {repositoryPath}");
Console.WriteLine($"Task: {task}\n");

await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(task))
{
    Console.Write(update);
}

Console.WriteLine();
return 0;
