from sqlmodel import Session, create_engine, select, col, or_
import configparser
import pathlib
import os
import pandas as pd
from datetime import date, time, datetime
# https://github.com/vnmabus/rdata
import rdata
from add_functions import *
import re
import base64
import time
import numpy as np

config = configparser.ConfigParser()
config.read('/Users/aluesin2/Documents/DIMSdb/config.ini')

sql_protocol = config.get('database', 'sql_protocol')
database_name_or_url = config.get('database', 'database_name_or_url')

sql_url = f'{sql_protocol}{database_name_or_url}'

engine = create_engine(sql_url)


def parse_settings_file(file, runname):
    settings_df = pd.read_table(file, sep="=")
    # rename the first column to "value"
    settings_df = settings_df.set_axis(["value"], axis=1)

    # get date
    run_date = re.search("202[0-9]{5}", runname)
    if run_date is not None:
        run_date = run_date.group(0)
    else:
        run_date = re.search("202[0-9]", runname)
        if run_date is not None:
            run_date = run_date.group(0)+"0101"
        else:
            run_date = "20000101"

    run_date = date.fromisoformat(run_date)

    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == runname)
        dimsrun = session.exec(query).one_or_none()

        if not dimsrun:
            dimsrun = add_dims_run(runname,
                                   settings_df.at["email", "value"],
                                   settings_df.at["nrepl", "value"],
                                   run_date,
                                   5,
                                   settings_df.at["resol", "value"],
                                   settings_df.at["matrix", "value"].upper())
            insert_data([dimsrun], session)


