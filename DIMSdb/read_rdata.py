import pandas as pd
import pyreadr
from DIMSdb.models import *
import pathlib


def parse_rdata(file, runname):
    result = pyreadr.read_r(file)

    polarity = pathlib.Path(file).stem.split("_")[-1]

    identified = result["outlist.ident"]
    unidentified = result["outlist.not.ident"]
    merged_df = pd.concat((identified, unidentified))
    cols_to_remove = ["HMDB_code", "assi_HMDB", "assi_noise", "avg.ctrls",
                      "avg.int", "fq.best", "fq.worst", "iso_HMDB",
                      "mzmax.pgrp", "mzmed.pgrp", "mzmin.pgrp", "nrsamples",
                      "ppmdev", "sd.ctrls", "theormz_HMDB", "theormz_noise"]
    patients = [col_name for col_name in merged_df.columns
                if col_name not in cols_to_remove and "_Zscore" not in col_name]
    print(patients)
    list_of_objects = []
    for index, row in merged_df.iterrows():
        dr = DIMSResults()
        dr.run_name = runname
        dr.polarity = polarity
        dr.m_z = row["mzmed.pgrp"]

        for patient in patients:
            zscore_colname = f'{patient}_Zscore'
            dr.z_score = row[zscore_colname]
            dr.sample_id = patient
            dr.intensity = row[patient]
            list_of_objects.append(dr.copy())

    return list_of_objects


def insert_data(list_of_models):
    pass


def main():
    print(parse_rdata('../outlist_identified_negative.RData', "koekjes"))


if __name__ == "__main__":
    main()
