"""Add founder profile columns to an existing database.

`create_all` only creates missing *tables*, never missing columns, so an
existing vcbrain.db needs this one-off. Safe to run repeatedly: each column is
added only if absent.

Run:  python scripts/migrate_founder_profile.py
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from app.database import engine

# SQLite's ALTER TABLE ADD COLUMN accepts these types directly; Postgres reads
# JSON/TEXT/VARCHAR identically, so the same DDL works on both.
_COLUMNS = {
    "photo_path": "VARCHAR(300)",
    "headline": "VARCHAR(160)",
    "bio": "TEXT",
    "role": "VARCHAR(120)",
    "location": "VARCHAR(160)",
    "personal_url": "VARCHAR(300)",
    "twitter_handle": "VARCHAR(100)",
    "work_history": "JSON",
    "profile_updated_at": "TIMESTAMP",
}


def main() -> None:
    existing = {c["name"] for c in inspect(engine).get_columns("founders")}
    added = []
    with engine.begin() as conn:
        for name, ddl_type in _COLUMNS.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE founders ADD COLUMN {name} {ddl_type}"))
            added.append(name)

    print(f"Added {len(added)} column(s): {', '.join(added) if added else '(already up to date)'}")


if __name__ == "__main__":
    main()
