"""Database engine and helpers for creating the project schema.

This module exposes the SQLModel engine configured from project
settings and a convenience helper to recreate the database schema
from the SQLModel metadata.

The helper function is intended for development and testing flows where
rebuilding the schema from models is desired. It will drop all tables
defined in the SQLModel metadata and then recreate them.
"""
from typing import Generator

from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel, Session
from dimsdb.config import settings

engine = create_engine(settings.DATABASE_URL)

def create_db_and_tables() -> None:
    """Drop all tables described by SQLModel metadata and recreate them.

    This function performs destructive operations: it drops all tables
    currently defined in the SQLModel metadata on the configured engine,
    then recreates them. Use with caution in production environments.

    Side effects:
        Drops and creates database tables.
    """
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()

SessionFactory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
