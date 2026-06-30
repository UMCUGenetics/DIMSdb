"""Link tables used to express many-to-many relationships between models.

This module contains lightweight association tables implemented as
SQLModel models with ``table=True``. They are used by the main ORM
models in ``dimsdb.models.models`` to declare many-to-many relationships
via the ``Relationship`` helper.

Link tables are minimal and only contain foreign keys (and occasionally
small auxiliary fields) to connect two primary entities. Do not change
column names or primary key definitions without updating migrations and
any code that constructs or queries these association tables.
"""

from typing import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from dimsdb.models.hmdb import HMDB
    from dimsdb.models.measuredmz import MeasuredMZ


class DIMSRunSample(SQLModel, table=True):
    """Link table associating a `Sample` with a `DIMSRun`.

    Attributes:
        sample_id: Foreign key referencing the linked Sample.
        dimsrun_id: Foreign key referencing the linked DIMSRun.
    """
    sample_id: int = Field(default=None, foreign_key="sample.id", primary_key=True)
    dimsrun_id: int = Field(default=None, foreign_key="dimsrun.id", primary_key=True)


class DIMSRunMeasuredMZ(SQLModel, table=True):
    """Association between a `DIMSRun` and a measured m/z value.

    Attributes:
        dimsrun_id: Foreign key referencing the DIMSRun.
        measuredmz_id: Foreign key referencing the MeasuredMZ.
    """
    dimsrun_id: int = Field(default=None, foreign_key="dimsrun.id", primary_key=True)
    measuredmz_id: int = Field(default=None, foreign_key="measuredmz.id", primary_key=True)


class HMDBMeasuredMZ(SQLModel, table=True):
    """Link table connecting HMDB entries to measured m/z values.

    This association may include an auxiliary ``adduct`` field that records
    the adduct type or annotation when available.

    Attributes:
        adduct: Optional adduct annotation.
        hmdb_id: Foreign key referencing the HMDB entry.
        measuredmz_id: Foreign key referencing the MeasuredMZ.
    """
    hmdb_id: int = Field(default=None, foreign_key="hmdb.id", primary_key=True)
    measuredmz_id: int = Field(default=None, foreign_key="measuredmz.id", primary_key=True)
    adduct: int | None = None

    hmdb: "HMDB" = Relationship(back_populates="hmdb_links")
    measuredmz: "MeasuredMZ" = Relationship(back_populates="measuredmz_links")


class DIMSResultsSample(SQLModel, table=True):
    """Association between `DIMSResults` rows and `Sample` objects.

    Attributes:
        sample_id: Foreign key referencing the Sample.
        dimsresults_id: Foreign key referencing the DIMSResults row.
    """
    sample_id: int = Field(default=None, foreign_key="sample.id", primary_key=True)
    dimsresults_id: int = Field(default=None, foreign_key="dimsresults.id", primary_key=True)


class PatientSample(SQLModel, table=True):
    """Link table associating a `Patient` with a `Sample`.

    Attributes:
        patient_id: Foreign key referencing the Patient.
        sample_id: Foreign key referencing the Sample.
    """
    patient_id: int = Field(default=None, foreign_key="patient.id", primary_key=True)
    sample_id: int = Field(default=None, foreign_key="sample.id", primary_key=True)
    
class DIMSResultsMeasuredMZ(SQLModel, table=True):
    
    dimsresults_id: int = Field(default=None, foreign_key="dimsresults.id", primary_key=True)
    measuredmz_id: int = Field(default=None, foreign_key="measuredmz.id", primary_key=True)
