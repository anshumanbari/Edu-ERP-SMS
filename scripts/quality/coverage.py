"""
Run the test suite and report where the coverage output landed. Coverage
collection itself is already configured in tests/pytest.ini (--cov=app),
so this reuses scripts.quality.test.run_tests rather than re-implementing
the pytest invocation — it only adds the report-location message and the
optional browser open.

Usage:
    python -m scripts.quality.coverage
    python -m scripts.quality.coverage --open
"""
import argparse
import sys
import webbrowser

from scripts._shared.common import PROJECT_ROOT, info, ok
from scripts.quality.test import run_tests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the test suite and report coverage.")
    parser.add_argument(
        "--open", action="store_true", help="Open the HTML coverage report in a browser afterward."
    )
    args = parser.parse_args(argv)

    returncode = run_tests()

    report_path = PROJECT_ROOT / "htmlcov" / "index.html"
    if report_path.exists():
        ok(f"Coverage report: {report_path}")
        if args.open:
            webbrowser.open(report_path.as_uri())
    else:
        info("No coverage report was generated.")

    return returncode


if __name__ == "__main__":
    sys.exit(main())
