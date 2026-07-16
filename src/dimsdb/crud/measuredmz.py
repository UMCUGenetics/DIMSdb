"""CRUD operations for managing MeasuredMZ records.

This module provides functions for creating, reading, updating, and deleting
measured m/z value records, as well as establishing relationships between
measured m/z values and DIMS runs.
"""
from typing import Any

from sqlalchemy import insert
from sqlmodel import Session, select

from dimsdb.models.measuredmz import MeasuredMZ
from dimsdb.models.dimsrun import DIMSRun


def select_measuredmz_by_id(db_session: Session, id: int) -> MeasuredMZ:
    """Retrieve a MeasuredMZ record by its ID.
    
    Args:
        db_session: Active database session.
        id: The ID of the MeasuredMZ record to retrieve.
    
    Returns:
        The MeasuredMZ record matching the given ID.
    
    Raises:
        Exception: If no record is found with the given ID.
    """
    return db_session.get_one(MeasuredMZ, id)


def select_measuredmz_by_mz(db_session: Session, mz_start: float, mz_end: float) -> list[MeasuredMZ]:
    """Retrieve MeasuredMZ records within a specified m/z range.
    
    Args:
        db_session: Active database session.
        mz_start: The lower bound of the m/z range (inclusive).
        mz_end: The upper bound of the m/z range (inclusive).
    
    Returns:
        A list of MeasuredMZ records within the specified range.
    """
    statement = (
        select(MeasuredMZ)
        .where(MeasuredMZ.mz >= mz_start)
        .where(MeasuredMZ.mz <= mz_end)
    )
    return db_session.exec(statement).all()


def select_ids_by_temp_keys(db_session: Session, temp_keys: list[str]) -> dict[str, int]:
    """Map temporary keys to database IDs for MeasuredMZ records.
    
    Retrieves the mapping between temporary tracking keys and assigned database IDs
    for a set of MeasuredMZ records.
    
    Args:
        db_session: Active database session.
        temp_keys: List of temporary keys to look up.
    
    Returns:
        A dictionary mapping temporary keys to their corresponding database IDs.
    """
    statement = (
        select(MeasuredMZ.id, MeasuredMZ.temp_id)
        .where(MeasuredMZ.temp_id.in_(temp_keys))
    )
    results = db_session.exec(statement).all()
    return {row.temp_id: row.id for row in results}


def insert_measuredmz(db_session: Session, measuredmz: MeasuredMZ) -> MeasuredMZ:
    """Create a new MeasuredMZ record in the database.
    
    Inserts a MeasuredMZ record and automatically commits the transaction.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        measuredmz: The MeasuredMZ object to insert.
    
    Returns:
        The inserted MeasuredMZ record with refreshed data from the database.
    
    Raises:
        Exception: Re-raises any exception that occurs during insertion after
            rolling back the transaction.
    """
    try:
        db_session.add(measuredmz)
        db_session.commit()
        db_session.refresh(measuredmz)
    except Exception:
        db_session.rollback()
        raise
    return measuredmz


def insert_bulk_measuredmzs(db_session: Session, list_measuredmz_dicts: list[dict[str, Any]]) -> None:
    """Bulk insert multiple MeasuredMZ records into the database.
    
    Creates multiple MeasuredMZ records in a single batch operation.
    Automatically commits on success or rolls back on failure.
    
    Args:
        db_session: Active database session.
        list_measuredmz_dicts: List of dictionaries containing MeasuredMZ data to insert.
    
    Raises:
        Exception: Re-raises any exception that occurs during insertion after
            rolling back the transaction.
    """
    try:
        db_session.exec(insert(MeasuredMZ), params=list_measuredmz_dicts)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise


def update_measuredmz(db_session: Session, measuredmz: MeasuredMZ, measuredmz_data: dict) -> MeasuredMZ:
    """Update an existing MeasuredMZ record with new data.
    
    Applies the provided data to the MeasuredMZ and commits the changes.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        measuredmz: The MeasuredMZ record to update.
        measuredmz_data: Dictionary containing the fields to update.
    
    Returns:
        The updated MeasuredMZ record with refreshed data from the database.
    
    Raises:
        Exception: Re-raises any exception that occurs during update after
            rolling back the transaction.
    """
    try:
        measuredmz.sqlmodel_update(measuredmz_data)
        db_session.add(measuredmz)
        db_session.commit()
        db_session.refresh(measuredmz)
    except Exception:
        db_session.rollback()
        raise
    return measuredmz


def delete_measuredmz(db_session: Session, measuredmz: MeasuredMZ) -> None:
    """Delete a MeasuredMZ record from the database.
    
    Removes the specified MeasuredMZ and commits the deletion.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        measuredmz: The MeasuredMZ record to delete.
    
    Raises:
        Exception: Re-raises any exception that occurs during deletion after
            rolling back the transaction.
    """
    try:
        db_session.delete(measuredmz)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise


def link_dimsrun(db_session: Session, measuredmz: MeasuredMZ, dimsrun: DIMSRun) -> MeasuredMZ:
    """Link a DIMSRun to a MeasuredMZ record.
    
    Associates a DIMS run with a measured m/z value by appending it to the
    measured m/z's dimsruns list and committing the relationship.
    
    Args:
        db_session: Active database session.
        measuredmz: The MeasuredMZ to link the run to.
        dimsrun: The DIMSRun to link to the measured m/z.
    
    Returns:
        The updated MeasuredMZ record with the linked run.
    """
    try:
        measuredmz.dimsruns.append(dimsrun)
        db_session.add(measuredmz)
        db_session.commit()
        db_session.refresh(measuredmz)
    except Exception:
        db_session.rollback()
    return measuredmz