"""
Roll back Alembic migrations. Destructive to schema (and potentially data)
— requires confirmation unless --yes is passed.

Usage:
    python -m scripts.database.rollback
    python -m scripts.database.rollback --revision base --yes
"""
import argparse
import sys

from scripts._shared.common import confirm, ok, run_module, warn


def downgrade(revision: str = "-1") -> int:
    """Run `alembic downgrade <revision>`. Returns the process return code."""
    result = run_module("alembic", ["downgrade", revision])
    if result.returncode == 0:
        ok(f"Database downgraded to revision '{revision}'.")
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Roll back Alembic migrations (wraps `alembic downgrade`).",
    )
    parser.add_argument(
        "--revision",
        default="-1",
        help="Target revision to roll back to (default: -1, one step back).",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip the confirmation prompt (required for CI/non-interactive use).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    warn("Rolling back migrations can drop columns/tables and lose data.")
    if not confirm(f"Roll back to revision '{args.revision}'?", assume_yes=args.yes):
        warn("Aborted.")
        return 1
    return downgrade(args.revision)


if __name__ == "__main__":
    sys.exit(main())
