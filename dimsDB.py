import argparse

import uvicorn

from DIMSdb.database import create_db_and_tables


def init_db(args):
    create_db_and_tables()


def run_server(args):
    uvicorn.run("DIMSdb.main:app", reload=True)


def import_dims(args):
    print(f"{args.file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda args: parser.print_help())
    subparser = parser.add_subparsers()

    parser_init = subparser.add_parser("init", help="Initializes database")
    parser_init.set_defaults(func=init_db)

    parser_run = subparser.add_parser("run", help="Run uvicorn server")
    parser_run.set_defaults(func=run_server)

    parser_import = subparser.add_parser("import", help="Import DIMS data")
    parser_import.add_argument("file")
    parser_import.set_defaults(func=import_dims)

    args = parser.parse_args()
    args.func(args)
