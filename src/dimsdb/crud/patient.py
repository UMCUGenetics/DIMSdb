from typing import List
from sqlmodel import Session, select
from datetime import date
from dimsdb.archive.models import Patient

def select_patient_by_id(db_session: Session, patient_id: str) -> Patient:
    return db_session.get_one(Patient, patient_id)

def select_patients_by_diagnosis(db_session: Session, patient_diagnosis_id: str) -> List[Patient]:
    statement = select(Patient).where(Patient.diagnosis == patient_diagnosis_id)
    return db_session.exec(statement).all()

def select_patients_by_birth_date(db_session: Session, date_range_start: date, date_range_end: date) -> List[Patient]:
    statement = (
        select(Patient)
        .where(Patient.birth_date >= date_range_start)
        .where(Patient.birth_date <= date_range_end)
    )
    return db_session.exec(statement).all()

def insert_patient(db_session: Session, patient: Patient) -> Patient:
    try:
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
    except Exception:
        db_session.rollback()
        raise
    return patient

def update_patient(db_session: Session, patient: Patient, patient_data: dict) -> Patient:
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
    try:
        db_session.delete(patient)
        db_session.commit()
    except Exception:
        db_session.rollback()
    raise
