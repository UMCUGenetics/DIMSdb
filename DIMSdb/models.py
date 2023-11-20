from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship


class DIMSRun(SQLModel, table=True):
    name: str = Field(primary_key=True)
    email: str = None
    date: datetime = None
    num_replicates: int = None

    dims_results: List["DIMSResults"] = Relationship(back_populates="run")


class DIMSResultsHMDBLink(SQLModel, table=True):
    hmdb_uuid: Optional[int] = Field(default=None, foreign_key="hmdb.uuid", primary_key=True)
    run_uuid: Optional[int] = Field(default=None, foreign_key="dimsresults.uuid", primary_key=True)


class DIMSResults(SQLModel, table=True):
    uuid: Optional[int] = Field(default=None, primary_key=True)
    run_name: str = Field(max_length=50)
    polarity: bool = None  # Positive = true, negative = false
    m_z: float
    intensity: float = None
    z_score: float = None

    sample_id: str = Field(foreign_key="sample.id")
    run_name: str = Field(foreign_key="dimsrun.name")

    hmdb: List["HMDB"] = Relationship(back_populates="dims_results", link_model=DIMSResultsHMDBLink)
    sample: "Sample" = Relationship(back_populates="dims_results")
    run: "DIMSRun" = Relationship(back_populates="dims_results")


class HMDB(SQLModel, table=True):
    uuid: int = Field(default=None, primary_key=True)
    hmdb_id: str = Field(max_length=14)
    name: str
    description: Optional[str] = None
    MZ: float

    dims_results: List["DIMSResults"] = Relationship(back_populates="hmdb", link_model=DIMSResultsHMDBLink)


class Sample(SQLModel, table=True):
    id: str = Field(primary_key=True)
    type: str = None

    patient_id: str = Field(foreign_key="patient.intermediate_id")
    patient: "Patient" = Relationship(back_populates="samples")
    dims_results: List["DIMSResults"] = Relationship(back_populates="sample")


class Patient(SQLModel, table=True):
    intermediate_id: str = Field(primary_key=True)
    birth_year: Optional[int] = None

    samples: List["Sample"] = Relationship(back_populates="patient")
