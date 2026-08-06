# Permission model

The two hosts share this policy:

| Permission kind | Decision | Reason |
| --- | --- | --- |
| `read` | Approve once | Required to inspect the selected repository |
| `write` | Ask | The operator must inspect the path and proposed diff |
| `shell` | Ask | The operator must inspect the complete command |
| `url` | Deny | The sample does not require network access |
| `mcp` | Deny | The sample does not require external tools or data |
| Unknown | Deny | New capabilities must be authorized deliberately |

Prompt instructions do not grant authority. They tell the agent what behavior is expected, while the
permission callback enforces which side effects are possible.

The console prompt is suitable for a local tutorial. A service should persist approval requests and
bind each decision to an authenticated operator, job identity, tool call, proposed action, and expiry.
Approval should resume only the exact paused action rather than granting standing session authority.

## Testing

Each language keeps the deterministic policy separate from Copilot types. This allows every branch to
be tested without a model request or subscription. End-to-end tests then verify that Copilot requests
are routed through the policy and that the permitted repair produces passing fixture tests.

