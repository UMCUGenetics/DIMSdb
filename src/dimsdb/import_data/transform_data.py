"""Module for transforming imported data into standardized formats.

This module provides functions to standardize column names and data structures
from various data sources to match the database schema.
"""
from pandas import DataFrame


def transform_hmdb_df(hmdb_df: DataFrame) -> DataFrame:
    """Transform HMDB dataframe column names to match database schema.
    
    Renames columns from the raw HMDB import format to match the standardized
    naming conventions used in the database model.
    
    Args:
        hmdb_df: Dataframe containing raw HMDB data with original column names.
    
    Returns:
        The input dataframe with renamed columns following database conventions.
    """
    hmdb_df.rename(
        columns={
            "HMDB_key": "hmdb_key",
            "HMDB_ID": "hmdb_id",
            "sec_HMDB_ID": "sec_hmdb_id",
            "HMDB_name": "name",
            "Chemical_formula": "chem_formula",
            "MNeutral": "theor_mz",
            "descr": "description",
        },
        inplace=True,
    )

    return hmdb_df
