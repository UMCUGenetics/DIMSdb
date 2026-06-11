from pathlib import Path

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session

import dimsdb.crud.hmdb as hmdb_crud
from dimsdb.models.hmdb import HMDB
from dimsdb.import_data.hmdb_parser import parse_hmdb_rdata_file
from dimsdb.import_data.hmdb_transformer import transform_hmdb_df
from dimsdb.utils.exceptions import NotFoundError

class HMDBService:
    def __init__(self, session: Session):
        """Initialize the service with a database session.

        Args:
            session: The active database session used for CRUD operations.
        """
        self.session = session

    def get_hmdb_by_hmdb_id(self, hmdb_id: str) -> HMDB:
        """Retrieve a single HMDB record by its primary HMDB ID.

        Args:
            hmdb_id: The primary HMDB ID of the desired record.

        Returns:
            The found HMDB model.

        Raises:
            ValueError: If no record is found for the given ID.
        """
        try:
            return hmdb_crud.select_hmdb_by_hmdb_id(self.session, hmdb_id)
        except NoResultFound:
            raise NotFoundError(f"HMDB with ID {hmdb_id} not found")

    def get_hmdbs_by_hmdb_key(self, hmdb_key: str) -> list[HMDB]:
        """Find HMDB records by an HMDB key.

        Args:
            hmdb_key: The key to search for. Behavior for partial matches
                depends on the underlying CRUD implementation.

        Returns:
            A list of matching HMDB models.

        Raises:
            ValueError: If no records are found for the given key.
        """
        try:
            return hmdb_crud.select_hmdbs_by_hmdb_key(self.session, hmdb_key)
        except NoResultFound:
            raise NotFoundError(f"HMDBs with key {hmdb_key} not found")

    def get_hmdbs_by_sec_hmdb_id(self, hmdb_id: str) -> list[HMDB]:
        """Find HMDB records by a secondary HMDB ID.

        Args:
            hmdb_id: The secondary HMDB ID to search for.

        Returns:
            A list of matching HMDB models.

        Raises:
            ValueError: If no records are found for the given secondary ID.
        """
        try:
            return hmdb_crud.select_hmdb_by_sec_hmdb_id(self.session, hmdb_id)
        except NoResultFound:
            raise NotFoundError(f"HMDBs with secondary ID {hmdb_id} not found")

    def create_hmdb(self, hmdb: HMDB) -> HMDB:
        """Create a new HMDB record in the database.

        The incoming model is validated via ``HMDB.model_validate`` before the
        insert is performed by the CRUD layer.

        Args:
            hmdb: The HMDB model containing data for the new record.

        Returns:
            The created HMDB model as returned by the CRUD layer.

        Raises:
            ValueError: If an integrity error occurs, for example when trying
                to insert a record with an existing primary key.
        """
        validated_hmdb = HMDB.model_validate(hmdb)
        try:
            return hmdb_crud.insert_hmdb(self.session, validated_hmdb)
        except IntegrityError:
            raise ValueError(f"HMDB with ID {hmdb.hmdb_id} already exists")

    def update_hmdb(self, hmdb_id: str, hmdb: HMDB) -> HMDB:
        """Update an existing HMDB record.

        The existing record is retrieved, a dict containing only the fields
        that were set on the provided model is prepared, and the update is
        delegated to the CRUD layer.

        Args:
            hmdb_id: The primary HMDB ID of the record to update.
            hmdb: An HMDB model containing the subset of fields to update.

        Returns:
            The updated HMDB model.
        """
        db_hmdb = self.get_hmdb_by_hmdb_id(hmdb_id)
        hmdb_data = hmdb.model_dump(exclude_unset=True)
        return hmdb_crud.update_hmdb(self.session, db_hmdb, hmdb_data)

    def delete_hmdb(self, hmdb_id: str) -> None:
        """Delete an HMDB record from the database.

        Args:
            hmdb_id: The primary HMDB ID of the record to delete.

        Returns:
            None
        """
        db_hmdb = self.get_hmdb_by_hmdb_id(hmdb_id)
        hmdb_crud.delete_hmdb(self.session, db_hmdb)

    def insert_hmdb_table(self, file_path: Path) -> None:
        hmdb_df = parse_hmdb_rdata_file(file_path)
        hmdb_df = transform_hmdb_df(hmdb_df)

        try:
            hmdb_crud.insert_hmdb_table(self.session, hmdb_df)
        except Exception as e:
            raise e
