"""CRUD operations for managing junction table relationships.

This module provides functions for bulk inserting link records into junction
tables that establish many-to-many relationships between entities.
"""
from sqlalchemy import insert
from sqlmodel import Session


def insert_bulk_links(db_session: Session, model, values: list[dict]) -> None:
    """Bulk insert link records into a junction table.
    
    Creates multiple relationships between entities by inserting rows into
    a junction table. Automatically commits on success or rolls back on failure.
    
    Args:
        db_session: Active database session for executing the operation.
        model: SQLModel class representing the junction table.
        values: List of dictionaries containing the link data to insert.
    
    Raises:
        Exception: Re-raises any exception that occurs during insertion after
            rolling back the transaction.
    """
    try:
        db_session.exec(insert(model), params=values)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
