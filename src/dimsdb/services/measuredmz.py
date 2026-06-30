"""Service module for managing Measured M/Z data.

This module provides business logic for performing CRUD operations on
MeasuredMZ entities, including bulk operations and linking to DIMSRun records.
"""
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

import dimsdb.crud.measuredmz as measuredmz_crud
from dimsdb.models.measuredmz import MeasuredMZ
from dimsdb.models.dimsrun import DIMSRun
from dimsdb.utils.exceptions import NotFoundError, ExistsError


class MeasuredMZService:
    """Service for managing MeasuredMZ entities and their relationships.
    
    This service acts as an intermediary between API endpoints and database
    operations, providing higher-level methods for querying, creating, updating,
    and deleting MeasuredMZ records.
    """
    def __init__(self, session: Session):
        """Initialize the MeasuredMZService.
        
        Args:
            session: SQLModel database session for executing queries.
        """
        self.session = session

    def get_measured_mz_by_id(self, measured_mz_id: int) -> MeasuredMZ:
        """Retrieve a MeasuredMZ record by its ID.
        
        Args:
            measured_mz_id: The ID of the MeasuredMZ record to retrieve.
        
        Returns:
            The MeasuredMZ record matching the given ID.
        
        Raises:
            NotFoundError: If no MeasuredMZ record with the given ID exists.
        """
        return measuredmz_crud.select_measuredmz_by_id(self.session, measured_mz_id)

    def get_measured_mz_by_mz(self, mz_start: float, mz_end: float) -> list[MeasuredMZ]:
        """Retrieve MeasuredMZ records within a specified m/z range.
        
        Args:
            mz_start: The lower bound of the m/z range (inclusive).
            mz_end: The upper bound of the m/z range (inclusive).
        
        Returns:
            A list of MeasuredMZ records within the specified range.
        """
        return measuredmz_crud.select_measuredmz_by_mz(self.session, mz_start, mz_end)

    def create_measured_mz(self, measured_mz: MeasuredMZ) -> MeasuredMZ:
        """Create a new MeasuredMZ record in the database.
        
        Args:
            measured_mz: The MeasuredMZ object to be created.
        
        Returns:
            The newly created MeasuredMZ record with database-generated fields.
        
        Raises:
            ExistsError: If a MeasuredMZ record with the same unique constraints already exists.
        """
        validated_measured_mz = MeasuredMZ.model_validate(measured_mz)
        try:
            return measuredmz_crud.insert_measuredmz(self.session, validated_measured_mz)
        except IntegrityError:
            raise ExistsError("Measured MZ already exists")

    def create_measured_mzs_in_bulk(self, measured_mzs: list[MeasuredMZ]) -> None:
        """Create multiple MeasuredMZ records in bulk.
        
        Args:
            measured_mzs: A list of MeasuredMZ objects to be created.
        
        Raises:
            ExistsError: If one or more MeasuredMZ records with conflicting unique constraints already exist.
        """
        try:
            list_measured_mz_dicts = [
                measured_mz.model_dump(exclude_none=True) for measured_mz in measured_mzs
            ]
            measuredmz_crud.insert_bulk_measuredmzs(self.session, list_measured_mz_dicts)
        except IntegrityError:
            raise ExistsError("One or more Measured MZs already exist")

    def create_id_map_measuredmzs(self, measured_mzs: list[MeasuredMZ]) -> dict[str, int]:
        """Create a mapping from temporary keys to database IDs for given MeasuredMZ records.
        
        Args:
            measured_mzs: A list of MeasuredMZ objects containing temporary keys.
        
        Returns:
            A dictionary mapping temporary keys to their corresponding database IDs.
        """
        temp_keys = [measured_mz.temp_key for measured_mz in measured_mzs]
        id_map = measuredmz_crud.select_ids_by_temp_keys(self.session, temp_keys)
        return id_map

    def update_measured_mz(self, measured_mz: MeasuredMZ) -> MeasuredMZ:
        """Update an existing MeasuredMZ record.
        
        Args:
            measured_mz: The MeasuredMZ object with updated fields.
        
        Returns:
            The updated MeasuredMZ record as stored in the database.
        
        Raises:
            NotFoundError: If no MeasuredMZ record with the given ID exists.
        """
        db_measured_mz = self.get_measured_mz_by_id(measured_mz.id)
        measured_mz_data = measured_mz.model_dump(exclude_none=True)
        return measuredmz_crud.update_measuredmz(self.session, db_measured_mz, measured_mz_data)

    def delete_measured_mz(self, measured_mz_id: int):
        """Delete a MeasuredMZ record by its ID.
        
        Args:
            measured_mz_id: The ID of the MeasuredMZ record to delete.
        
        Raises:
            NotFoundError: If no MeasuredMZ record with the given ID exists.
        """
        db_measured_mz = self.get_measured_mz_by_id(measured_mz_id)
        measuredmz_crud.delete_measuredmz(self.session, db_measured_mz)

    def get_or_create_measured_mz(self, measured_mz: MeasuredMZ) -> MeasuredMZ:
        """Retrieve an existing MeasuredMZ or create it if it does not exist.
        
        Args:
            measured_mz: The MeasuredMZ object to get or create.
        
        Returns:
            The existing or newly created MeasuredMZ record.
        """
        try:
            return self.create_measured_mz(self.session, measured_mz)
        except ExistsError:
            return self.get_measured_mz_by_id(measured_mz.id)

    def link_dimsrun_to_measuredmzs(self, measuredmz: MeasuredMZ, dimsrun: DIMSRun) -> MeasuredMZ:
        """Link a DIMSRun to a MeasuredMZ record.
        
        Args:
            measuredmz: The MeasuredMZ record to link to.
            dimsrun: The DIMSRun record to associate with the MeasuredMZ.
        
        Returns:
            The MeasuredMZ record with the DIMSRun linked (if not already linked).
        """
        if dimsrun in measuredmz.dimsruns:
            return measuredmz

        return measuredmz_crud.link_dimsrun(self.session, measuredmz, dimsrun)