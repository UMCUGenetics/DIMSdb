from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel


class DIMS_run(SQLModel, table=True):
    name: str = Field(primary_key=True)
    email: str = None
    date: date = None
    num_replicates: None


class Dims_result(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    run_name: str = Field(max_length=50)
    hmdb_id: Optional[str] = Field(max_length=11)
    polarity: bool = None # Positive = true, negative = false
    m_z: float = Field(primary_key=True)
    intensity: float = None
    z_score: float = None


class HMDB(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    MZ: float


class Sample(SQLModel, table=True):
    id: str = Field(primary_key=True)
    type: str = None


class Patient(SQLModel, table=True):
    intermediate_id: str = Field(primary_key=True)
    birth_year: Optional[int] = None