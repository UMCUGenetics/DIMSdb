"""Service module for managing junction table relationships.

This module provides a service layer for bulk operations on junction tables
that establish many-to-many relationships between entities.
"""
from sqlmodel import Session

import dimsdb.crud.linktables as linktables_crud


class LinktablesService:
    """Service for managing bulk link operations across junction tables.
    
    Provides a service-layer interface for creating relationships between
    entities by inserting link records into junction tables.
    """

    def __init__(self, session: Session):
        """Initialize the LinktablesService.
        
        Args:
            session: SQLModel database session for executing operations.
        """
        self.session = session

    def create_links_in_bulk(self, model, link_list: list[dict]) -> None:
        """Bulk create link records in a junction table.
        
        Inserts multiple relationship records into the specified junction table
        in a single batch operation.
        
        Args:
            model: SQLModel class representing the junction table.
            link_list: List of dictionaries containing the link data to insert.
        """
        linktables_crud.insert_bulk_links(self.session, model, link_list)
