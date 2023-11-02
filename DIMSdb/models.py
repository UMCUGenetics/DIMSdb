from typing import Optional
from sqlmodel import Field, SQLModel


class Dims_result(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    hmdb_id: Optional[str] = None
    polarity: bool = None # Positive = true, negative = false
    m_z: float = None
    intensity: float = None
    z_score: float = None


class HMDB(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    MZ: float


class Patient(SQLModel, table=True):
    intermediate_id: str = Field(primary_key=True)
    birth_year: Optional[int] = None