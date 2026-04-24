from typing import List
from sqlalchemy import Column
from sqlalchemy.types import Text
from sqlmodel import Field, SQLModel, Relationship
from datetime import date


class DIMSResultsHMDBLink(SQLModel, table=True):
    uuid: int = Field(default=None, primary_key=True)
    hmdb_id: int | None = Field(default=None, foreign_key="hmdb.uuid", primary_key=False)
    dims_results_uuid: int | None = Field(default=None, foreign_key="dimsresults.uuid", primary_key=False)
    row_hash: str = None
    adduct: int = None

    dims_result: "DIMSResults" = Relationship(back_populates="hmdb_links")
    hmdb: "HMDB" = Relationship(back_populates="dims_result_links")


class DIMSRun(SQLModel, table=True):
    name: str = Field(primary_key=True)
    date: date
    num_replicates: int = None
    ppm: int = None
    resolution: int = None
    matrix: str = None
    email: str = None
    pipeline_version: str = None

    dims_results: List["DIMSResults"] = Relationship(back_populates="run")


class Patient(SQLModel, table=True):
    intermediate_id: str = Field(primary_key=True)
    birth_date: date | None = None

    samples: List["Sample"] = Relationship(back_populates="patient")


class Sample(SQLModel, table=True):
    id: str = Field(primary_key=True)
    collection_date: date | None = None
    patient_id: str = Field(foreign_key="patient.intermediate_id")

    patient: "Patient" = Relationship(back_populates="samples")
    dims_results: List["DIMSResults"] = Relationship(back_populates="sample")


class DIMSResults(SQLModel, table=True):
    uuid: int = Field(default=None, primary_key=True)
    polarity: bool = None  # Positive = true, negative = false
    m_z: float = None
    intensity: float = None
    z_score: float = None
    ppm_dev: float | None = None
    row_hash: str = None

    sample_id: str = Field(foreign_key="sample.id")
    run_name: str = Field(foreign_key="dimsrun.name", max_length=50)

    hmdb_links: List["DIMSResultsHMDBLink"] = Relationship(back_populates="dims_result")
    sample: "Sample" = Relationship(back_populates="dims_results")
    run: "DIMSRun" = Relationship(back_populates="dims_results")


class HMDB(SQLModel, table=True):
    uuid: int = Field(default=None, primary_key=True)
    hmdb_key: str = Field(max_length=14)
    hmdb_id: str = Field(max_length=14)
    sec_hmdb_id: str = Field(max_length=275)
    name: str = Field(max_length=275)
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

    dims_result_links: List["DIMSResultsHMDBLink"] = Relationship(back_populates="hmdb")
