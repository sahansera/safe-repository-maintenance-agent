using GitHub.Copilot;
using GitHub.Copilot.Rpc;

namespace SafeRepositoryAgent;

public static class ConsolePermissionHandler
{
    public static Task<PermissionDecision> HandleAsync(
        PermissionRequest request,
        PermissionInvocation _)
    {
        PolicyDecision decision = PermissionPolicy.Decide(request.Kind);

        Console.WriteLine($"\n[permission: {request.Kind}]");
        Console.WriteLine(Describe(request));

        return decision switch
        {
            PolicyDecision.Approve => Task.FromResult(PermissionDecision.ApproveOnce()),
            PolicyDecision.Deny => Task.FromResult(
                PermissionDecision.Reject("Blocked by the repository agent policy.")),
            _ => Task.FromResult(Prompt()),
        };
    }

    private static PermissionDecision Prompt()
    {
        Console.Write("Approve once? [y/N] ");
        string? answer = Console.ReadLine()?.Trim();

        return answer is not null && answer.Equals("y", StringComparison.OrdinalIgnoreCase)
            ? PermissionDecision.ApproveOnce()
            : PermissionDecision.Reject("The operator denied this action.");
    }

    private static string Describe(PermissionRequest request) => request switch
    {
        PermissionRequestShell shell => $"Command: {shell.FullCommandText}",
        PermissionRequestWrite write => $"File: {write.FileName}\n{write.Diff}",
        PermissionRequestRead read => $"Read requested: {read.Intention}",
        PermissionRequestUrl url => $"URL: {url.Url}",
        PermissionRequestMcp mcp => $"MCP tool: {mcp.ServerName}/{mcp.ToolName}",
        _ => "No additional request details were supplied.",
    };
}

