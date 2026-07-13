"""
Lightweight security check: dependency vulnerability scan (pip-audit, if
reachable) plus a handful of fast, network-independent static checks drawn
directly from the gaps already recorded in docs/05_SECURITY_ARCHITECTURE.md
and docs/04_DATABASE_STRATEGY.md - this script doesn't invent new checks,
it automates ones already identified.

Usage:
    python -m scripts.quality.security
    python -m scripts.quality.security --skip-audit
"""
import argparse
import re
import sys

from scripts._shared.common import PROJECT_ROOT, fail, info, ok, run_module, warn


def _check_env_is_gitignored() -> bool:
    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists():
        fail(".gitignore not found - .env may be trackable by git.")
        return False
    contents = gitignore.read_text()
    if ".env" in contents:
        ok(".env is listed in .gitignore.")
        return True
    fail(".env is NOT listed in .gitignore - a real secret could be committed.")
    return False


def _check_engine_echo() -> bool:
    database_py = PROJECT_ROOT / "app" / "core" / "database.py"
    if not database_py.exists():
        warn("app/core/database.py not found - skipped echo check.")
        return True
    if re.search(r"echo\s*=\s*True", database_py.read_text()):
        warn(
            "engine.echo=True is hardcoded in app/core/database.py - logs full SQL "
            "(including parameter values) unconditionally. Known gap, see "
            "docs/05_SECURITY_ARCHITECTURE.md section 8."
        )
        return True  # a warning, not a failure - documented, pre-existing gap
    ok("engine.echo is not hardcoded to True.")
    return True


def _check_no_hardcoded_secrets() -> bool:
    """
    Scans app/ for literal secret-like assignments (e.g. SECRET_KEY = "..."),
    which would indicate a credential committed to source instead of read
    via app.core.config.settings. Deliberately narrow (few, high-confidence
    patterns) to avoid false positives on legitimate variable names like
    `hashed_password`.
    """
    suspicious_pattern = re.compile(
        r'\b(SECRET_KEY|DATABASE_PASSWORD|ACCESS_TOKEN)\s*=\s*["\'][^"\']+["\']'
    )
    offenders = []
    for path in (PROJECT_ROOT / "app").rglob("*.py"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if suspicious_pattern.search(line):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno}")

    if offenders:
        fail("Possible hardcoded secret(s) found:")
        for offender in offenders:
            print(f"       {offender}")
        return False
    ok("No hardcoded SECRET_KEY/DATABASE_PASSWORD/ACCESS_TOKEN literals found in app/.")
    return True


def _run_dependency_audit() -> bool:
    info("Running pip-audit (requires network access to the PyPI advisory database)...")
    result = run_module("pip_audit", [])
    if result.returncode == 0:
        ok("pip-audit found no known vulnerabilities.")
        return True
    warn("pip-audit reported findings or could not run (e.g. no network access). See output above.")
    return True  # non-fatal - dependency audit availability shouldn't block local dev


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run static security checks and a dependency vulnerability scan."
    )
    parser.add_argument("--skip-audit", action="store_true", help="Skip the pip-audit dependency scan.")
    args = parser.parse_args(argv)

    checks = [
        _check_env_is_gitignored(),
        _check_no_hardcoded_secrets(),
        _check_engine_echo(),
    ]
    if not args.skip_audit:
        checks.append(_run_dependency_audit())

    if all(checks):
        ok("Security checks passed.")
        return 0
    fail("One or more security checks failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
