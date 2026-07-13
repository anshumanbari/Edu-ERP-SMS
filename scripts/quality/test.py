"""
Run the test suite (wraps `pytest -c tests/pytest.ini`, the exact
invocation documented in tests/README.md).

Usage:
    python -m scripts.quality.test
    python -m scripts.quality.test --unit
    python -m scripts.quality.test --integration
    python -m scripts.quality.test -- -k test_login
"""
import argparse
import sys

from scripts._shared.common import run_module


def run_tests(marker: str | None = None, extra_args: list[str] | None = None) -> int:
    """Run pytest against tests/pytest.ini. Returns the process return code."""
    args = ["-c", "tests/pytest.ini"]
    if marker:
        args += ["-m", marker]
    args += extra_args or []
    result = run_module("pytest", args)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the test suite.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unit", action="store_true", help="Run only tests marked 'unit'.")
    group.add_argument("--integration", action="store_true", help="Run only tests marked 'integration'.")
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments forwarded to pytest as-is (e.g. -- -k test_login).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    marker = "unit" if args.unit else "integration" if args.integration else None
    extra = [a for a in args.pytest_args if a != "--"]
    return run_tests(marker=marker, extra_args=extra)


if __name__ == "__main__":
    sys.exit(main())
