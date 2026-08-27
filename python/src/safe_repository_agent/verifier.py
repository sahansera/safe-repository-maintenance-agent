"""Verify a candidate patch from a clean, trusted repository state."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence


MAX_OUTPUT_CHARS = 8_000


class VerificationError(RuntimeError):
    """Raised when the verifier cannot safely evaluate a candidate."""


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 60,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise VerificationError(f"Command timed out after {timeout}s: {' '.join(command)}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "no output").strip()
        raise VerificationError(f"Command failed: {' '.join(command)}\n{detail}") from error


def _load_policy(workspace: Path, base_sha: str, policy_path: str) -> dict[str, Any]:
    result = _run(
        ["git", "show", f"{base_sha}:{policy_path}"],
        cwd=workspace,
    )
    try:
        policy = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise VerificationError(f"Trusted policy is not valid JSON: {policy_path}") from error

    if not isinstance(policy, dict):
        raise VerificationError("Trusted policy must be a JSON object")
    return policy


def _safe_working_directory(workspace: Path, configured: str) -> Path:
    candidate = (workspace / configured).resolve()
    try:
        candidate.relative_to(workspace.resolve())
    except ValueError as error:
        raise VerificationError("workingDirectory escapes the clean workspace") from error
    if not candidate.is_dir():
        raise VerificationError(f"workingDirectory does not exist: {configured}")
    return candidate


def _validate_policy(policy: dict[str, Any]) -> tuple[str, list[str], list[dict[str, Any]]]:
    working_directory = policy.get("workingDirectory", ".")
    protected_paths = policy.get("protectedPaths", [])
    checks = policy.get("checks", [])

    if not isinstance(working_directory, str):
        raise VerificationError("workingDirectory must be a string")
    if not isinstance(protected_paths, list) or not all(
        isinstance(path, str) and path for path in protected_paths
    ):
        raise VerificationError("protectedPaths must contain non-empty strings")
    if not isinstance(checks, list) or not checks:
        raise VerificationError("checks must contain at least one check")
    if not all(isinstance(check, dict) for check in checks):
        raise VerificationError("Each check must be a JSON object")

    return working_directory, protected_paths, checks


def _touches_protected_path(changed_path: str, protected_paths: list[str]) -> bool:
    normalized = changed_path.rstrip("/")
    return any(
        normalized == protected.rstrip("/")
        or normalized.startswith(f"{protected.rstrip('/')}/")
        for protected in protected_paths
    )


def verify_patch(
    repository: str,
    base_sha: str,
    patch_path: Path,
    policy_path: str,
) -> dict[str, Any]:
    """Apply a patch to a clean base and return a machine-readable report."""
    started = time.monotonic()
    local_repository = Path(repository)
    clone_source = str(local_repository.resolve()) if local_repository.exists() else repository
    report: dict[str, Any] = {
        "repository": repository,
        "baseSha": base_sha,
        "policyPath": policy_path,
        "checks": [],
        "passed": False,
    }

    try:
        patch_bytes = patch_path.read_bytes()
        if not patch_bytes:
            raise VerificationError("Candidate patch is empty")

        with tempfile.TemporaryDirectory(prefix="safe-repo-verifier-") as temp_dir:
            workspace = Path(temp_dir) / "repository"
            _run(
                ["git", "clone", "--no-checkout", clone_source, str(workspace)],
                cwd=Path(temp_dir),
            )
            resolved_base = _run(
                ["git", "rev-parse", "--verify", f"{base_sha}^{{commit}}"],
                cwd=workspace,
            ).stdout.strip()
            report["resolvedBaseSha"] = resolved_base
            _run(["git", "checkout", "--detach", resolved_base], cwd=workspace)

            policy = _load_policy(workspace, resolved_base, policy_path)
            working_directory, protected_paths, checks = _validate_policy(policy)

            candidate_patch = Path(temp_dir) / "candidate.patch"
            candidate_patch.write_bytes(patch_bytes)
            _run(["git", "apply", "--check", str(candidate_patch)], cwd=workspace)
            _run(["git", "apply", str(candidate_patch)], cwd=workspace)

            changed_output = _run(
                ["git", "diff", "--name-only", resolved_base],
                cwd=workspace,
            ).stdout
            changed_paths = [path for path in changed_output.splitlines() if path]
            if not changed_paths:
                raise VerificationError("Candidate patch produced no tracked changes")
            report["changedPaths"] = changed_paths

            protected_changes = [
                path
                for path in changed_paths
                if _touches_protected_path(path, protected_paths)
            ]
            if protected_changes:
                raise VerificationError(
                    "Candidate changes protected paths: " + ", ".join(protected_changes)
                )

            check_cwd = _safe_working_directory(workspace, working_directory)
            for configured_check in checks:
                name = configured_check.get("name")
                command = configured_check.get("command")
                timeout = configured_check.get("timeoutSeconds", 60)
                if not isinstance(name, str) or not name:
                    raise VerificationError("Each check needs a non-empty name")
                if not isinstance(command, list) or not command or not all(
                    isinstance(part, str) and part for part in command
                ):
                    raise VerificationError(f"Check {name} needs a command array")
                if not isinstance(timeout, int) or timeout < 1 or timeout > 600:
                    raise VerificationError(f"Check {name} has an invalid timeoutSeconds")

                completed = _run(command, cwd=check_cwd, timeout=timeout, check=False)
                check_report = {
                    "name": name,
                    "command": command,
                    "exitCode": completed.returncode,
                    "stdout": completed.stdout[-MAX_OUTPUT_CHARS:],
                    "stderr": completed.stderr[-MAX_OUTPUT_CHARS:],
                    "passed": completed.returncode == 0,
                }
                report["checks"].append(check_report)
                if completed.returncode != 0:
                    raise VerificationError(f"Check failed: {name}")

            report["passed"] = True
    except (OSError, VerificationError) as error:
        report["error"] = str(error)

    report["durationSeconds"] = round(time.monotonic() - started, 3)
    return report


def run() -> None:
    parser = argparse.ArgumentParser(
        description="Verify an exact patch from a clean repository base."
    )
    parser.add_argument("repository", help="Git repository URL or local path")
    parser.add_argument("base_sha", help="Trusted base commit SHA")
    parser.add_argument("patch", type=Path, help="Patch exported with git diff --binary")
    parser.add_argument(
        "--policy",
        default="verification/fixture.json",
        help="Policy path read from the trusted base commit",
    )
    args = parser.parse_args()

    report = verify_patch(args.repository, args.base_sha, args.patch, args.policy)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    run()
