"""CRUD operations for HMDB records.

This module provides database query and manipulation functions for HMDB entities,
including single and bulk retrieval, insertion, updates, and deletion operations.
It also handles linking HMDB records to measured m/z values.
"""
from pandas import DataFrame
from sqlmodel import Session, select, col, or_
from sqlalchemy import insert
from typing import Any

from dimsdb.models import MeasuredMZ
from dimsdb.models.hmdb import HMDB
from dimsdb.models.linktables import HMDBMeasuredMZ


def select_hmdb_by_hmdb_id(db_session: Session, hmdb_id: str) -> HMDB:
    """Retrieve a single HMDB record by primary HMDB ID.
    
    Args:
        db_session: SQLModel database session.
        hmdb_id: The primary HMDB identifier.
    
    Returns:
        The HMDB record with the given ID, or None if not found.
    """
    statement = select(HMDB).where(HMDB.hmdb_id == hmdb_id)
    return db_session.exec(statement).first()

def select_hmdbs_by_hmdb_ids(db_session: Session, list_hmdb_id: list[str]) -> list[HMDB]:
    """Retrieve multiple HMDB records by a list of primary HMDB IDs.
    
    Args:
        db_session: SQLModel database session.
        list_hmdb_id: List of primary HMDB identifiers.
    
    Returns:
        A list of HMDB records matching the given IDs.
    """
    statement = select(HMDB).where(HMDB.hmdb_id.in_(list_hmdb_id))
    return db_session.exec(statement).all()

def select_hmdbs_by_hmdb_key(db_session: Session, hmdb_key: str) -> list[HMDB]:
    """Retrieve HMDB records by HMDB key.
    
    Args:
        db_session: SQLModel database session.
        hmdb_key: The HMDB key to search for.
    
    Returns:
        A list of HMDB records matching the given key.
    """
    statement = select(HMDB).where(HMDB.hmdb_key == hmdb_key)
    return db_session.exec(statement).all()

def select_hmdb_by_sec_hmdb_id(db_session: Session, hmdb_id: str) -> list[HMDB]:
    """Retrieve HMDB records by secondary HMDB ID.
    
    Secondary HMDB IDs are stored as a semicolon-separated list. This function
    searches for records where the given ID is part of that list.
    
    Args:
        db_session: SQLModel database session.
        hmdb_id: A secondary HMDB identifier.
    
    Returns:
        A list of HMDB records containing the given secondary ID.
    """
    statement = (
        select(HMDB).
        where(or_(col(HMDB.sec_hmdb_id).contains(hmdb_id + ";"), col(HMDB.sec_hmdb_id).endswith(hmdb_id)))
    )
    return db_session.exec(statement).all()

def insert_hmdb(db_session: Session, hmdb: HMDB) -> HMDB:
    """Insert a single HMDB record into the database.
    
    The record is added to the session, committed, and refreshed to ensure
    consistency with the database state.
    
    Args:
        db_session: SQLModel database session.
        hmdb: The HMDB record to insert.
    
    Returns:
        The inserted HMDB record, refreshed from the database.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.add(hmdb)
        db_session.commit()
        db_session.refresh(hmdb)
    except Exception:
        db_session.rollback()
        raise
    return hmdb

def insert_hmdb_table(db_session: Session, hmdb_df: DataFrame) -> None:
    """Insert HMDB records from a DataFrame directly into the database table.
    
    This function writes a DataFrame containing HMDB records to the HMDB table
    using pandas' to_sql method with chunking for performance. Executed within
    a database transaction.
    
    Args:
        db_session: SQLModel database session.
        hmdb_df: DataFrame containing HMDB records with columns matching the table schema.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        with db_session.begin() as conn:
            hmdb_df.to_sql(name='hmdb', con=conn, index=False, if_exists='append', chunksize=5000)
    except Exception:
        db_session.rollback()
        raise

def insert_hmdb_in_bulk(db_session: Session, list_hmdb_dicts: list[dict[str, Any]]) -> None:
    """Insert multiple HMDB records in bulk using parameterized insert.
    
    This function uses SQLAlchemy's insert() construct with parameter binding
    for efficient bulk insertion of multiple records.
    
    Args:
        db_session: SQLModel database session.
        list_hmdb_dicts: List of dictionaries containing HMDB data.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.exec(insert(HMDB), params=list_hmdb_dicts)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise

def update_hmdb(db_session: Session, hmdb: HMDB, hmdb_data: dict) -> HMDB:
    """Update an HMDB record with new data.
    
    The record is updated with the provided data, committed, and refreshed
    to ensure consistency with the database state.
    
    Args:
        db_session: SQLModel database session.
        hmdb: The HMDB record to update.
        hmdb_data: Dictionary of field names and new values.
    
    Returns:
        The updated HMDB record, refreshed from the database.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        hmdb.sqlmodel_update(hmdb_data)
        db_session.add(hmdb)
        db_session.commit()
        db_session.refresh(hmdb)
    except Exception:
        db_session.rollback()
        raise
    return hmdb

def delete_hmdb(db_session: Session, hmdb: HMDB) -> None:
    """Delete an HMDB record from the database.
    
    Args:
        db_session: SQLModel database session.
        hmdb: The HMDB record to delete.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.delete(hmdb)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise

def link_measuredmz(db_session: Session, hmdb: HMDB, measuredmz: MeasuredMZ, adduct: int) -> None:
    """Create a relationship between an HMDB record and a measured m/z value.
    
    Establishes a junction table entry linking the HMDB entity to a measured m/z
    entity with a specific adduct value.
    
    Args:
        db_session: SQLModel database session.
        hmdb: The HMDB record to link.
        measuredmz: The measured m/z record to link.
        adduct: The adduct type or charge state associated with the link.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        link = HMDBMeasuredMZ(
            hmdb=hmdb,
            measuredmz=measuredmz,
            adduct=adduct
        )
        db_session.add(link)
        db_session.commit()
        db_session.refresh(link)
    except Exception:
        db_session.rollback()
        raise
