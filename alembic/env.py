from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.core.database import Base

# Import every ORM model so Base.metadata is fully populated for autogenerate.
# Mirrors the model-import block in app/main.py (kept in sync manually, same
# reason that block exists: SQLAlchemy only knows about a table once its
# model class has been imported).
from app.models.student import Student  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.academic_session import AcademicSession  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.program import Program  # noqa: F401
from app.models.semester import Semester  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.section import Section  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.teacher_assignment import TeacherAssignment  # noqa: F401
from app.models.classroom import Classroom  # noqa: F401
from app.models.timetable import Timetable  # noqa: F401
from app.models.examination import Examination  # noqa: F401
from app.models.exam_mark import ExamMark  # noqa: F401
from app.models.result import Result  # noqa: F401
from app.models.fee_structure import FeeStructure  # noqa: F401
from app.models.fee_payment import FeePayment  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Drive the connection URL from the application's own Settings object
# (app/core/config.py) instead of a static value in alembic.ini, so
# Alembic always targets the same database as the running app.
config.set_main_option("sqlalchemy.url", settings.database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
