using SafeRepositoryAgent;
using Xunit;

namespace SafeRepositoryAgent.Tests;

public sealed class PermissionPolicyTests
{
    [Theory]
    [InlineData("read", PolicyDecision.Approve)]
    [InlineData("write", PolicyDecision.Prompt)]
    [InlineData("shell", PolicyDecision.Prompt)]
    [InlineData("url", PolicyDecision.Deny)]
    [InlineData("mcp", PolicyDecision.Deny)]
    [InlineData("unknown", PolicyDecision.Deny)]
    public void DecideReturnsExpectedDecision(string kind, PolicyDecision expected)
    {
        Assert.Equal(expected, PermissionPolicy.Decide(kind));
    }
}
