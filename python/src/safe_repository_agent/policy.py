from enum import Enum


class PolicyDecision(Enum):
    APPROVE = "approve"
    PROMPT = "prompt"
    DENY = "deny"


def decide(permission_kind: str) -> PolicyDecision:
    if permission_kind == "read":
        return PolicyDecision.APPROVE
    if permission_kind in {"write", "shell"}:
        return PolicyDecision.PROMPT
    return PolicyDecision.DENY

