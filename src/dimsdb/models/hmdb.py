from sqlalchemy import Column
from sqlalchemy.types import Text
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import HMDBMeasuredMZ

if TYPE_CHECKING:
    from dimsdb.models.measuredmz import MeasuredMZ

class HMDB(BaseModel, table=True):
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
    theor_mz: float
    
    chem_formula: str | None = None
    
    description: str | None = Field(default=None, sa_column=Column(Text))
    relevance: str | None = Field(default=None, sa_column=Column(Text))
    origin: str | None = Field(default=None, sa_column=Column(Text))
    fluids: str | None = Field(default=None, sa_column=Column(Text))
    tissue: str | None = Field(default=None, sa_column=Column(Text))
    disease: str | None = Field(default=None, sa_column=Column(Text))
    pathway: str | None = Field(default=None, sa_column=Column(Text))

    measuredmzs: list["MeasuredMZ"] = Relationship(
        link_model=HMDBMeasuredMZ,
        back_populates="hmdbs")
