"""
Show Alembic migration history and the database's current revision.

Usage:
    python -m scripts.database.history
"""
import argparse
import sys

from scripts._shared.common import run_module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Show migration history and the current revision.",
    )
    parser.parse_args(argv)

    history_result = run_module("alembic", ["history", "--verbose"])
    current_result = run_module("alembic", ["current"])
    return history_result.returncode or current_result.returncode


if __name__ == "__main__":
    sys.exit(main())
