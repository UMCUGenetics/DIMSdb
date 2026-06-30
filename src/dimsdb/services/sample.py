"""Service layer for Sample model operations.

This module provides the SampleService class which wraps CRUD operations
for the `Sample` model using the repository/CRUD functions in
`dimsdb.crud.sample`. The service translates lower-level exceptions
into domain-level exceptions and performs lightweight validation or
transformation when necessary.

Example:
    service = SampleService(session)
    sample = service.get_sample_by_id('SAMPLE_1')

The service methods raise `dimsdb.utils.exceptions.NotFoundError` when a
requested sample does not exist and `ExistsError` when attempting to
create a sample that already exists.
"""

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

import dimsdb.crud.sample as sample_crud
from dimsdb.models import Patient, DIMSRun
from dimsdb.models.sample import Sample
from dimsdb.utils.exceptions import NotFoundError, ExistsError


class SampleService:
    """High-level operations for Sample entities.

    The service is a thin layer around the CRUD functions in
    `dimsdb.crud.sample`. It is responsible for:

    - Performing minor validation (via the Pydantic/SQLModel model)
    - Converting database/detail exceptions to domain exceptions
    - Coordinating multi-step operations (e.g. get-or-create)

    Attributes:
        session: An active SQLModel/SQLAlchemy `Session` used for
            database operations.
    """

    def __init__(self, session: Session):
        """Create a SampleService bound to a database session.

        Args:
            session: An active `sqlmodel.Session` used to run queries.
        """
        self.session = session

    def get_sample_by_id(self, sample_id: str) -> Sample:
        """Retrieve a Sample by its identifier.

        Args:
            sample_id: The unique identifier of the sample to retrieve.

        Returns:
            The matching `Sample` instance.
        """
        return sample_crud.select_sample_by_id(self.session, sample_id)

    def create_sample(self, sample: Sample) -> Sample:
        """Create a new Sample in the database.

        The provided `sample` object is validated using `Sample.model_validate`
        before being passed to the CRUD insert function. Integrity errors
        (e.g. uniqueness violations) are converted to `ExistsError`.

        Args:
            sample: A `Sample` instance to insert.

        Returns:
            The inserted `Sample` as returned by the CRUD layer.

        Raises:
            ExistsError: If a sample with the same identity already exists.
        """
        validated_sample = Sample.model_validate(sample)
        try:
            return sample_crud.insert_sample(self.session, validated_sample)
        except IntegrityError:
            raise ExistsError("Sample already exists")

    def update_sample(self, sample_id: str, sample: Sample) -> Sample:
        """Update an existing Sample's fields.

        The method fetches the existing database sample, builds a dictionary
        of fields to update (excluding None values) and delegates to the
        CRUD layer.

        Args:
            sample_id: Identifier of the sample to update.
            sample: A `Sample` instance containing updated values. Fields
                set to None are ignored.

        Returns:
            The updated `Sample` instance as returned by the CRUD layer.
        """
        db_sample = self.get_sample_by_id(sample_id)
        sample_data = sample.model_dump(exclude_none=True)
        return sample_crud.update_sample(self.session, db_sample, sample_data)

    def delete_sample(self, sample_id: str):
        """Delete a Sample by id.

        Args:
            sample_id: Identifier of the sample to delete.

        Raises:
            dimsdb.utils.exceptions.NotFoundError: If the sample does not exist.
        """
        db_sample = self.get_sample_by_id(sample_id)
        sample_crud.delete_sample(self.session, db_sample)

    def get_or_create_sample(self, sample: Sample) -> Sample:
        """Return an existing Sample or create it if missing.

        Attempts to fetch a sample using `sample.sample_id`. If not found,
        creates a new record.

        Args:
            sample: A `Sample` instance to lookup or create.

        Returns:
            The existing or newly created `Sample`.
        """
        try:
            return self.get_sample_by_id(sample.sample_id)
        except NotFoundError:
            return self.create_sample(sample)

    def link_patient_to_sample(self, sample: Sample, patient: Patient) -> Sample:
        if patient in sample.patients:
            return sample

        return sample_crud.link_patient(self.session, sample, patient)
    
    def link_dimsrun_to_sample(self, sample: Sample, dimsrun: DIMSRun) -> Sample:
        if dimsrun in sample.dimsruns:
            return sample

        return sample_crud.link_dimsrun(self.session, sample, dimsrun)
    