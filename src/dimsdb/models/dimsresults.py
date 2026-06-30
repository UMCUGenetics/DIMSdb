"""Models for DIMS measurement results.

This module defines the DIMSResults model for storing quantitative measurement
data (intensities and z-scores) from DIMS analyses.
"""
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship
from dimsdb.models.base import BaseModel
from dimsdb.models.linktables import DIMSResultsSample, DIMSResultsMeasuredMZ

if TYPE_CHECKING:
    from dimsdb.models.sample import Sample
    from dimsdb.models.measuredmz import MeasuredMZ


class DIMSResults(BaseModel, table=True):
    """Quantitative measurement results from a DIMS analysis.
    
    Stores per-sample intensities and normalized z-scores produced by the DIMS
    pipeline. Results are linked to samples and measured m/z values through
    junction tables to support many-to-many relationships.
    
    Attributes:
        id: Primary key for the result record.
        temp_key: Temporary key for tracking results during bulk operations.
        intensity: Measured intensity value for the feature in the sample.
        z_score: Z-score or normalized value when available.
        samples: List of Sample records associated with this result.
        measuredmzs: List of MeasuredMZ records associated with this result.
    """

    id: int = Field(default=None, primary_key=True)
    temp_key: str = Field(default=None, nullable=False, index=True)

    intensity: float | None = None
    z_score: float | None = None

    samples: list["Sample"] = Relationship(
        link_model=DIMSResultsSample,
        back_populates="dimsresults")
    measuredmzs: list["MeasuredMZ"] = Relationship(
        link_model=DIMSResultsMeasuredMZ,
        back_populates="dimsresults")
