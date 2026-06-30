"""Utility functions for model transformations.

This module provides helper functions for common data transformations used
in model definitions and data processing workflows.
"""


def map_to_upper(value: str) -> str:
    """Convert a string value to uppercase.
    
    Args:
        value: The string to convert.
    
    Returns:
        The input string converted to uppercase.
    """
    return value.upper()
