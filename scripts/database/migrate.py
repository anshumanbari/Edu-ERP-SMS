"""
Apply Alembic migrations up to a target revision (default: head).

Usage:
    python -m scripts.database.migrate
    python -m scripts.database.migrate --revision <revision_id>
"""
import argparse
import sys

from scripts._shared.common import ok, run_module


def upgrade(revision: str = "head") -> int:
    """Run `alembic upgrade <revision>`. Returns the process return code."""
    result = run_module("alembic", ["upgrade", revision])
    if result.returncode == 0:
        ok(f"Database upgraded to revision '{revision}'.")
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply Alembic migrations (wraps `alembic upgrade`).",
    )
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision to migrate to (default: head).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return upgrade(args.revision)


if __name__ == "__main__":
    sys.exit(main())
