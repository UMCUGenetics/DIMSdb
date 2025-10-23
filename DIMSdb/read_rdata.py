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
import math

config = configparser.ConfigParser()
# config.read(f'{pathlib.Path(__file__).parent.parent.absolute()}/config.ini')
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
            run_date = run_date.group(0) + "0101"
        else:
            run_date = "20000101"

    run_date = date.fromisoformat(run_date)

    # fill DIMSRun table
    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == runname)
        dimsrun = session.exec(query).one_or_none()

        if not dimsrun:
            dimsrun = add_dims_run(runname,
                                   settings_df["email"]["value"],
                                   settings_df["nrepl"]["value"],
                                   run_date,
                                   5,
                                   settings_df["resol"]["value"],
                                   settings_df["matrix"]["value"])
            insert_data([dimsrun])

        session.refresh(dimsrun)
    return dimsrun


def parse_rdata(file, runname):
    # get polarity from the file name
    print("start")
    print(datetime.now())

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

    # fill Patients and Samples tables
    for sample_id in sample_ids:
        patient_id = sample_id.split(".")[0]
        # Patients
        with Session(engine) as session:
            query = select(Patient).where(Patient.intermediate_id == patient_id)
            patient = session.exec(query).one_or_none()

        if not patient:
            patient = add_patient(patient_id, None)
            insert_data([patient])

        # Samples
        with Session(engine) as session:
            query = select(Sample).where(Sample.id == sample_id)
            sample = session.exec(query).one_or_none()

        if not sample:
            sample = add_sample(sample_id, patient)
            insert_data([sample])

    # TODO: dubbele metabolieten, pos en neg mode, komen 2x in dimsresults, nu 2x dezelfde data ipv verschillend per scanmode
        # fill DIMSResults table
        zscore_colname = f'{sample_id}_Zscore'
        for index, row in merged_df.iterrows():
            if "_" in row["HMDB_code"]:
                adduct = row["HMDB_code"].split("_")[1]
            else:
                adduct = 0

            dimsresult = add_dims_result(dimsrun,
                                         sample_id,
                                         polarity,
                                         float(row["mzmed.pgrp"]),
                                         float(row[sample_id]),
                                         float(row[zscore_colname]),
                                         adduct,
                                         row["ppmdev"],
                                         runname,
                                         sample)

            with Session(engine) as session:
                session.add(dimsresult)
                session.commit()
                session.refresh(dimsresult)

            add_sample_hmdb(dimsresult, row, sample_id)

    print("___ DIMSresults done ___")


def add_sample_hmdb(dimsresult, row, sample_id):
    with Session(engine) as session:
        query = select(Sample).where(Sample.id == sample_id)
        results = session.exec(query)
        sample = results.one()
        dimsresult.sample = sample
        if row["HMDB_code"]:
            if "_" in row["HMDB_code"]:
                hmdb_code = row["HMDB_code"].split("_")[0]
            else:
                hmdb_code = row["HMDB_code"]
            results = session.query(HMDB).filter(col(HMDB.sec_hmdb_id).like(hmdb_code))
            hmdbs = results.all()
            dimsresult.hmdb = hmdbs
        session.add(dimsresult)
        session.commit()


def insert_data(list_of_models):
    with Session(engine) as session:
        session.add_all(list_of_models)
        session.commit()


def main():
    # Update run_name with folder name of data to be inserted
    path_name = "/Users/aluesin2/Documents/DIMSdb/test_data/"
    run_names = [f for f in os.listdir(path_name) if not f.startswith('.')]

    run_names = ["test_long", "test_wide"]  # 2 tests, one with all columns, one with all rows
    run_names = ["RES_PL_20231002_plasma"]

    for run_name in run_names:
        print(run_name)
        settings_file = path_name + run_name + 'settings.config'
        dimsrun = parse_settings_file(settings_file, run_name)
        # file_neg = path_name + run_name + '/outlist_ident_space_negative.RData'
        file_neg = path_name + run_name + '/outlist_identified_negative.RData'
        print(file_neg)
        parse_rdata(file_neg, run_name)
        # file_pos = path_name + run_name + '/outlist_ident_space_positive.RData'
        file_pos = path_name + run_name + '/outlist_identified_positive.RData'
        print(file_pos)
        parse_rdata(file_pos, run_name)


if __name__ == "__main__":
    main()
