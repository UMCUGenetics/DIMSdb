"""CRUD operations for managing DIMSResults records.

This module provides functions for creating, reading, updating, and deleting
DIMS result records, as well as establishing relationships between results
and other entities like samples and measured m/z values.
"""
from typing import Any

from sqlalchemy import insert
from sqlmodel import Session, select

from dimsdb.models.dimsresults import DIMSResults
from dimsdb.models.sample import Sample
from dimsdb.models.measuredmz import MeasuredMZ


def select_dimsresults_by_id(db_session: Session, dimsresults_id: int) -> DIMSResults:
    """Retrieve a DIMSResults record by its ID.
    
    Args:
        db_session: Active database session.
        dimsresults_id: The ID of the DIMSResults record to retrieve.
    
    Returns:
        The DIMSResults record matching the given ID.
    
    Raises:
        Exception: If no record is found with the given ID.
    """
    return db_session.get_one(DIMSResults, dimsresults_id)


def select_ids_by_temp_keys(db_session: Session, temp_keys: list[str]) -> dict[str, int]:
    """Map temporary keys to database IDs for DIMSResults records.
    
    Retrieves the mapping between temporary tracking keys and assigned database IDs
    for a set of DIMSResults records.
    
    Args:
        db_session: Active database session.
        temp_keys: List of temporary keys to look up.
    
    Returns:
        A dictionary mapping temporary keys to their corresponding database IDs.
    """
    statement = (
        select(DIMSResults.id, DIMSResults.temp_id)
        .where(DIMSResults.temp_id.in_(temp_keys))
    )
    results = db_session.exec(statement).all()
    return {row.temp_id: row.id for row in results}


def insert_dimsresults(db_session: Session, dimsresults: DIMSResults) -> DIMSResults:
    """Create a new DIMSResults record in the database.
    
    Inserts a DIMSResults record and automatically commits the transaction.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        dimsresults: The DIMSResults object to insert.
    
    Returns:
        The inserted DIMSResults record with refreshed data from the database.
    
    Raises:
        Exception: Re-raises any exception that occurs during insertion after
            rolling back the transaction.
    """
    try:
        db_session.add(dimsresults)
        db_session.commit()
        db_session.refresh(dimsresults)
    except Exception:
        db_session.rollback()
        raise
    return dimsresults


def insert_bulk_dimsresults(db_session: Session, list_dimsresults_dicts: list[dict[str, Any]]) -> None:
    """Bulk insert multiple DIMSResults records into the database.
    
    Creates multiple DIMSResults records in a single batch operation.
    Automatically commits on success or rolls back on failure.
    
    Args:
        db_session: Active database session.
        list_dimsresults_dicts: List of dictionaries containing DIMSResults data to insert.
    
    Raises:
        Exception: Re-raises any exception that occurs during insertion after
            rolling back the transaction.
    """
    try:
        db_session.exec(insert(DIMSResults), params=list_dimsresults_dicts)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise


def update_dimsresults(db_session: Session, dimsresults: DIMSResults, dimsresults_data: dict) -> DIMSResults:
    """Update an existing DIMSResults record with new data.
    
    Applies the provided data to the DIMSResults and commits the changes.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        dimsresults: The DIMSResults record to update.
        dimsresults_data: Dictionary containing the fields to update.
    
    Returns:
        The updated DIMSResults record with refreshed data from the database.
    
    Raises:
        Exception: Re-raises any exception that occurs during update after
            rolling back the transaction.
    """
    try:
        dimsresults.sqlmodel_update(dimsresults_data)
        db_session.add(dimsresults)
        db_session.commit()
        db_session.refresh(dimsresults)
    except Exception:
        db_session.rollback()
        raise
    return dimsresults


def delete_dimsresults(db_session: Session, dimsresults: DIMSResults) -> None:
    """Delete a DIMSResults record from the database.
    
    Removes the specified DIMSResults and commits the deletion.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        dimsresults: The DIMSResults record to delete.
    
    Raises:
        Exception: Re-raises any exception that occurs during deletion after
            rolling back the transaction.
    """
    try:
        db_session.delete(dimsresults)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise


def link_sample(db_session: Session, dimsresults: DIMSResults, sample: Sample) -> DIMSResults:
    """Link a Sample to a DIMSResults record.
    
    Associates a sample with a result by appending it to the result's samples list
    and committing the relationship.
    
    Args:
        db_session: Active database session.
        dimsresults: The DIMSResults to link the sample to.
        sample: The Sample to link to the result.
    
    Returns:
        The updated DIMSResults record with the linked sample.
    """
    try:
        dimsresults.samples.append(sample)
        db_session.add(dimsresults)
        db_session.commit()
        db_session.refresh(dimsresults)
    except Exception:
        db_session.rollback()
    return dimsresults


def link_measuredmz(db_session: Session, dimsresults: DIMSResults, measuredmz: MeasuredMZ) -> DIMSResults:
    """Link a MeasuredMZ to a DIMSResults record.
    
    Associates a measured m/z value with a result by appending it to the result's
    measuredmzs list and committing the relationship.
    
    Args:
        db_session: Active database session.
        dimsresults: The DIMSResults to link the measured m/z to.
        measuredmz: The MeasuredMZ to link to the result.
    
    Returns:
        The updated DIMSResults record with the linked measured m/z.
    """
    try:
        dimsresults.measuredmzs.append(measuredmz)
        db_session.add(dimsresults)
        db_session.commit()
        db_session.refresh(dimsresults)
    except Exception:
        db_session.rollback()
    return dimsresults
