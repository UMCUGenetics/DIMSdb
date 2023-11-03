import configparser
import pathlib

import pandas as pd
import pyreadr
from sqlmodel import create_engine, Session

from DIMSdb.models import *

config = configparser.ConfigParser()
config.read(f'{pathlib.Path(__file__).parent.parent.absolute()}/config.ini')

sql_protocol = config.get('database', 'sql_protocol')
datbase_name_or_url = config.get('database', 'datbase_name_or_url')

sql_url = f'{sql_protocol}{datbase_name_or_url}'

engine = create_engine(sql_url)


def parse_rdata(file, runname):
    result = pyreadr.read_r(file)

    polarity = pathlib.Path(file).stem.split("_")[-1]

    identified = result["outlist.ident"]
    unidentified = result["outlist.not.ident"]
    merged_df = pd.concat((identified, unidentified))

    merged_df["HMDB_code"].fillna('', inplace=True)
    merged_df["HMDB_code"] = merged_df["HMDB_code"].str.split(";")

    merged_df["assi_HMDB"].fillna('', inplace=True)
    merged_df["assi_HMDB"] = merged_df["assi_HMDB"].str.split(";")

    cols_to_remove = ["HMDB_code", "assi_HMDB", "assi_noise", "avg.ctrls",
                      "avg.int", "fq.best", "fq.worst", "iso_HMDB",
                      "mzmax.pgrp", "mzmed.pgrp", "mzmin.pgrp", "nrsamples",
                      "ppmdev", "sd.ctrls", "theormz_HMDB", "theormz_noise"]
    patients = [col_name for col_name in merged_df.columns
                if col_name not in cols_to_remove and "_Zscore" not in col_name]
    list_of_objects = []
    for index, row in merged_df.iterrows():
        dr = DIMSResults()
        dr.run_name = runname
        dr.polarity = polarity
        dr.m_z = row["mzmed.pgrp"]

        if row["HMDB_code"]:
            for HMDB_index, HMDB_code in enumerate(row["HMDB_code"]):
                hmdb_object = HMDB()
                hmdb_object.hmdb_id = HMDB_code
                hmdb_object.name = row["assi_HMDB"][HMDB_index]
                hmdb_object.MZ = row["theormz_HMDB"]
                # list_of_objects.append(hmdb_object.copy())
                # dr.hmdb.append(hmdb_object)

        for patient in patients:
            zscore_colname = f'{patient}_Zscore'
            dr.z_score = row[zscore_colname]
            dr.sample_id = patient
            dr.intensity = row[patient]
            list_of_objects.append(dr.copy())

    return list_of_objects


def insert_data(list_of_models):
    with Session(engine) as session:
        session.add_all(list_of_models)
        session.commit()


def main():
    # TODO: Update runname with folder name of data to be inserted
    objectlist = parse_rdata('../outlist_identified_negative.RData', "koekjes")
    insert_data(objectlist)


if __name__ == "__main__":
    main()
