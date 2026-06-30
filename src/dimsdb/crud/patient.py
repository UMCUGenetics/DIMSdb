"""CRUD operations for Patient records.

This module provides database query and manipulation functions for Patient entities,
including retrieval by various criteria, insertion, updates, and deletion operations.
It also handles linking patients to samples.
"""
from typing import List
from sqlmodel import Session, select
from datetime import date
from dimsdb.models.patient import Patient
from dimsdb.models.sample import Sample

def select_patient_by_id(db_session: Session, patient_id: str) -> Patient:
    """Retrieve a patient record by its ID.
    
    Args:
        db_session: SQLModel database session.
        patient_id: The unique identifier of the patient.
    
    Returns:
        The Patient record with the given ID.
    """
    return db_session.get_one(Patient, patient_id)

def select_patients_by_diagnosis(db_session: Session, patient_diagnosis_id: str) -> List[Patient]:
    """Retrieve patients by diagnosis identifier.
    
    Args:
        db_session: SQLModel database session.
        patient_diagnosis_id: The diagnosis identifier to filter by.
    
    Returns:
        A list of Patient records matching the given diagnosis.
    """
    statement = select(Patient).where(Patient.diagnosis == patient_diagnosis_id)
    return db_session.exec(statement).all()

def select_patients_by_birth_date(db_session: Session, date_range_start: date, date_range_end: date) -> List[Patient]:
    """Retrieve patients whose birth dates fall within a specified range.
    
    Args:
        db_session: SQLModel database session.
        date_range_start: The start of the date range (inclusive).
        date_range_end: The end of the date range (inclusive).
    
    Returns:
        A list of Patient records with birth dates within the range.
    """
    statement = (
        select(Patient)
        .where(Patient.birth_date >= date_range_start)
        .where(Patient.birth_date <= date_range_end)
    )
    return db_session.exec(statement).all()

def insert_patient(db_session: Session, patient: Patient) -> Patient:
    """Insert a single patient record into the database.
    
    The record is added to the session, committed, and refreshed to ensure
    consistency with the database state.
    
    Args:
        db_session: SQLModel database session.
        patient: The Patient record to insert.
    
    Returns:
        The inserted Patient record, refreshed from the database.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
    except Exception:
        db_session.rollback()
        raise
    return patient

def update_patient(db_session: Session, patient: Patient, patient_data: dict) -> Patient:
    """Update a patient record with new data.
    
    The record is updated with the provided data, committed, and refreshed
    to ensure consistency with the database state.
    
    Args:
        db_session: SQLModel database session.
        patient: The Patient record to update.
        patient_data: Dictionary of field names and new values.
    
    Returns:
        The updated Patient record, refreshed from the database.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        patient.sqlmodel_update(patient_data)
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
    except Exception:
        db_session.rollback()
        raise
    return patient

def delete_patient(db_session: Session, patient: Patient) -> None:
    """Delete a patient record from the database.
    
    Args:
        db_session: SQLModel database session.
        patient: The Patient record to delete.
    
    Raises:
        Exception: If the database operation fails; the transaction is rolled back.
    """
    try:
        db_session.delete(patient)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise

def link_sample(db_session: Session, patient: Patient, sample: Sample) -> Patient:
    """Create a relationship between a patient and a sample.
    
    Adds the sample to the patient's samples list and commits the change.
    
    Args:
        db_session: SQLModel database session.
        patient: The Patient record to link.
        sample: The Sample record to link.
    
    Returns:
        The updated Patient record with the sample relationship established.
    """
    patient.samples.append(sample)
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient
