"""Models for Human Metabolome Database (HMDB) integration.

This module defines the HMDB model for storing metabolite information and
linking to measured m/z values.
"""
from sqlalchemy import Column
from sqlalchemy.types import Text
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel

if TYPE_CHECKING:
    from dimsdb.models.linktables import HMDBMeasuredMZ


class HMDB(BaseModel, table=True):
    """Representation of a metabolite record from HMDB.
    
    Stores HMDB identifiers, descriptive metadata, and relationships to measured
    m/z values. Text fields use SQLAlchemy Text columns to preserve formatting
    of longer descriptions.
    
    Attributes:
        id: Primary key for the HMDB record.
        hmdb_key: HMDB key for metabolites sharing the same chemical formula.
        hmdb_id: Primary HMDB identifier.
        sec_hmdb_id: Secondary HMDB identifiers for alternative records.
        name: Chemical name of the compound from HMDB.
        theor_mz: Theoretical m/z value for the compound.
        chem_formula: Chemical formula when available.
        description: Longer textual description from HMDB.
        relevance: Relevance notes or curation remarks.
        origin: Origin information (e.g., endogenous, exogenous).
        fluids: Typical biological fluids where the compound is observed.
        tissue: Typical tissues where the compound is observed.
        disease: Associated disease annotations.
        pathway: Biochemical pathway annotations.
        hmdb_links: Relationship to MeasuredMZ objects linked to this entry.
    """


    id: int = Field(default=None, primary_key=True)
    
    hmdb_key: str = Field(max_length=14)
    hmdb_id: str = Field(max_length=14)
    sec_hmdb_id: str = Field(max_length=300)
    name: str = Field(max_length=300)
    theor_mz: float
    
    chem_formula: str | None = None

    description: str | None = Field(default=None, sa_column=Column(Text))
    relevance: str | None = Field(default=None, sa_column=Column(Text))
    origin: str | None = Field(default=None, sa_column=Column(Text))
    fluids: str | None = Field(default=None, sa_column=Column(Text))
    tissue: str | None = Field(default=None, sa_column=Column(Text))
    disease: str | None = Field(default=None, sa_column=Column(Text))
    pathway: str | None = Field(default=None, sa_column=Column(Text))

    hmdb_links: list["HMDBMeasuredMZ"] = Relationship(back_populates="hmdb")