"""
The single "is this project healthy" gate: environment prerequisites
(scripts.environment.check), the app import sanity check documented in
CLAUDE.md, and an Alembic current-vs-head comparison. Exits non-zero on
any failure - the intended entry point for a future CI pipeline
(docs/DEVELOPER_PLATFORM.md, Automation Strategy §3.5).

Usage:
    python -m scripts.environment.verify
    python -m scripts.environment.verify --with-tests
"""
import argparse
import sys

from scripts._shared.common import PYTHON, fail, ok, run, run_module, warn
from scripts.environment.check import run_checks


def _check_import_sanity() -> bool:
    result = run([PYTHON, "-c", "import app.main"])
    if result.returncode == 0:
        ok("`import app.main` succeeded.")
        return True
    fail("`import app.main` failed.")
    return False


def _check_migrations_up_to_date() -> bool:
    current = run_module("alembic", ["current"], capture_output=True, text=True)
    heads = run_module("alembic", ["heads"], capture_output=True, text=True)

    current_rev = (current.stdout or "").strip()
    head_rev = (heads.stdout or "").strip().split()[0] if heads.stdout.strip() else ""

    if not current_rev:
        fail("Could not determine the database's current Alembic revision.")
        return False
    if head_rev and head_rev not in current_rev:
        warn("Database is not at the latest migration. Run `python -m scripts.database.migrate`.")
        return False
    ok("Database is at the latest migration.")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the full project health gate: environment, import sanity, migrations, "
        "and optionally the test suite."
    )
    parser.add_argument(
        "--with-tests", action="store_true", help="Also run the full test suite (slower)."
    )
    args = parser.parse_args(argv)

    checks = [
        run_checks(),
        _check_import_sanity(),
        _check_migrations_up_to_date(),
    ]

    if args.with_tests:
        from scripts.quality.test import run_tests

        checks.append(run_tests() == 0)

    if all(checks):
        ok("Project verification passed.")
        return 0
    fail("Project verification failed - see the checks above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
