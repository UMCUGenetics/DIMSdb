"""CRUD operations for managing DIMSRun records.

This module provides functions for creating, reading, updating, and deleting
DIMS run records, as well as establishing relationships between runs and other
entities like samples and measured m/z values.
"""
from sqlmodel import Session

from dimsdb.models.dimsrun import DIMSRun
from dimsdb.models.sample import Sample
from dimsdb.models.measuredmz import MeasuredMZ


def select_dimsrun_by_runname(db_session: Session, runname: str) -> DIMSRun | None:
    """Retrieve a DIMSRun record by its run name.
    
    Args:
        db_session: Active database session.
        runname: The unique run name identifier.
    
    Returns:
        The DIMSRun record if found, otherwise None.
    """
    return db_session.get_one(DIMSRun, runname)


def insert_dimsrun(db_session: Session, run: DIMSRun) -> DIMSRun:
    """Create a new DIMSRun record in the database.
    
    Inserts a DIMSRun record and automatically commits the transaction.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        run: The DIMSRun object to insert.
    
    Returns:
        The inserted DIMSRun record with refreshed data from the database.
    
    Raises:
        Exception: Re-raises any exception that occurs during insertion after
            rolling back the transaction.
    """
    try:
        db_session.add(run)
        db_session.commit()
        db_session.refresh(run)
    except Exception:
        db_session.rollback()
        raise
    return run


def update_dimsrun(db_session: Session, dimsrun: DIMSRun, run_data: dict) -> DIMSRun:
    """Update an existing DIMSRun record with new data.
    
    Applies the provided data to the DIMSRun and commits the changes.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        dimsrun: The DIMSRun record to update.
        run_data: Dictionary containing the fields to update.
    
    Returns:
        The updated DIMSRun record with refreshed data from the database.
    
    Raises:
        Exception: Re-raises any exception that occurs during update after
            rolling back the transaction.
    """
    try:
        dimsrun.sqlmodel_update(run_data)
        db_session.add(dimsrun)
        db_session.commit()
        db_session.refresh(dimsrun)
    except Exception:
        db_session.rollback()
        raise
    return dimsrun


def delete_dimsrun(db_session: Session, dimsrun: DIMSRun) -> None:
    """Delete a DIMSRun record from the database.
    
    Removes the specified DIMSRun and commits the deletion.
    Rolls back on any exception.
    
    Args:
        db_session: Active database session.
        dimsrun: The DIMSRun record to delete.
    
    Raises:
        Exception: Re-raises any exception that occurs during deletion after
            rolling back the transaction.
    """
    try:
        db_session.delete(dimsrun)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise


def link_samples(db_session: Session, dimsrun: DIMSRun, sample: Sample) -> DIMSRun:
    """Link a Sample to a DIMSRun.
    
    Associates a sample with a run by appending it to the run's samples list
    and committing the relationship.
    
    Args:
        db_session: Active database session.
        dimsrun: The DIMSRun to link the sample to.
        sample: The Sample to link to the run.
    
    Returns:
        The updated DIMSRun record with the linked sample.
    """
    try:
        dimsrun.samples.append(sample)
        db_session.add(dimsrun)
        db_session.commit()
        db_session.refresh(dimsrun)
    except Exception:
        db_session.rollback()
    return dimsrun


def link_measuredmz(db_session: Session, dimsrun: DIMSRun, measuredmz: MeasuredMZ) -> DIMSRun:
    """Link a MeasuredMZ to a DIMSRun.
    
    Associates a measured m/z value with a run by appending it to the run's
    measuredmzs list and committing the relationship.
    
    Args:
        db_session: Active database session.
        dimsrun: The DIMSRun to link the measured m/z to.
        measuredmz: The MeasuredMZ to link to the run.
    
    Returns:
        The updated DIMSRun record with the linked measured m/z.
    """
    try:
        dimsrun.measuredmzs.append(measuredmz)
        db_session.add(dimsrun)
        db_session.commit()
        db_session.refresh(dimsrun)
    except Exception:
        db_session.rollback()
    return dimsrun
