"""
Print a snapshot of the current project/environment state: app identity,
interpreter, database target (host/port/name only — never credentials),
current Alembic revision, and git branch (best-effort, read-only).

Usage:
    python -m scripts.development.info
"""
import argparse
import platform
import subprocess
import sys

from scripts._shared.common import PROJECT_ROOT, run_module


def _current_alembic_revision() -> str:
    result = run_module(
        "alembic", ["current"], capture_output=True, text=True
    )
    output = (result.stdout or "").strip()
    return output or "(unavailable — is the database reachable?)"


def _current_git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or "(unavailable)"
    except FileNotFoundError:
        return "(git not installed)"


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Show project/environment info.").parse_args(argv)

    from app.core.config import settings

    print("EduCore SMS - Project Info")
    print("-" * 40)
    print(f"App name:        {settings.app_name}")
    print(f"App version:     {settings.app_version}")
    print(f"Python:          {platform.python_version()} ({sys.executable})")
    print(f"Platform:        {platform.system()} {platform.release()}")
    print(f"Database host:   {settings.database_host}:{settings.database_port}")
    print(f"Database name:   {settings.database_name}")
    print(f"Git branch:      {_current_git_branch()}")
    print(f"Alembic status:  {_current_alembic_revision()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
