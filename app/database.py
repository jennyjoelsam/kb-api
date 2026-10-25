"""Database connection setup (SQLAlchemy).

- engine:        the connection to the database file
- SessionLocal:  makes a "session", one conversation with the database
- get_db:        FastAPI gives each request its own session, then closes it
"""
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    """Parent class for all database table classes."""


def make_engine(url: str) -> Engine:
    # SQLite refuses to be used from a different thread than the one that opened it.
    # FastAPI may handle a request on another thread, so we switch that check off.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
