"""
Generate a new Alembic revision from the current model state.

Usage:
    python -m scripts.database.revision -m "Add fee_waiver column"
    python -m scripts.database.revision -m "Manual change" --no-autogenerate
"""
import argparse
import sys

from scripts._shared.common import ok, run_module


def create_revision(message: str, autogenerate: bool = True) -> int:
    """Run `alembic revision [--autogenerate] -m <message>`."""
    args = ["revision", "-m", message]
    if autogenerate:
        args.insert(1, "--autogenerate")
    result = run_module("alembic", args)
    if result.returncode == 0:
        ok(f"Revision created: '{message}'. Review it in alembic/versions/ before applying.")
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a new Alembic migration (wraps `alembic revision`).",
    )
    parser.add_argument("-m", "--message", required=True, help="Description of the migration.")
    parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Create an empty revision instead of diffing models against the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return create_revision(args.message, autogenerate=not args.no_autogenerate)


if __name__ == "__main__":
    sys.exit(main())
