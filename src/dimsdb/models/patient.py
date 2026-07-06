"""Patient model representing clinical subjects in the database.

This module defines the Patient entity and its relationships to samples
and other clinical entities.
"""
from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import PatientSample

if TYPE_CHECKING:
    from dimsdb.models.sample import Sample

class Patient(BaseModel, table=True):
    """Represent a patient and their associated samples.

    This model stores basic patient metadata and defines a relationship to
    Sample objects through the PatientSample link table.

    Attributes:
        id: Primary key for the patient.
        patient_id: Unique identifier for the patient (external or clinical ID).
        birth_date: Patient's date of birth or None if unknown.
        diagnosis: Clinical diagnosis or notes associated with the patient.
        samples: List of associated Sample objects.
    """
    id: int | None = Field(primary_key=True)
    patient_id: str | None = None
    birth_date: date | None = None
    diagnosis: str | None = None

    samples: list["Sample"] = Relationship(
        link_model=PatientSample,
        back_populates="patients")