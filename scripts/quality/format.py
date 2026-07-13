"""
Format the codebase with ruff format.

Usage:
    python -m scripts.quality.format
    python -m scripts.quality.format --check
"""
import argparse
import sys

from scripts._shared.common import run_module

TARGET_PATHS = ["app", "tests", "scripts", "alembic"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format the codebase (wraps `ruff format`).")
    parser.add_argument(
        "--check", action="store_true", help="Report what would change without writing files (CI-friendly)."
    )
    args = parser.parse_args(argv)

    ruff_args = ["format", *TARGET_PATHS]
    if args.check:
        ruff_args.append("--check")

    result = run_module("ruff", ruff_args)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
