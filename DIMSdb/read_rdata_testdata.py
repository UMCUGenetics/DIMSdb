from sqlmodel import Session, create_engine, select, col
from sqlalchemy import any_
import configparser
import pathlib
# import pyreadr
import os
# os.chdir('/Users/mraves2/Development/DIMSdb/DIMSdb')
# from models import DIMSRun, DIMSResults, Patient, Sample, HMDB
import pandas as pd
import pickle
from models import *
# from sqlalchemy.orm import mapper
# mapper(DIMSResults, dimsresults)
from datetime import date, time, datetime
from math import isnan
# https://github.com/vnmabus/rdata
import rdata

config = configparser.ConfigParser()
# config.read(f'{pathlib.Path(__file__).parent.parent.absolute()}/config.ini')
config.read('/Users/aluesin2/Documents/DIMSdb/config.ini')

sql_protocol = config.get('database', 'sql_protocol')
database_name_or_url = config.get('database', 'database_name_or_url')

sql_url = f'{sql_protocol}{database_name_or_url}'

engine = create_engine(sql_url)


def parse_rdata(file, runname):
    # get polarity from the file name
    print("start")
    print(datetime.now())
    polarity_string = pathlib.Path(file).stem.split("_")[-1]
    polarity = True
    if polarity_string == 'negative':
        polarity = False
    # read the RData file
    # result = pyreadr.read_r(file)
    parsed = rdata.parser.parse_file(file)
    result = rdata.conversion.convert(parsed)
    # identified = pyreadr.read_r(file, use_objects="outlist.identified")

    # split data into identified and unidentified part
    identified = result["outlist.ident"]
    unidentified = result["outlist.not.ident"]
    # unidentified = result["outlist.not.ident.space"]
    # merge the two parts
    merged_df = pd.concat((identified, unidentified))

    merged_df["HMDB_code"].fillna('', inplace=True)
    merged_df["HMDB_code"] = merged_df["HMDB_code"].str.split(";")

    merged_df["assi_HMDB"].fillna('', inplace=True)
    merged_df["assi_HMDB"] = merged_df["assi_HMDB"].str.split(";")

    cols_to_remove = ["HMDB_code", "assi_HMDB", "assi_noise", "avg.ctrls",
                      "avg.int", "fq.best", "fq.worst", "iso_HMDB",
                      "mzmax.pgrp", "mzmed.pgrp", "mzmin.pgrp", "nrsamples",
                      "ppmdev", "sd.ctrls", "theormz_HMDB", "theormz_noise"]
    sample_ids = [col_name for col_name in merged_df.columns
                if col_name not in cols_to_remove and "_Zscore" not in col_name]
    # patient_ids = [sample_ids.split('.')[0] for sample_id in sample_ids]
    # merged_df.to_excel("merged_df_RES_PL_20231002_plasma.xlsx")
    print(sample_ids)
    # list_of_objects = []

    # replace later with sample type from input
    sample_type = "plasma"

    # fill Patients and Samples tables
    for sample_id in sample_ids:
        # print(sample_id)
        patient_id = sample_id.split(".")[0]
        # print(patient_id)
        # Patients
        with Session(engine) as session:
            query = select(Patient).where(Patient.intermediate_id == patient_id)
            patient = session.exec(query).one_or_none()

        if not patient:
            patient = Patient()
            patient.intermediate_id = patient_id
            patient.birth_year = 2000
            insert_data([patient])
            # list_of_objects.append(patient.copy())

        # Samples
        with Session(engine) as session:
            query = select(Sample).where(Sample.id == sample_id)
            sample = session.exec(query).one_or_none()

        if not sample:
            sample = Sample()
            sample.id = sample_id
            sample.patient = patient
            sample.type = sample_type
            insert_data([sample])
            # list_of_objects.append(sample.copy())

    # fill DIMSRun table
    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == runname)
        dimsrun = session.exec(query).one_or_none()

    if not dimsrun:
        dimsrun = DIMSRun()
        dimsrun.name = runname
        dimsrun.email = "todo@umcutrecht.nl"
        dimsrun.date = date.today()
        dimsrun.num_replicates = 2
        insert_data([dimsrun])
        # list_of_objects.append(dimsrun.copy())
    print("before HMDB")
    print(datetime.now())

    # fill HMDB table
    hmdb_objects = []
    for index, row in merged_df.iterrows():
        if row["HMDB_code"]:
            # if theormz_HMDB is not defined, set it to 0
            if isnan(row["theormz_HMDB"]):  # if row["theormz_HMDB"] == " "
                MZ_index = 0
            else:
                MZ_index = float(row["theormz_HMDB"])

            for HMDB_index, HMDB_code in enumerate(row["HMDB_code"]):
                if HMDB_code:
                    # NB: M+H and M-H have the same HMDB_ID, but not same m/z !
                    # add _pH or _mH respectively to HMDB_code to make them unique
                    if not "_" in HMDB_code:
                        if polarity == 0:
                            HMDB_code = HMDB_code + "_mH"
                        elif polarity == 1:
                            HMDB_code = HMDB_code + "_pH"
                        row["HMDB_code"][HMDB_index] = HMDB_code
                    with Session(engine) as session:
                        query = select(HMDB).where(HMDB.hmdb_id == HMDB_code)
                        hmdb_entry = session.exec(query).one_or_none()

                    if not hmdb_entry:
                        hmdb_entry = HMDB(
                            hmdb_id=HMDB_code,
                            name=row["assi_HMDB"][HMDB_index],
                            # MZ=float(row["theormz_HMDB"])
                            theor_MZ=MZ_index
                        )
                        hmdb_objects.append(hmdb_entry)
    insert_data(hmdb_objects)

    print("after HMDB")
    print(datetime.now())

    print("before DIMSresults")
    # fill DIMSResults table
    dimsresults_list = []

    for index, row in merged_df.iterrows():
        # print(row["HMDB_code"])
        dimsresults_list_perrow = []
        for sample_id in sample_ids:
            dimsresult = DIMSResults()
            dimsresult.run = dimsrun
            dimsresult.run_name = runname
            dimsresult.polarity = polarity
            dimsresult.m_z = float(row["mzmed.pgrp"])
            zscore_colname = f'{sample_id}_Zscore'
            dimsresult.intensity = float(row[sample_id])
            dimsresult.z_score = float(row[zscore_colname])
            dimsresult.sample_id = sample_id

            with Session(engine) as session:
                session.add(dimsresult)
                session.commit()
                session.refresh(dimsresult)
            # insert_data(dimsresult)

            add_sample_hmdb(dimsresult, row, sample_id)

            # dimsresults_list.append(dimsresult)
        # dimsresults_list.extend(dimsresults_list_perrow)
    # insert_data(dimsresults_list)
    # list_of_objects.extend(dimsresultsobj.copy())
    print("after DIMSresults")
    print(datetime.now())


