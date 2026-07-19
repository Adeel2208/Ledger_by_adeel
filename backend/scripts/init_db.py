"""Create all tables from the ORM metadata.

Dev convenience (SQLite). For prod migrations use Alembic (`alembic upgrade head`).

Run:  python scripts/init_db.py
"""
from __future__ import annotations

from app.database import Base, engine
from app import models  # noqa: F401  (imports register every table on Base.metadata)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Created tables:", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    main()
