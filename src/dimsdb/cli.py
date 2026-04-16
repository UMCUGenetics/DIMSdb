from pathlib import Path
from typing import Annotated
import typer
import uvicorn

from dimsdb import database
from dimsdb.import_data.fill_hmdb_table import fill_table
from dimsdb.import_data.read_data import main

# Setup Typer CLI
cli = typer.Typer(no_args_is_help=True)

@cli.command("init")
def init_db():
    database.create_db_and_tables()

@cli.command("run")
def run_server():
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
):
    print(f"{directory}")
    main(directory)

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
):
    fill_table(file)

if __name__ == "__main__":
    cli()
