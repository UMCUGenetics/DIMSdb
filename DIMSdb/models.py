from typing import Optional
from sqlmodel import Field, SQLModel


class HMDB(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    MZ: float


class Patient(SQLModel, table=True):
    intermediate_id: str = Field(primary_key=True)
    birth_year: Optional[int] = None