# Architecture

Both hosts implement the same protocol:

1. Resolve and validate one repository working directory.
2. Start the GitHub Copilot runtime through Microsoft Agent Framework.
3. Disable ambient configuration discovery.
4. Instruct the agent to read guidance from the selected repository explicitly.
5. Route every requested side effect through host application policy.
6. Stream progress to the operator.
7. Require validation evidence in the final report.
8. Dispose the agent client on success, failure, or cancellation.

The GitHub Copilot harness owns planning, model calls, and tool invocation. Microsoft Agent Framework
provides the agent abstraction, lifecycle, streaming, sessions, middleware, and telemetry surface.
The .NET or Python host remains responsible for authorization and containment.

## Trust boundaries

The selected repository is untrusted input. Its source, instructions, package scripts, tests, and
dependencies can all influence execution. A working directory limits normal tool scope but does not
isolate processes, credentials, or the network.

For untrusted repositories, run each job inside a disposable container or microVM with:

- A non-root user
- Bounded CPU, memory, disk, subprocesses, and wall-clock time
- No ambient cloud or developer credentials
- Short-lived, repository-scoped credentials when source-control access is required
- Network access denied by default
- A disposable writable workspace
- An audit record of requests, decisions, commands, diffs, and validation results

The tutorial stops at a reviewable, validated patch. It does not commit, push, open a pull request, or
merge changes.

