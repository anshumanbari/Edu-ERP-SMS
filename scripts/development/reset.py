"""
Reset the local development database to a clean, fully-migrated state:
downgrade to base, then upgrade back to head. Destructive - drops all data
 -  requires confirmation unless --yes is passed.

Reuses scripts.database.rollback.downgrade / scripts.database.migrate.upgrade
rather than re-invoking alembic directly, so there is exactly one place
that knows how to run a migration.

Usage:
    python -m scripts.development.reset
    python -m scripts.development.reset --yes --seed
"""
import argparse
import sys

from scripts._shared.common import confirm, fail, ok, warn
from scripts.database.migrate import upgrade
from scripts.database.rollback import downgrade


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset the local database: downgrade to base, then upgrade to head."
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip the confirmation prompt.")
    parser.add_argument(
        "--seed", action="store_true", help="Run scripts.database.seed after the reset completes."
    )
    args = parser.parse_args(argv)

    warn("This drops every table in the database and rebuilds the schema from scratch.")
    if not confirm("Reset the local database?", assume_yes=args.yes):
        warn("Aborted.")
        return 1

    if downgrade("base") != 0:
        fail("Downgrade to base failed - aborting reset.")
        return 1
    if upgrade("head") != 0:
        fail("Upgrade to head failed after downgrade - database may be in an inconsistent state.")
        return 1

    ok("Database reset to a clean, fully-migrated state.")

    if args.seed:
        from scripts.database.seed import _seed

        _seed(admin_email="admin@example.com", admin_password="ChangeMe123")

    return 0


if __name__ == "__main__":
    sys.exit(main())
