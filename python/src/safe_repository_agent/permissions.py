import asyncio
from typing import Any

from copilot.generated.rpc import PermissionDecisionReject
from copilot.session import PermissionHandler, PermissionRequestResult
from copilot.session_events import PermissionRequest

from safe_repository_agent.policy import PolicyDecision, decide


def _describe(request: PermissionRequest) -> str:
    kind = request.kind
    if kind == "shell":
        return f"Command: {getattr(request, 'full_command_text', '')}"
    if kind == "write":
        return f"File: {getattr(request, 'file_name', '')}\n{getattr(request, 'diff', '')}"
    if kind == "read":
        return f"Read requested: {getattr(request, 'intention', '')}"
    if kind == "url":
        return f"URL: {getattr(request, 'url', '')}"
    if kind == "mcp":
        server = getattr(request, "server_name", "")
        tool = getattr(request, "tool_name", "")
        return f"MCP tool: {server}/{tool}"
    return "No additional request details were supplied."


async def handle_permission(
    request: PermissionRequest,
    context: dict[str, Any],
) -> PermissionRequestResult:
    decision = decide(request.kind)

    print(f"\n[permission: {request.kind}]")
    print(_describe(request))

    if decision is PolicyDecision.APPROVE:
        return PermissionHandler.approve_all(request, context)
    if decision is PolicyDecision.DENY:
        return PermissionDecisionReject(feedback="Blocked by the repository agent policy.")

    answer = (await asyncio.to_thread(input, "Approve once? [y/N] ")).strip().lower()
    if answer == "y":
        return PermissionHandler.approve_all(request, context)
    return PermissionDecisionReject(feedback="The operator denied this action.")

