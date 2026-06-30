"""CRUD operations for Sample records.

This module provides database query and manipulation functions for Sample entities,
including retrieval, insertion, updates, and deletion operations. It also handles
linking samples to patients and DIMS runs.
"""
from sqlmodel import Session

from dimsdb.models import DIMSRun
from dimsdb.models.sample import Sample
from dimsdb.models.patient import Patient


def select_sample_by_id(db_session: Session, sample_id: str) -> Sample:
    """Retrieve a sample record by its ID.
    
    Args:
        db_session: SQLModel database session.
        sample_id: The unique identifier of the sample.
    
    Returns:
        The Sample record with the given ID.
    """
    return db_session.get_one(Sample, sample_id)

def insert_sample(db_session: Session, sample: Sample) -> Sample:
    """Insert a single sample record into the database.
    
    The record is added to the session, committed, and refreshed to ensure
    consistency with the database state.
    
    Args:
        db_session: SQLModel database session.
        sample: The Sample record to insert.
    
    Returns:
        The inserted Sample record, refreshed from the database.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.add(sample)
        db_session.commit()
        db_session.refresh(sample)
    except Exception:
        db_session.rollback()
        raise
    return sample

def update_sample(db_session: Session, sample: Sample, sample_data: dict) -> Sample:
    """Update a sample record with new data.
    
    The record is updated with the provided data, committed, and refreshed
    to ensure consistency with the database state.
    
    Args:
        db_session: SQLModel database session.
        sample: The Sample record to update.
        sample_data: Dictionary of field names and new values.
    
    Returns:
        The updated Sample record, refreshed from the database.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        sample.sqlmodel_update(sample_data)
        db_session.add(sample)
        db_session.commit()
        db_session.refresh(sample)
    except Exception:
        db_session.rollback()
        raise
    return sample

def delete_sample(db_session: Session, sample: Sample) -> None:
    """Delete a sample record from the database.
    
    Args:
        db_session: SQLModel database session.
        sample: The Sample record to delete.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.delete(sample)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise

def link_patient(db_session: Session, sample: Sample, patient: Patient) -> Sample:
    """Create a relationship between a sample and a patient.
    
    Adds the patient to the sample's patient list and commits the change.
    
    Args:
        db_session: SQLModel database session.
        sample: The Sample record to link.
        patient: The Patient record to link.
    
    Returns:
        The updated Sample record with the patient relationship established.
    """

    sample.patients.append(patient)
    db_session.add(sample)
    db_session.commit()
    db_session.refresh(sample)
    return sample

def link_dimsrun(db_session: Session, sample: Sample, dimsrun: DIMSRun) -> Sample:
    """Create a relationship between a sample and a DIMS run.
    
    Adds the DIMS run to the sample's dimsruns list and commits the change.
    
    Args:
        db_session: SQLModel database session.
        sample: The Sample record to link.
        dimsrun: The DIMSRun record to link.
    
    Returns:
        The updated Sample record with the DIMS run relationship established.
    """
    sample.dimsruns.append(dimsrun)
    db_session.add(sample)
    db_session.commit()
    db_session.refresh(sample)
    return sample