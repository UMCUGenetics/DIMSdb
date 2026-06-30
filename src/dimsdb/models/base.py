"""Base model class for all SQLModel entities.

This module provides the base class that all domain models inherit from,
establishing common database model conventions and configurations.
"""
from sqlmodel import SQLModel


class BaseModel(SQLModel):
    """Base class for all domain models.
    
    All SQLModel entities inherit from this class to ensure consistent
    database model structure and conventions across the codebase.
    """
    pass
