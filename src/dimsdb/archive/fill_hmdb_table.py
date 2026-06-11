import pandas as pd
import rdata

from dimsdb.db.session import engine


def read_hmdb_file(file):
    parsed = rdata.parser.parse_file(file)
    hmdb_df = rdata.conversion.convert(parsed, default_encoding="utf8")
    hmdb_df = pd.DataFrame(hmdb_df.get("dimspect_df"))
    hmdb_df.rename(
        columns={
            "HMDB_key": "hmdb_key",
            "HMDB_ID": "hmdb_id",
            "sec_HMDB_ID": "sec_hmdb_id",
            "HMDB_name": "name",
            "Chemical_formula": "chem_formula",
            "MNeutral": "theor_mz",
            "descr": "description"
        },
        inplace=True,
    )
    return hmdb_df


def add_hmdb_table(hmdb_df):
    with engine.begin() as conn:
        hmdb_df.to_sql(name="hmdb", con=conn, if_exists="append", index=False, chunksize=10000)


def fill_table(path_file):
    print("Transform the RData HMDB file")
    hmdb_df = read_hmdb_file(path_file)
    print("Start importing the HMDB df")
    add_hmdb_table(hmdb_df)
