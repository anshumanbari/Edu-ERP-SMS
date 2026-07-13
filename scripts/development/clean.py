"""
Remove generated/cache artifacts: __pycache__ directories, .pytest_cache,
.ruff_cache, .mypy_cache, htmlcov/, and the .coverage data file. Never
touches .venv, .git, or any source file.

Usage:
    python -m scripts.development.clean
"""
import argparse
import shutil
import sys

from scripts._shared.common import PROJECT_ROOT, info, ok

DIR_NAMES_TO_REMOVE = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "htmlcov"}
FILE_NAMES_TO_REMOVE = {".coverage"}
SKIP_DIR_NAMES = {".venv", ".git"}


def clean() -> int:
    removed = 0
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_dir() and path.name in DIR_NAMES_TO_REMOVE:
            shutil.rmtree(path, ignore_errors=True)
            info(f"Removed {path.relative_to(PROJECT_ROOT)}")
            removed += 1
        elif path.is_file() and path.name in FILE_NAMES_TO_REMOVE:
            path.unlink(missing_ok=True)
            info(f"Removed {path.relative_to(PROJECT_ROOT)}")
            removed += 1

    ok(f"Cleaned {removed} artifact(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(
        description="Remove __pycache__, test/lint/coverage caches, and coverage reports."
    ).parse_args(argv)
    return clean()


if __name__ == "__main__":
    sys.exit(main())