def parse_rdata(file, runname):
    # get polarity from the file name
    polarity_string = pathlib.Path(file).stem.split("_")[-1]
    polarity = True  # if polarity is positive
    if polarity_string == 'negative':
        polarity = False

    # read the RData file
    parsed = rdata.parser.parse_file(file)
    result = rdata.conversion.convert(parsed)

    # split data into identified and unidentified part
    identified = result["outlist.ident"]
    unidentified = result["outlist.not.ident"]

    # merge the two parts
    merged_df = pd.concat((identified, unidentified))

    merged_df["HMDB_code"].fillna('', inplace=True)
    merged_df["HMDB_code"] = merged_df["HMDB_code"].str.split(";")  # string to list

    merged_df["assi_HMDB"].fillna('', inplace=True)
    merged_df["assi_HMDB"] = merged_df["assi_HMDB"].str.split(";")  # string to list
    merged_df = merged_df.reset_index(drop=True)

    cols_no_samples = ["HMDB_code", "assi_HMDB", "assi_noise", "avg.ctrls",
                       "avg.int", "fq.best", "fq.worst", "iso_HMDB",
                       "mzmax.pgrp", "mzmed.pgrp", "mzmin.pgrp", "nrsamples",
                       "ppmdev", "sd.ctrls", "theormz_HMDB", "theormz_noise"]
    # get sample columns
    sample_ids = [col_name for col_name in merged_df.columns
                  if col_name not in cols_no_samples and "_Zscore" not in col_name]

    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == runname)
        dimsrun = session.exec(query).one_or_none()

    hash_same_row = []

    with Session(engine) as session:
        # fill Patients and Samples tables
        for sample_id in sample_ids:
            if sample_id == sample_ids[0]:
                first_sample = True
            else:
                first_sample = False

            print(sample_id)
            patient_id = sample_id.split(".")[0]
            # Patients
            query = select(Patient).where(Patient.intermediate_id == patient_id)
            patient = session.exec(query).one_or_none()

            if not patient:
                patient = add_patient(patient_id, None)
                insert_data([patient], session)

            # Samples
            query = select(Sample).where(Sample.id == sample_id)
            sample = session.exec(query).one_or_none()

            if not sample:
                sample = add_sample(sample_id, patient)
                insert_data([sample], session)

            # fill DIMSResults table
            zscore_colname = f'{sample_id}_Zscore'
            for index, row in merged_df.iterrows():

                if first_sample:
                    hash_row = str(round(row['mzmed.pgrp'], 5)) + str(time.time())
                    hash_row = base64.b64encode(hash_row.encode("ascii")).decode("ascii")
                    hash_same_row.append(hash_row)
                else:
                    hash_row = hash_same_row[index]

                if np.isnan(row["ppmdev"]):
                    ppmdev = None
                else:
                    ppmdev = row["ppmdev"]

                dimsresult = add_dims_result(dimsrun,
                                             sample_id,
                                             polarity,
                                             float(row["mzmed.pgrp"]),
                                             float(row[sample_id]),
                                             float(row[zscore_colname]),
                                             ppmdev,
                                             hash_row,
                                             runname,
                                             sample)

                session.add(dimsresult)
                session.commit()
                session.refresh(dimsresult)

                for hmdb_index, hmdb_code in enumerate(row['HMDB_code']):
                    if hmdb_code != '':
                        if not hmdb_code:
                            adduct = None
                        elif "_" in hmdb_code:
                            adduct = hmdb_code.split("_")[1]
                            hmdb_code = hmdb_code.split("_")[0]
                        else:
                            adduct = 0
                        # print(hmdb_code)

                        query = select(HMDB).where(or_(col(HMDB.sec_hmdb_id).contains(hmdb_code + ";"),
                                                       col(HMDB.sec_hmdb_id).endswith(hmdb_code)))
                        hmdb = session.exec(query).one_or_none()

                        if not hmdb:
                            hmdb_name = row["assi_HMDB"][hmdb_index]
                            if "[M" in hmdb_name:
                                hmdb_name = hmdb_name.split(" [M")[0]

                            hmdb = add_hmdb(hmdb_code,
                                            hmdb_code,
                                            hmdb_code,
                                            hmdb_name,
                                            "",
                                            row["theormz_HMDB"])

                            session.add(hmdb)
                            session.commit()
                            session.refresh(hmdb)

                            dimsresult_hmdb_link = add_dimsresult_hmdb_link(hmdb, dimsresult, adduct)
                            session.add(dimsresult_hmdb_link)
                            session.commit()
                        else:
                            query = select(DIMSResultsHMDBLink).where(DIMSResultsHMDBLink.result_id == dimsresult.uuid) \
                                .where(DIMSResultsHMDBLink.hmdb_id == hmdb.uuid)
                            dimsresult_hmdb_link = session.exec(query).one_or_none()

                            if not dimsresult_hmdb_link:
                                dimsresult_hmdb_link = add_dimsresult_hmdb_link(hmdb, dimsresult, adduct)
                                session.add(dimsresult_hmdb_link)
                                session.commit()

    print("___ DIMSresults done ___")


def add_sample_hmdb(dimsresult, hmdb_code, session):
    print(dimsresult.uuid)
    results = session.query(HMDB).filter(col(HMDB.sec_hmdb_id).like(hmdb_code + ";"),
                                         or_(col(HMDB.sec_hmdb_id).endswith(hmdb_code)))
    hmdbs = results.all()
    dimsresult.hmdb = hmdbs
    session.add(dimsresult)
    session.commit()


def insert_data(list_of_models, session):
    session.add_all(list_of_models)
    session.commit()


def main():
    # Update run_name with folder name of data to be inserted
    print("start")
    print(datetime.now())

    path_name = "/Users/aluesin2/Documents/DIMSdb/test_data/"
    run_names = [f for f in os.listdir(path_name) if not f.startswith('.')]
    print(run_names)

    # run_names = ["test_long", "test_wide"]  # 2 tests, one with all columns, one with all rows
    # run_names = ["TEST_20241115_RUN9"]

    for run_name in run_names:
        print(run_name)
        settings_file = path_name + run_name + '/settings.config'
        parse_settings_file(settings_file, run_name)
        file_neg = path_name + run_name + '/outlist_identified_negative.RData'
        print(file_neg)
        parse_rdata(file_neg, run_name)
        file_pos = path_name + run_name + '/outlist_identified_positive.RData'
        print(file_pos)
        parse_rdata(file_pos, run_name)

    print(datetime.now())
    print("___ Data done ___")


if __name__ == "__main__":
    main()
