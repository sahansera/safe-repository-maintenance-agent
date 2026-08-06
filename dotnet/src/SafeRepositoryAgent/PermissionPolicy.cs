namespace SafeRepositoryAgent;

public enum PolicyDecision
{
    Approve,
    Prompt,
    Deny,
}

public static class PermissionPolicy
{
    public static PolicyDecision Decide(string permissionKind) => permissionKind switch
    {
        "read" => PolicyDecision.Approve,
        "write" or "shell" => PolicyDecision.Prompt,
        "url" or "mcp" => PolicyDecision.Deny,
        _ => PolicyDecision.Deny,
    };
}

