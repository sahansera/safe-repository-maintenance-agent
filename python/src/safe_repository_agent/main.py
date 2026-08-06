import argparse
import asyncio
from pathlib import Path

from agent_framework.github import GitHubCopilotAgent, GitHubCopilotOptions

from safe_repository_agent.permissions import handle_permission


INSTRUCTIONS = """
You are a repository maintenance agent. Work only inside the supplied working directory.
Read AGENTS.md before making changes. Make the smallest change that satisfies the task.
Do not access the network, install packages, commit, push, or create a pull request.
Run the repository's focused validation and finish with a concise report containing the files
changed, commands run, and validation result.
""".strip()

DEFAULT_TASK = """
First read AGENTS.md. Then fix the failing normalizeTitle behavior described by the tests.
Inspect the repository, make the smallest coherent change, run the focused test command, and
report the result.
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe repository maintenance agent.")
    parser.add_argument("repository", type=Path, help="Repository working directory")
    parser.add_argument("task", nargs="?", default=DEFAULT_TASK, help="Maintenance task")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    repository = args.repository.expanduser().resolve(strict=True)
    if not repository.is_dir():
        raise NotADirectoryError(repository)

    options = GitHubCopilotOptions(
        working_directory=str(repository),
        enable_config_discovery=False,
        on_permission_request=handle_permission,
    )
    agent: GitHubCopilotAgent[GitHubCopilotOptions] = GitHubCopilotAgent(
        instructions=INSTRUCTIONS,
        default_options=options,
    )

    print(f"Repository: {repository}")
    print(f"Task: {args.task}\n")

    async with agent:
        async for update in agent.run(args.task, stream=True):
            print(update.text, end="", flush=True)

    print()
    return 0


def run() -> None:
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    run()
