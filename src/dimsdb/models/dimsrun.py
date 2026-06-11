from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import DIMSRunSample, DIMSRunMeasuredMZ

if TYPE_CHECKING:
    from dimsdb.models.sample import Sample
    from dimsdb.models.measuredmz import MeasuredMZ

class DIMSRun(BaseModel, table=True):
    """Metadata representing a single DIMS experimental run.

    The model captures run-level configuration (name, date, instrument
    settings) and relationships to measured m/z values and samples.

    Attributes:
        id: Primary key for the run.
        name: Human-readable name of the run.
        date: Date of the DIMS run.
        num_replicates: Optional number of replicates.
        ppm: Parts-per-million tolerance used during peak annotation.
        resolution: Instrument resolution setting.
        matrix: Biological matrix (e.g., plasma, urine) used for the run.
        email: Contact email of the submitter.
        pipeline_version: Version of the processing pipeline that produced outputs.
        samples: Samples measured in this run.
        measuredmzs: MeasuredMZ entries recorded for this run.
    """

    id: int = Field(primary_key=True)
    run_id: str
    date: date
    num_replicates: int | None = None
    ppm: int = None
    resolution: int = None
    matrix: str = None
    email: str = None
    pipeline_version: str | None = None

    samples: list["Sample"] = Relationship(
        link_model=DIMSRunSample,
        back_populates="dimsruns")
    measuredmzs: list["MeasuredMZ"] = Relationship(
        link_model=DIMSRunMeasuredMZ,
        back_populates="dimsruns")
