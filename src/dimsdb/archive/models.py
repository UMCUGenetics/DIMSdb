"""SQLModel ORM models for the DIMSdb project.

This module defines the database models used throughout the project and
their relationships. Models are implemented using SQLModel and rely on
link tables defined in ``dimsdb.models.linktables`` to express many-to-many
relationships between entities.
"""

from sqlalchemy import Column
from sqlalchemy.types import Text
from sqlmodel import Field, SQLModel, Relationship
from datetime import date

from dimsdb.models.linktables import (DIMSRunSample, DIMSRunMeasuredMZ, HMDBMeasuredMZ, DIMSResultsSample, PatientSample,
                                      DIMSResultsMeasuredMZ)

class Patient(SQLModel, table=True):
    """Represent a patient and their associated samples.

    This model stores basic patient metadata and defines a relationship to
    ``Sample`` objects through the ``PatientSample`` link table.

    Attributes:
        id: Primary key for the patient.
        patient_id: Unique identifier for the patient (external or clinical ID).
        birth_date: Patient's date of birth or None if unknown.
        diagnosis: Clinical diagnosis or notes associated with the patient.
        samples: List of associated Sample objects.
    """
    id: int = Field(primary_key=True)
    patient_id: str | None = None
    birth_date: date | None = None
    diagnosis: str | None = None
    samples: list["Sample"] = Relationship(link_model=PatientSample, back_populates="patients")

class Sample(SQLModel, table=True):
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
    id: int = Field(primary_key=True)
    sample_id: str | None = None
    collection_date: date | None = None
    patients: list["Patient"] = Relationship(link_model=PatientSample, back_populates="samples")
    dimsresults: list["DIMSResults"] = Relationship(link_model=DIMSResultsSample, back_populates="samples")
    dimsruns: list["DIMSRun"] = Relationship(link_model=DIMSRunSample, back_populates="samples")

class DIMSRun(SQLModel, table=True):
    """Metadata representing a single DIMS experimental run.

    The model captures run-level configuration (name, date, instrument
    settings) and relationships to measured m/z values and samples.

    Attributes:
        id: Primary key for the run.
        name: Human-readable name of the run.
        date: Date of the DIMS run.
        num_replicates: Optional number of replicates.
        ppm: Parts-per-million tolerance used during peak annotation.
        resolution: Instrument resolution setting.
        matrix: Biological matrix (e.g., plasma, urine) used for the run.
        email: Contact email of the submitter.
        pipeline_version: Version of the processing pipeline that produced outputs.
        samples: Samples measured in this run.
        measuredmzs: MeasuredMZ entries recorded for this run.
    """
    id: int = Field(primary_key=True)
    run_id: str
    date: date
    num_replicates: int | None = None
    ppm: int = None
    resolution: int = None
    matrix: str = None
    email: str = None
    pipeline_version: str | None = None
    samples: list["Sample"] = Relationship(link_model=DIMSRunSample, back_populates="dimsruns")
    measuredmzs: list["MeasuredMZ"] = Relationship(link_model=DIMSRunMeasuredMZ, back_populates="dimsruns")

class HMDB(SQLModel, table=True):
    """Representation of an HMDB database entry linked to measured m/z.

    This model stores HMDB identifiers, descriptive metadata and a list of
    MeasuredMZ objects that reference the HMDB entry. Fields that may
    contain long textual content use a Text column to preserve formatting.

    Attributes:
        id: Primary key for the HMDB record.
        hmdb_key: HMDB id that is used for metabolites with the same chemical formula.
        hmdb_id: Primary HMDB identifier.
        sec_hmdb_id: Secondary HMDB identifiers.
        name: Chemical name from HMDB.
        chem_formula: Chemical formula when available.
        description: Longer textual description from HMDB.
        theor_mz: Theoretical m/z value for the compound.
        relevance: Relevance notes or curation remarks.
        origin: Origin information (e.g., endogenous, exogenous).
        fluids: Typical fluids where the compound is observed.
        tissue: Typical tissues of where the compound is observed.
        disease: Associated disease annotations.
        pathway: Pathway annotations.
        measuredmzs: List of MeasuredMZ objects linked to this HMDB entry.
    """
    id: int = Field(default=None, primary_key=True)
    hmdb_key: str = Field(max_length=14)
    hmdb_id: str = Field(max_length=14)
    sec_hmdb_id: str = Field(max_length=300)
    name: str = Field(max_length=300)
    chem_formula: str | None = None
    description: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    theor_mz: float
    relevance: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    origin: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    fluids: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    tissue: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    disease: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    pathway: str | None = Field(
        default=None,
        sa_column=Column(Text)
    )
    measuredmzs: list["MeasuredMZ"] = Relationship(link_model=HMDBMeasuredMZ, back_populates="hmdbs")

class DIMSResults(SQLModel, table=True):
    """Measured intensity and z-score results linked to samples.

    This table stores the per-sample quantitative results produced by the
    DIMS pipeline and connects to samples using a link table. Results may
    be shared across multiple samples via the association table.

    Attributes:
        id: Primary key for the result row.
        intensity: Measured intensity value for the feature.
        z_score: Z-score or normalized value when available.
        samples: Samples associated with this result.
        measuredmzs: MeasuredMZ entries associated with this result.
    """
    id: int = Field(default=None, primary_key=True)
    intensity: float | None = None
    z_score: float | None = None
    samples: list["Sample"] = Relationship(link_model=DIMSResultsSample, back_populates="dimsresults")
    measuredmzs: list["MeasuredMZ"] = Relationship(link_model=DIMSResultsMeasuredMZ, back_populates="dimsresults")

class MeasuredMZ(SQLModel, table=True):
    """A measured mass/charge (m/z) value recorded in a DIMS run.

    Each MeasuredMZ corresponds to an observed m/z in a specific run and
    may be linked to HMDB entries, DIMS runs, and result rows through link
    tables.

    Attributes:
        id: Primary key for the measured m/z.
        mz: Observed mass/charge value.
        is_positive: Whether the measurement was made in the positive mode, or negative.
        ppm_dev: Measured parts-per-million deviation for the peak.
        dimsruns: DIMSRun entries that include this measured m/z.
        hmdbs: HMDB entries associated with this measured m/z.
        dimsresults: DIMSResults entries associated with this measured m/z.
    """
    id: int = Field(default=None, primary_key=True)
    mz: float
    is_positive: bool = None
    ppm_dev: float | None = None
    dimsruns: list["DIMSRun"] = Relationship(link_model=DIMSRunMeasuredMZ, back_populates="measuredmzs")
    hmdbs: list["HMDB"] = Relationship(link_model=HMDBMeasuredMZ, back_populates="measuredmzs")
    dimsresults: list["DIMSResults"] = Relationship(link_model=DIMSResultsMeasuredMZ, back_populates="measuredmzs")
