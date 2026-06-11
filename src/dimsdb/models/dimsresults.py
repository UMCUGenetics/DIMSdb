from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import DIMSResultsSample, DIMSResultsMeasuredMZ

if TYPE_CHECKING:
    from dimsdb.models.sample import Sample
    from dimsdb.models.measuredmz import MeasuredMZ

class DIMSResults(BaseModel, table=True):
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

    samples: list["Sample"] = Relationship(
        link_model=DIMSResultsSample,
        back_populates="dimsresults")
    measuredmzs: list["MeasuredMZ"] = Relationship(
        link_model=DIMSResultsMeasuredMZ,
        back_populates="dimsresults")
