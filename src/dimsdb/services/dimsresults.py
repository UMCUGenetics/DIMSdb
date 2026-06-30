"""Service module for managing DIMS result records.

This module provides business logic for performing CRUD operations on
DIMSResults entities, including bulk operations and linking to samples
and measured m/z values.
"""
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

import dimsdb.crud.dimsresults as dimsresults_crud
from dimsdb.models import Sample, MeasuredMZ
from dimsdb.models.dimsresults import DIMSResults
from dimsdb.utils.exceptions import NotFoundError, ExistsError


class DIMSResultsService:
    """Service for managing DIMSResults entities and their relationships.
    
    This service acts as an intermediary between API endpoints and database
    operations, providing higher-level methods for querying, creating, updating,
    and deleting DIMS result records and establishing relationships.
    """

    def __init__(self, session: Session):
        """Initialize the DIMSResultsService.
        
        Args:
            session: SQLModel database session for executing queries.
        """
        self.session = session

    def get_dimsresults_by_id(self, dimsresults_id: int) -> DIMSResults:
        """Retrieve a DIMSResults record by its ID.
        
        Args:
            dimsresults_id: The ID of the DIMSResults record to retrieve.
        
        Returns:
            The DIMSResults record matching the given ID.
        
        Raises:
            NotFoundError: If no DIMSResults record with the given ID exists.
        """
        return dimsresults_crud.select_dimsresults_by_id(self.session, dimsresults_id)

    def create_dimsresults(self, dimsresults: DIMSResults) -> DIMSResults:
        """Create a new DIMSResults record in the database.
        
        Args:
            dimsresults: The DIMSResults object to be created.
        
        Returns:
            The newly created DIMSResults record with database-generated fields.
        
        Raises:
            ExistsError: If a DIMSResults record with the same unique constraints already exists.
        """
        validated_dimsresults = DIMSResults.model_validate(dimsresults)
        try:
            return dimsresults_crud.insert_dimsresults(self.session, validated_dimsresults)
        except IntegrityError:
            raise ExistsError("DIMSResult already exists")

    def create_bulk_dimsresults(self, dimsresults: list[DIMSResults]) -> dict[str, int]:
        """Create multiple DIMSResults records in bulk.
        
        Creates result records in batch and returns a mapping from temporary keys
        to database IDs for tracking purposes.
        
        Args:
            dimsresults: A list of DIMSResults objects to be created.
        
        Returns:
            A dictionary mapping temporary keys to their corresponding database IDs.
        
        Raises:
            ExistsError: If one or more DIMSResults records with conflicting unique constraints already exist.
        """
        try:
            list_dimsresult_dicts = [
                dimsresult.model_dump(exclude_none=True) for dimsresult in dimsresults
            ]
            dimsresults_crud.insert_bulk_dimsresults(self.session, list_dimsresult_dicts)

            temp_keys = [dimsresult.temp_key for dimsresult in dimsresults]

            id_map = dimsresults_crud.select_ids_by_temp_keys(self.session, temp_keys)
            return id_map
        except IntegrityError:
            raise ExistsError("One or more DIMSResults already exist")

    def update_dimsresults(self, dimsresults_id: int, dimsresults: DIMSResults) -> DIMSResults:
        """Update an existing DIMSResults record.
        
        Args:
            dimsresults_id: The ID of the record to update.
            dimsresults: The DIMSResults object with updated fields.
        
        Returns:
            The updated DIMSResults record as stored in the database.
        
        Raises:
            NotFoundError: If no DIMSResults record with the given ID exists.
        """
        db_dimsresults = self.get_dimsresults_by_id(dimsresults_id)
        dimsresults_data = dimsresults.model_dump(exclude_none=True)
        return dimsresults_crud.update_dimsresults(self.session, db_dimsresults, dimsresults_data)

    def delete_dimsresults(self, dimsresults_id: int):
        """Delete a DIMSResults record by its ID.
        
        Args:
            dimsresults_id: The ID of the DIMSResults record to delete.
        
        Raises:
            NotFoundError: If no DIMSResults record with the given ID exists.
        """
        db_dimsresults = self.get_dimsresults_by_id(dimsresults_id)
        dimsresults_crud.delete_dimsresults(self.session, db_dimsresults)

    def get_or_create_dimsresults(self, dimsresults: DIMSResults) -> DIMSResults:
        """Retrieve an existing DIMSResults or create it if it does not exist.
        
        Args:
            dimsresults: The DIMSResults object to get or create.
        
        Returns:
            The existing or newly created DIMSResults record.
        """
        try:
            return self.get_dimsresults_by_id(dimsresults.id)
        except NotFoundError:
            return self.create_dimsresults(dimsresults)

    def link_sample_to_dimsresults(self, dimsresults: DIMSResults, sample: Sample) -> DIMSResults:
        """Link a Sample to a DIMSResults record.
        
        Associates a sample with a result by linking them together. If the sample
        is already linked, returns without modification.
        
        Args:
            dimsresults: The DIMSResults record to link to.
            sample: The Sample record to associate with the result.
        
        Returns:
            The DIMSResults record with the sample linked (if not already linked).
        """
        if sample in dimsresults.samples:
            return dimsresults

        return dimsresults_crud.link_sample(self.session, dimsresults, sample)

    def link_measuredmz_to_dimsresults(self, dimsresults: DIMSResults, measuredmz: MeasuredMZ) -> DIMSResults:
        """Link a MeasuredMZ to a DIMSResults record.
        
        Associates a measured m/z value with a result by linking them together.
        If the measured m/z is already linked, returns without modification.
        
        Args:
            dimsresults: The DIMSResults record to link to.
            measuredmz: The MeasuredMZ record to associate with the result.
        
        Returns:
            The DIMSResults record with the measured m/z linked (if not already linked).
        """
        if measuredmz in dimsresults.measuredmzs:
            return dimsresults

        return dimsresults_crud.link_measuredmz(self.session, dimsresults, measuredmz)
