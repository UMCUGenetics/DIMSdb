from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import HMDBMeasuredMZ, DIMSResultsMeasuredMZ, DIMSRunMeasuredMZ

if TYPE_CHECKING:
    from dimsdb.models.hmdb import HMDB
    from dimsdb.models.dimsresults import DIMSResults
    from dimsdb.models.dimsrun import DIMSRun

class MeasuredMZ(BaseModel, table=True):
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

    dimsruns: list["DIMSRun"] = Relationship(
        link_model=DIMSRunMeasuredMZ,
        back_populates="measuredmzs")
    hmdbs: list["HMDB"] = Relationship(
        link_model=HMDBMeasuredMZ,
        back_populates="measuredmzs")
    dimsresults: list["DIMSResults"] = Relationship(
        link_model=DIMSResultsMeasuredMZ,
        back_populates="measuredmzs")
