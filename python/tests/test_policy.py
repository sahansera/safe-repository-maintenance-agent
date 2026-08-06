import pytest

from safe_repository_agent.policy import PolicyDecision, decide


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("read", PolicyDecision.APPROVE),
        ("write", PolicyDecision.PROMPT),
        ("shell", PolicyDecision.PROMPT),
        ("url", PolicyDecision.DENY),
        ("mcp", PolicyDecision.DENY),
        ("unknown", PolicyDecision.DENY),
    ],
)
def test_decide_returns_expected_decision(kind: str, expected: PolicyDecision) -> None:
    assert decide(kind) is expected

