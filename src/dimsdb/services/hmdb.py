"""Service module for managing HMDB records.

This module provides business logic for performing CRUD operations on HMDB
(Human Metabolome Database) entities, including querying by various identifiers,
creating and updating records, and establishing relationships to measured m/z values.
"""
from pathlib import Path

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session

import dimsdb.crud.hmdb as hmdb_crud
from dimsdb.models import MeasuredMZ
from dimsdb.models.hmdb import HMDB
from dimsdb.import_data.parse_files import parse_hmdb_rdata_file
from dimsdb.import_data.transform_data import transform_hmdb_df
from dimsdb.utils.exceptions import NotFoundError


class HMDBService:
    """Service for managing HMDB entities and their relationships.
    
    This service acts as an intermediary between API endpoints and database
    operations, providing higher-level methods for querying, creating, updating,
    and deleting HMDB records and establishing relationships with measured m/z values.
    """

    def __init__(self, session: Session):
        """Initialize the HMDBService.
        
        Args:
            session: SQLModel database session for executing queries.
        """
        self.session = session

    def get_hmdb_by_hmdb_id(self, hmdb_id: str) -> HMDB:
        """Retrieve an HMDB record by its primary HMDB ID.
        
        Args:
            hmdb_id: The primary HMDB identifier.
        
        Returns:
            The HMDB record matching the given ID.
        
        Raises:
            NotFoundError: If no HMDB record with the given ID exists.
        """
        try:
            return hmdb_crud.select_hmdb_by_hmdb_id(self.session, hmdb_id)
        except NoResultFound:
            raise NotFoundError(f"HMDB with ID {hmdb_id} not found")

    def get_hmdbs_by_list_hmdb_ids(self, list_hmdb_ids: list[str]) -> list[HMDB]:
        """Retrieve multiple HMDB records by a list of HMDB IDs.
        
        Args:
            list_hmdb_ids: List of primary HMDB identifiers.
        
        Returns:
            A list of HMDB records matching the given IDs.
        
        Raises:
            NotFoundError: If no HMDB records are found for the given IDs.
        """
        try:
            return hmdb_crud.select_hmdbs_by_hmdb_ids(self.session, list_hmdb_ids)
        except NoResultFound:
            raise NotFoundError(f"HMDB with IDs {list_hmdb_ids} not found")

    def get_hmdbs_by_hmdb_key(self, hmdb_key: str) -> list[HMDB]:
        """Retrieve HMDB records by an HMDB key.
        
        Args:
            hmdb_key: The HMDB key to search for.
        
        Returns:
            A list of HMDB records matching the given key.
        
        Raises:
            NotFoundError: If no HMDB records are found for the given key.
        """
        try:
            return hmdb_crud.select_hmdbs_by_hmdb_key(self.session, hmdb_key)
        except NoResultFound:
            raise NotFoundError(f"HMDBs with key {hmdb_key} not found")

    def get_hmdbs_by_sec_hmdb_id(self, hmdb_id: str) -> list[HMDB]:
        """Retrieve HMDB records by a secondary HMDB ID.
        
        Args:
            hmdb_id: The secondary HMDB identifier.
        
        Returns:
            A list of HMDB records matching the given secondary ID.
        
        Raises:
            NotFoundError: If no HMDB records are found for the given secondary ID.
        """
        try:
            return hmdb_crud.select_hmdb_by_sec_hmdb_id(self.session, hmdb_id)
        except NoResultFound:
            raise NotFoundError(f"HMDBs with secondary ID {hmdb_id} not found")

    def create_hmdb(self, hmdb: HMDB) -> HMDB:
        """Create a new HMDB record in the database.
        
        Validates the incoming model before insertion and raises an exception
        if a record with the same unique constraints already exists.
        
        Args:
            hmdb: The HMDB object to be created.
        
        Returns:
            The newly created HMDB record with database-generated fields.
        
        Raises:
            ValueError: If an integrity error occurs (e.g., duplicate primary key).
        """
        validated_hmdb = HMDB.model_validate(hmdb)
        try:
            return hmdb_crud.insert_hmdb(self.session, validated_hmdb)
        except IntegrityError:
            raise ValueError(f"HMDB with ID {hmdb.hmdb_id} already exists")

    def create_hmdb_in_bulk(self, hmdbs: list[HMDB]) -> None:
        """Create multiple HMDB records in bulk.
        
        Args:
            hmdbs: A list of HMDB objects to be created.
        """
        hmdb_dict = [
            hmdb.model_dump(exclude_unset=True) for hmdb in hmdbs
        ]

        hmdb_crud.insert_hmdb_in_bulk(self.session, hmdb_dict)

    def update_hmdb(self, hmdb_id: str, hmdb: HMDB) -> HMDB:
        """Update an existing HMDB record.
        
        Retrieves the existing record and applies the provided updates,
        including only fields that were explicitly set.
        
        Args:
            hmdb_id: The primary HMDB ID of the record to update.
            hmdb: The HMDB object with updated fields.
        
        Returns:
            The updated HMDB record as stored in the database.
        
        Raises:
            NotFoundError: If no HMDB record with the given ID exists.
        """
        db_hmdb = self.get_hmdb_by_hmdb_id(hmdb_id)
        hmdb_data = hmdb.model_dump(exclude_unset=True)
        return hmdb_crud.update_hmdb(self.session, db_hmdb, hmdb_data)

    def delete_hmdb(self, hmdb_id: str) -> None:
        """Delete an HMDB record by its ID.
        
        Args:
            hmdb_id: The primary HMDB ID of the record to delete.
        
        Raises:
            NotFoundError: If no HMDB record with the given ID exists.
        """
        db_hmdb = self.get_hmdb_by_hmdb_id(hmdb_id)
        hmdb_crud.delete_hmdb(self.session, db_hmdb)

    def insert_hmdb_table(self, file_path: Path) -> None:
        """Load and insert HMDB data from an RData file.
        
        Parses an RData file containing HMDB data, transforms it to match
        the database schema, and inserts all records.
        
        Args:
            file_path: Path to the RData file containing HMDB data.
        
        Raises:
            Exception: Re-raises any exception that occurs during parsing or insertion.
        """
        hmdb_df = parse_hmdb_rdata_file(file_path)
        hmdb_df = transform_hmdb_df(hmdb_df)

        try:
            hmdb_crud.insert_hmdb_table(self.session, hmdb_df)
        except Exception as e:
            raise e

    def get_or_create_hmdb(self, hmdb: HMDB) -> HMDB:
        """Retrieve an existing HMDB or create it if it does not exist.
        
        Args:
            hmdb: The HMDB object to get or create.
        
        Returns:
            The existing or newly created HMDB record.
        """
        try:
            return self.get_hmdb_by_hmdb_id(hmdb.hmdb_id)
        except NotFoundError:
            return self.create_hmdb(hmdb)

    def link_measuredmz_to_hmdb(self, hmdb: HMDB, measuredmz: MeasuredMZ, adduct: int) -> None:
        """Link a MeasuredMZ to an HMDB record with adduct information.
        
        Associates a measured m/z value with an HMDB record, including the adduct
        information that describes how the compound ionized.
        
        Args:
            hmdb: The HMDB record to link to.
            measuredmz: The MeasuredMZ to associate with the HMDB.
            adduct: The adduct type or number representing the ionization form.
        """
        hmdb_crud.link_measuredmz(self.session, hmdb, measuredmz, adduct)
