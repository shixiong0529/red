from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import models
from app.db import Base


MODEL_ORDER = [
    models.User,
    models.Profile,
    models.Session,
    models.ChatMessage,
    models.GuestbookPost,
    models.GuestbookReply,
    models.UserRoom,
]


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _copy_table(src: Session, dst: Session, model) -> int:
    rows = src.execute(select(model)).scalars().all()
    copied = 0
    for row in rows:
        data = {column.name: getattr(row, column.name) for column in model.__table__.columns}
        dst.merge(model(**data))
        copied += 1
    dst.commit()
    return copied


def _reset_postgres_sequences(dst: Session) -> None:
    for model in MODEL_ORDER:
        table_name = model.__table__.name
        pk_columns = list(model.__table__.primary_key.columns)
        if len(pk_columns) != 1:
            continue
        pk_name = pk_columns[0].name
        dst.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', '{pk_name}'),
                    COALESCE((SELECT MAX({pk_name}) FROM {table_name}), 1),
                    COALESCE((SELECT MAX({pk_name}) FROM {table_name}), 0) > 0
                )
                """
            )
        )
    dst.commit()


def main() -> None:
    sqlite_path = os.getenv("SQLITE_PATH", "./red_dragonfly.db")
    postgres_url = os.getenv("POSTGRES_URL")

    if not postgres_url:
        raise SystemExit("Missing POSTGRES_URL environment variable.")

    sqlite_file = Path(sqlite_path)
    if not sqlite_file.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_file}")

    sqlite_url = f"sqlite:///{sqlite_file.resolve().as_posix()}"
    pg_url = _normalize_url(postgres_url)

    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    postgres_engine = create_engine(pg_url, pool_pre_ping=True)

    Base.metadata.create_all(bind=postgres_engine)

    sqlite_session = sessionmaker(bind=sqlite_engine, autocommit=False, autoflush=False)
    postgres_session = sessionmaker(bind=postgres_engine, autocommit=False, autoflush=False)

    with sqlite_session() as src, postgres_session() as dst:
        for model in MODEL_ORDER:
            copied = _copy_table(src, dst, model)
            print(f"{model.__tablename__}: copied {copied} rows")
        _reset_postgres_sequences(dst)
        print("postgres sequences: reset")

    print("Migration completed.")


if __name__ == "__main__":
    main()
