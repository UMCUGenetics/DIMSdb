"""Service module for managing DIMSRun records.

This module provides business logic for performing CRUD operations on DIMSRun
entities, including querying, creating, updating, and deleting runs, as well
as establishing relationships between runs and samples.
"""
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session

import dimsdb.crud.dimsrun as dimsrun_crud
from dimsdb.models.sample import Sample
from dimsdb.models.dimsrun import DIMSRun
from dimsdb.utils.exceptions import NotFoundError, ExistsError


class DIMSRunService:
    """Service for managing DIMSRun entities and their relationships.
    
    This service acts as an intermediary between API endpoints and database
    operations, providing higher-level methods for querying, creating, updating,
    and deleting DIMS run records and establishing relationships with samples.
    """

    def __init__(self, session: Session):
        """Initialize the DIMSRunService.
        
        Args:
            session: SQLModel database session for executing queries.
        """
        self.session = session

    def get_dimsrun_by_runname(self, runname: str) -> DIMSRun | None:
        """Retrieve a DIMSRun record by its run name.
        
        Args:
            runname: The unique run name identifier.
        
        Returns:
            The DIMSRun record if found, otherwise None.
        
        Raises:
            NotFoundError: If no DIMSRun record with the given run name exists.
        """
        try:
            return dimsrun_crud.select_dimsrun_by_runname(self.session, runname)
        except NoResultFound:
            raise NotFoundError("DIMSRun not found")

    def create_dimsrun(self, dimsrun: DIMSRun) -> DIMSRun:
        """Create a new DIMSRun record in the database.
        
        Args:
            dimsrun: The DIMSRun object to be created.
        
        Returns:
            The newly created DIMSRun record with database-generated fields.
        
        Raises:
            ExistsError: If a DIMSRun record with the same unique constraints already exists.
        """
        validated_dimsrun = DIMSRun.model_validate(dimsrun)
        try:
            return dimsrun_crud.insert_dimsrun(self.session, validated_dimsrun)
        except IntegrityError:
            raise ExistsError("DIMSRun already exists")

    def update_dimsrun(self, run_id: str, dimsrun: DIMSRun) -> DIMSRun:
        """Update an existing DIMSRun record.
        
        Args:
            run_id: The unique identifier of the run to update.
            dimsrun: The DIMSRun object with updated fields.
        
        Returns:
            The updated DIMSRun record as stored in the database.
        
        Raises:
            NotFoundError: If no DIMSRun record with the given run ID exists.
        """
        db_dimsrun = self.get_dimsrun_by_runname(run_id)
        dimsrun_data = dimsrun.model_dump(exclude_none=True)
        return dimsrun_crud.update_dimsrun(self.session, db_dimsrun, dimsrun_data)

    def delete_dimsrun(self, run_id: str) -> None:
        """Delete a DIMSRun record by its ID.
        
        Args:
            run_id: The unique identifier of the run to delete.
        
        Raises:
            NotFoundError: If no DIMSRun record with the given run ID exists.
        """
        db_dimsrun = self.get_dimsrun_by_runname(run_id)
        dimsrun_crud.delete_dimsrun(self.session, db_dimsrun)

    def get_or_create_dimsrun(self, dimsrun: DIMSRun) -> DIMSRun:
        """Retrieve an existing DIMSRun or create it if it does not exist.
        
        Args:
            dimsrun: The DIMSRun object to get or create.
        
        Returns:
            The existing or newly created DIMSRun record.
        """
        try:
            return self.get_dimsrun_by_runname(dimsrun.run_id)
        except NotFoundError:
            return self.create_dimsrun(dimsrun)

    def link_sample_to_dimsrun(self, dimsrun: DIMSRun, sample: Sample) -> DIMSRun:
        """Link a Sample to a DIMSRun.
        
        Associates a sample with a run. If the sample is already linked,
        returns without modification.
        
        Args:
            dimsrun: The DIMSRun to link the sample to.
            sample: The Sample to link to the run.
        
        Returns:
            The DIMSRun record with the sample linked (if not already linked).
        """
        if sample in dimsrun.samples:
            return dimsrun

        return dimsrun_crud.link_samples(self.session, dimsrun, sample)
