"""
Lint the codebase with ruff (config: pyproject.toml [tool.ruff]).

Usage:
    python -m scripts.quality.lint
    python -m scripts.quality.lint --fix
"""
import argparse
import sys

from scripts._shared.common import run_module

TARGET_PATHS = ["app", "tests", "scripts", "alembic"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint the codebase (wraps `ruff check`).")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations where possible.")
    args = parser.parse_args(argv)

    ruff_args = ["check", *TARGET_PATHS]
    if args.fix:
        ruff_args.append("--fix")

    result = run_module("ruff", ruff_args)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
