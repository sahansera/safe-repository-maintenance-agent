from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from safe_repository_agent.verifier import verify_patch


def git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def create_repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "source"
    repository.mkdir()
    git(repository, "init")
    git(repository, "config", "user.name", "Verifier Test")
    git(repository, "config", "user.email", "verifier@example.test")

    (repository / "fixture").mkdir()
    (repository / "verification").mkdir()
    (repository / "fixture" / "value.txt").write_text("broken\n")
    (repository / "verification" / "fixture.json").write_text(
        json.dumps(
            {
                "workingDirectory": "fixture",
                "protectedPaths": ["verification", "fixture/AGENTS.md"],
                "checks": [
                    {
                        "name": "fixture-value",
                        "command": [
                            sys.executable,
                            "-c",
                            "from pathlib import Path; "
                            "assert Path('value.txt').read_text() == 'fixed\\n'",
                        ],
                        "timeoutSeconds": 10,
                    }
                ],
            }
        )
    )
    (repository / "fixture" / "AGENTS.md").write_text("Run the approved checks.\n")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Create failing fixture")
    return repository, git(repository, "rev-parse", "HEAD").strip()


def export_patch(repository: Path, patch_path: Path, *paths: str) -> None:
    patch_path.write_text(git(repository, "diff", "--binary", "HEAD", "--", *paths))
    git(repository, "restore", ".")


def test_verifier_accepts_patch_that_passes_trusted_check(tmp_path: Path) -> None:
    repository, base_sha = create_repository(tmp_path)
    (repository / "fixture" / "value.txt").write_text("fixed\n")
    patch_path = tmp_path / "candidate.patch"
    export_patch(repository, patch_path, "fixture/value.txt")

    report = verify_patch(
        str(repository), base_sha, patch_path, "verification/fixture.json"
    )

    assert report["passed"] is True
    assert report["changedPaths"] == ["fixture/value.txt"]
    assert report["checks"][0]["passed"] is True


def test_verifier_resolves_relative_local_repository_before_cloning(
    tmp_path: Path,
) -> None:
    repository, base_sha = create_repository(tmp_path)
    (repository / "fixture" / "value.txt").write_text("fixed\n")
    patch_path = tmp_path / "candidate.patch"
    export_patch(repository, patch_path, "fixture/value.txt")

    previous_directory = Path.cwd()
    try:
        os.chdir(tmp_path)
        report = verify_patch(
            "source", base_sha, patch_path, "verification/fixture.json"
        )
    finally:
        os.chdir(previous_directory)

    assert report["passed"] is True


def test_verifier_rejects_patch_when_trusted_check_fails(tmp_path: Path) -> None:
    repository, base_sha = create_repository(tmp_path)
    (repository / "fixture" / "value.txt").write_text("still broken\n")
    patch_path = tmp_path / "candidate.patch"
    export_patch(repository, patch_path, "fixture/value.txt")

    report = verify_patch(
        str(repository), base_sha, patch_path, "verification/fixture.json"
    )

    assert report["passed"] is False
    assert report["error"] == "Check failed: fixture-value"
    assert report["checks"][0]["passed"] is False


def test_verifier_rejects_changes_to_trusted_policy(tmp_path: Path) -> None:
    repository, base_sha = create_repository(tmp_path)
    policy_path = repository / "verification" / "fixture.json"
    policy_path.write_text(policy_path.read_text().replace("fixed", "broken"))
    patch_path = tmp_path / "candidate.patch"
    export_patch(repository, patch_path, "verification/fixture.json")

    report = verify_patch(
        str(repository), base_sha, patch_path, "verification/fixture.json"
    )

    assert report["passed"] is False
    assert report["error"] == "Candidate changes protected paths: verification/fixture.json"
