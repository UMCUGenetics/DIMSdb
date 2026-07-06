"""Sample model representing biological samples in the database.

This module defines the Sample entity and its relationships to patients,
DIMS runs, and measurement results.
"""
from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import PatientSample, DIMSResultsSample, DIMSRunSample

if TYPE_CHECKING:
    from dimsdb.models.patient import Patient
    from dimsdb.models.dimsresults import DIMSResults
    from dimsdb.models.dimsrun import DIMSRun

class Sample(BaseModel, table=True):
    """A biological sample collected from a patient.

    Samples may be linked to patients, DIMS runs, and measured results. The
    model centralizes collection metadata and relationships used when
    importing or querying experimental data.

    Attributes:
        id: Primary key for the sample.
        sample_id: Unique identifier for the sample (external or lab ID).
        collection_date: Date the sample was collected, when available.
        patients: List of Patient objects linked to this sample.
        dimsresults: DIMSResults associated with this sample.
        dimsruns: DIMSRun entries that contain this sample.
    """
    id: int | None = Field(primary_key=True)
    sample_id: str | None = None
    collection_date: date | None = None

    patients: list["Patient"] = Relationship(
        link_model=PatientSample,
        back_populates="samples")
    dimsresults: list["DIMSResults"] = Relationship(
        link_model=DIMSResultsSample,
        back_populates="samples")
    dimsruns: list["DIMSRun"] = Relationship(
        link_model=DIMSRunSample,
        back_populates="samples")

