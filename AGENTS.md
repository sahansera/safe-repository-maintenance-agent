# Repository guidance

## Scope

This repository contains equivalent .NET and Python implementations of one permission-gated GitHub
Copilot repository maintenance agent. Keep their observable behavior and permission policy aligned.

## Requirements

- Keep the fixture language-neutral and deliberately failing before an agent repairs it.
- Reads inside the selected working directory may be approved automatically.
- Writes and shell commands must require operator approval.
- URL, MCP, and unknown permission kinds must fail closed.
- Do not grant commit, push, pull-request, or merge authority.
- Do not add secrets, credentials, recorded authentication state, or generated Copilot session data.
- Pin the Agent Framework and GitHub Copilot SDK packages used by the tutorials.

## Validation

Run the .NET and Python policy tests after changing shared behavior. For changes to agent integration,
also exercise each host against a disposable fixture copy and confirm the original fixture remains
failing and unchanged.

