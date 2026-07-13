"""
Seed the local development database with a baseline admin account and a
minimal set of reference records, so a fresh clone has something to log in
with and explore immediately. Idempotent - safe to run repeatedly.

Reuses the application's own session, models, and password hashing
(app.core.database, app.core.security) rather than issuing raw SQL - this
is real reuse of existing configuration, not a parallel data-access layer.

An admin user is created via a direct ORM insert rather than
`crud.create_user`, because `UserCreate.role` intentionally excludes
`admin` for self-registration (app/schemas/user.py,
docs/05_SECURITY_ARCHITECTURE.md §3) - provisioning the first admin has to
happen out-of-band, and this script is that out-of-band path for local dev.

Usage:
    python -m scripts.database.seed
    python -m scripts.database.seed --admin-email admin@school.local --admin-password ChangeMe123
"""
import argparse
import sys
from datetime import date

from scripts._shared.common import info, ok


def _seed(admin_email: str, admin_password: str) -> None:
    from app.core.database import SessionLocal
    from app.core.roles import Role
    from app.core.security import hash_password
    from app.models.academic_session import AcademicSession
    from app.models.department import Department
    from app.models.program import Program
    from app.models.user import User

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == admin_email).first() is None:
            db.add(
                User(
                    name="Platform Admin",
                    email=admin_email,
                    hashed_password=hash_password(admin_password),
                    role=Role.ADMIN,
                )
            )
            db.commit()
            ok(f"Created admin user '{admin_email}'.")
        else:
            info(f"Admin user '{admin_email}' already exists - skipped.")

        department = db.query(Department).filter(Department.code == "CS").first()
        if department is None:
            department = Department(
                name="Computer Science", code="CS", description="Seeded by scripts.database.seed"
            )
            db.add(department)
            db.commit()
            db.refresh(department)
            ok("Created Department 'Computer Science' (CS).")
        else:
            info("Department 'CS' already exists - skipped.")

        if db.query(AcademicSession).filter(AcademicSession.session_name == "2025-26").first() is None:
            db.add(
                AcademicSession(
                    session_name="2025-26",
                    start_date=date(2025, 7, 1),
                    end_date=date(2026, 6, 30),
                    status="active",
                    is_current=True,
                    description="Seeded by scripts.database.seed",
                )
            )
            db.commit()
            ok("Created AcademicSession '2025-26'.")
        else:
            info("AcademicSession '2025-26' already exists - skipped.")

        if db.query(Program).filter(Program.code == "BTCS").first() is None:
            db.add(
                Program(
                    name="B.Tech Computer Science",
                    code="BTCS",
                    department_id=department.id,
                    description="Seeded by scripts.database.seed",
                )
            )
            db.commit()
            ok("Created Program 'B.Tech Computer Science' (BTCS).")
        else:
            info("Program 'BTCS' already exists - skipped.")
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed the local database with a baseline admin user and reference data. Idempotent.",
    )
    parser.add_argument("--admin-email", default="admin@example.com", help="Email for the seeded admin user.")
    parser.add_argument("--admin-password", default="ChangeMe123", help="Password for the seeded admin user.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _seed(args.admin_email, args.admin_password)
    return 0


if __name__ == "__main__":
    sys.exit(main())
