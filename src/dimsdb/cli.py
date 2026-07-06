"""Command-line interface for DIMSdb management and operations.

This module provides CLI commands for common administrative and data import tasks,
including database initialization, server startup, DIMS data ingestion, and HMDB
table population.
"""
from pathlib import Path
from typing import Annotated
import typer
import uvicorn

from dimsdb.db.session import create_db_and_tables, SessionFactory
from dimsdb.services.hmdb import HMDBService
from dimsdb.services.ingestion import IngestionService

# Setup Typer CLI
cli = typer.Typer(no_args_is_help=True)

@cli.command("init")
def init_db() -> None:
    """Initialize the database and create all required tables.
    
    This command sets up the database schema based on the defined models,
    creating all necessary tables and relationships.
    """
    create_db_and_tables()

@cli.command("run")
def run_server() -> None:
    """Start the FastAPI development server.
    
    Launches the Uvicorn ASGI server with auto-reload enabled, allowing
    the API to respond to HTTP requests.
    """
    uvicorn.run("DIMSdb.main:app", reload=True)

@cli.command("import")
def import_dims(
        directory: Annotated[
            Path,
            typer.Argument(
                ...,
                exists=True,
                file_okay=False,
                dir_okay=True,
                readable=True,
                help="Directory to import DIMS data from"
            )
        ]
) -> None:
    """Import DIMS run data from a directory.
    
    Parses and ingests a DIMS run directory, loading experimental metadata,
    samples, results, and relationships into the database. Requires a directory
    containing the complete DIMS run output structure.
    
    Args:
        directory: Path to the DIMS run directory containing data files.
    """
    print(f"{directory}")
    with SessionFactory() as session:
        IngestionService(session).ingest_run(directory, 10000)

@cli.command("hmdb")
def fill_hmdb_table(
        file: Annotated[
            Path,
            typer.Argument(
                ...,
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                help="HMDB input RData file"
            )
        ]
) -> None:
    """Populate the HMDB table from an RData file.
    
    Parses an R data file containing HMDB records and inserts them into
    the database. This is typically run once to load the complete HMDB
    reference database.
    
    Args:
        file: Path to the HMDB RData file to import.
    """
    print("Start fill_table() function")
    with SessionFactory() as session:
        HMDBService(session).insert_hmdb_table(file)

if __name__ == "__main__":
    cli()