def add_sample_hmdb(dimsresult, row, sample_id):
    with Session(engine) as session:
        query = select(Sample).where(Sample.id == sample_id)
        results = session.exec(query)
        sample = results.one()
        dimsresult.sample = sample
        if row["HMDB_code"]:
            results = session.query(HMDB).filter(col(HMDB.hmdb_id).in_(row["HMDB_code"]))
            hmdbs = results.all()
            # dimsresults.hmdb = hmdbs
            dimsresult.hmdb = hmdbs
        session.add(dimsresult)
        session.commit()


def insert_data(list_of_models):
    with Session(engine) as session_commit:
        session_commit.add_all(list_of_models)
        session_commit.commit()


def main():
    # Update run_name with folder name of data to be inserted
    # path_name = "/Users/mraves2/Metabolomics/DIMSdb/Input_data/Plasma/RData/"
    path_name = "/Users/aluesin2/Documents/DIMSdb/test_data/"
    run_names = [f for f in os.listdir(path_name) if not f.startswith('.')]
    # run_names = sorted(run_names)
    # run_names = run_names[0:(len(run_names)-3)] # last ones are small test datasets
    # run_names = ["t"] # small test dataset
    run_names = ["test_long", "test_wide"] # 2 tests, one with all columns, one with all rows
    run_names = ["RES_PL_20231002_plasma"]
    for run_name in run_names:
        print(run_name)
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

