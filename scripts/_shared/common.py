"""
Shared support code for every script under scripts/ — not a category of
its own (see docs/DEVELOPER_PLATFORM.md), just the one place subprocess
running, console output, and project-path resolution live so no individual
script re-implements them.

Every script is expected to be invoked with the project's own venv
interpreter (the same convention CLAUDE.md's Commands section already
uses, e.g. `./.venv/Scripts/python.exe scripts/development/start.py`) —
that interpreter is `sys.executable`, which is why PYTHON below is just
that, not a hunted-for venv path. This is also what makes these scripts
work unmodified inside a future Docker image or CI runner: whichever
Python invokes the script is the one used for every subprocess.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON = sys.executable


def info(message: str) -> None:
    print(f"[INFO] {message}")


def ok(message: str) -> None:
    print(f"[OK]   {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """
    Run a command from the project root, streaming output live (no
    capture) so it behaves the same interactively and in CI/Docker logs.
    Returns the CompletedProcess — callers decide how to react to a
    non-zero return code, this never raises on its own.
    """
    info("Running: " + " ".join(cmd))
    kwargs.setdefault("cwd", PROJECT_ROOT)
    return subprocess.run(cmd, **kwargs)


def run_module(module: str, args: list[str] | None = None, **kwargs) -> subprocess.CompletedProcess:
    """Run `<venv python> -m <module> <args>` — the standard shape for
    invoking alembic/pytest/ruff/uvicorn/pip the same way CLAUDE.md's
    documented commands already do."""
    return run([PYTHON, "-m", module, *(args or [])], **kwargs)


def confirm(prompt: str, assume_yes: bool = False) -> bool:
    """
    Interactive confirmation for destructive actions. `assume_yes` is how
    every script's `--yes`/`-y` flag skips the prompt for non-interactive
    use (CI, Docker, scripted calls) — never block automation on stdin.
    """
    if assume_yes:
        return True
    reply = input(f"{prompt} [y/N]: ").strip().lower()
    return reply in ("y", "yes")
