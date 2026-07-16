"""Module for parsing various data file formats used in DIMS runs.

This module provides functions to parse RData files, version logs, and workflow
parameters to extract data structures and metadata for ingestion into the database.
"""
import re
import rdata
import pyreadr
import pandas as pd
from pandas import DataFrame
from pathlib import Path

def parse_hmdb_rdata_file(file_path: Path) -> DataFrame:
    """Parse an RData file containing HMDB (Human Metabolome Database) data.
    
    Reads and converts an R data file to a pandas DataFrame using the rdata package.
    
    Args:
        file_path: Path to the RData file to parse.
    
    Returns:
        A dataframe containing the HMDB data extracted from the RData file.
    
    Raises:
        FileNotFoundError: If the file does not exist at the specified path.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    parsed_hmdb_file = rdata.parser.parse_file(file_path)
    hmdb_df = rdata.conversion.convert(parsed_hmdb_file, default_encoding="utf8")
    hmdb_df = pd.DataFrame(hmdb_df.get("dimspect_df"))
    return hmdb_df


def parse_rdata_file(file: str) -> DataFrame:
    """Parse an RData file and return the first dataframe contained within.
    
    Uses the pyreadr package to read R data files and extracts the first
    dataframe object found in the file.
    
    Args:
        file: Path to the RData file to parse.
    
    Returns:
        A dataframe containing the parsed RData file content.
    """
    result = pyreadr.read_r(file)

    df_name = list(result.keys())[0]

    rdata_df = result.get(df_name)

    return rdata_df


def parse_version_log_file(file_path, repo_name="DIMS") -> str | None:
    """Extract repository version tag from a workflow log file.
    
    Searches through a log file to find a repository name entry and extracts
    the associated version tag from the following line.
    
    Args:
        file_path: Path to the version log file.
        repo_name: Name of the repository to search for (default: "DIMS").
    
    Returns:
        The version tag string if found, otherwise None.
    """
    lines = open(file_path, "r").readlines()

    for i, line in enumerate(lines):
        if line.strip() == repo_name:
            if i + 1 < len(lines):
                commit_line = lines[i + 1]
                match = re.search(r'v\s*([^\s,]+)', commit_line)
                if match:
                    return match.group(1)
            break

    return None


def parse_run_parameters_file(file_path) -> DataFrame:
    """Extract workflow run parameters from a tab-separated parameters file.
    
    Reads a workflow parameters file and filters to keep only specified parameter
    columns (email, matrix, nr_replicates, ppm, resolution, date).
    
    Args:
        file_path: Path to the workflow parameters file.
    
    Returns:
        A dataframe containing the filtered run parameters.
    """
    parameter_df = pd.read_table(file_path, delimiter="\t")
    cols_to_keep = [
        "email",
        "matrix",
        "nr_replicates",
        "ppm",
        "resolution",
        "date"
    ]
    pattern = "|".join(cols_to_keep)
    parameter_df = parameter_df[parameter_df["param"].str.contains(pattern, case=False, na=False)]
    return parameter_df
