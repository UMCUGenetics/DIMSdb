from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship


class DIMSRun(SQLModel, table=True):
    name: str = Field(primary_key=True)
    email: str = None
    date: datetime = None
    num_replicates: int = None

    dims_results: List["DIMSResults"] = Relationship(back_populates='run')


class DIMSResults(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    run_name: str = Field(max_length=50)
    polarity: bool = None # Positive = true, negative = false
    m_z: float = Field(primary_key=True)
    intensity: float = None
    z_score: float = None

    hmdb_id: Optional[str] = Field(foreign_key='hmdb.id', max_length=11)
    sample_id: str = Field(foreign_key='sample.id')
    run_name: str = Field(foreign_key='dimsrun.name')

    hmdb: Optional["HMDB"] = Relationship(back_populates='dims_results')
    sample: "Sample" = Relationship(back_populates='dims_results')
    run: "DIMSRun" = Relationship(back_populates='dims_results')



class HMDB(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=11)
    name: str
    description: str
    MZ: float

    dims_results: List["DIMSResults"] = Relationship(back_populates='hmdb')


class Sample(SQLModel, table=True):
    id: str = Field(primary_key=True)
    type: str = None

    patient_id: str = Field(foreign_key='patient.intermediate_id')
    patient: "Patient" = Relationship(back_populates='samples')
    dims_results: List["DIMSResults"] = Relationship(back_populates='sample')

class Patient(SQLModel, table=True):
    intermediate_id: str = Field(primary_key=True)
    birth_year: Optional[int] = None

    samples: List["Sample"] = Relationship(back_populates='patient')
