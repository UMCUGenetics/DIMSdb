"""Module for retrieving and extracting sample information from data structures.

This module provides utility functions to identify and extract sample identifiers
from dataframes and related data structures.
"""


def get_samples_run(peakgroup_df_cols):
    """Extract sample identifiers from peakgroup dataframe column names.
    
    Filters column names to identify sample identifiers that start with "C" or "P"
    and excludes z-score columns. These column names represent individual samples
    in a DIMS run.
    
    Args:
        peakgroup_df_cols: Column names from the peakgroup dataframe.
    
    Returns:
        A list of sample identifiers found in the column names.
    """
    sample_ids = [
        col for col in peakgroup_df_cols
        if (col.startswith(("C", "P")) and not col.endswith("_Zscore"))
    ]

    return sample_ids
