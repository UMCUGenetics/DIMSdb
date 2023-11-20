from sqlmodel import Session, create_engine
import configparser
import pathlib
import pyreadr
import os
# os.chdir('/Users/mraves2/Development/DIMSdb/DIMSdb')
# from models import DIMSRun, DIMSResults, Patient, Sample, HMDB
import pandas as pd
import pickle
from models import *
# from sqlalchemy.orm import mapper
# mapper(DIMSResults, dimsresults)
from datetime import date

config = configparser.ConfigParser()
config.read(f'{pathlib.Path(__file__).parent.parent.absolute()}/config.ini')

sql_protocol = config.get('database', 'sql_protocol')
database_name_or_url = config.get('database', 'database_name_or_url')

sql_url = f'{sql_protocol}{database_name_or_url}'

engine = create_engine(sql_url)


def parse_rdata(file, runname):
    # get polarity from the file name
    polarity_string = pathlib.Path(file).stem.split("_")[-1]
    polarity = True
    if polarity_string == 'negative':
        polarity = False
    print(polarity)
    # read the RData file
    result = pyreadr.read_r(file)
    # identified = pyreadr.read_r(file, use_objects="outlist.identified")

    # split data into identified and unidentified part
    identified = result["outlist.ident"]
    # unidentified = result["outlist.not.ident"]
    unidentified = result["outlist.not.ident"]
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
    samples = [col_name for col_name in merged_df.columns
                if col_name not in cols_to_remove and "_Zscore" not in col_name]
    patients = [sample.split('.')[0] for sample in samples]
    list_of_objects = []

    # replace later with sample type from input
    sample_type = "plasma"

    # fill Patients and Samples tables
    for sample in samples:
        print(sample)
        # Patients
        patientobj = Patient()
        patient = sample  #.split(".")[0]
        patientobj.intermediate_id = patient
        patientobj.birth_year = 2000
        # list_of_objects.append(patientobj.copy())
        insert_data([patientobj])
        # Samples
        sampleobj = Sample()
        sampleobj.id = sample
        sampleobj.patient_id = sample
        sampleobj.type = sample_type
        insert_data([sampleobj])
        # list_of_objects.append(sampleobj.copy())

    # fill DIMSRun table
    dimsrun = DIMSRun()
    dimsrun.name = runname
    dimsrun.email = "todo@umcutrecht.nl"
    dimsrun.date = date.today()
    dimsrun.num_replicates = 2
    insert_data([dimsrun])
    # list_of_objects.append(dimsrun.copy())

    # fill DIMSResults table
    dimsresultsobj = []
    for index, row in merged_df.iterrows():
        dimsresultsobj_perrow = []
        for sample in samples:
            dimsresults = DIMSResults()
            dimsresults.run_name = runname
            dimsresults.polarity = polarity
            dimsresults.m_z = float(row["mzmed.pgrp"])
            zscore_colname = f'{sample}_Zscore'
            dimsresults.sample_id = sample
            dimsresults.intensity = float(row[sample])
            dimsresults.z_score = float(row[zscore_colname])
            dimsresultsobj_perrow.append(dimsresults)
        dimsresultsobj.extend(dimsresultsobj_perrow)
    insert_data(dimsresultsobj)
    # list_of_objects.extend(dimsresultsobj.copy())

    hmdb_objects = []
    for index, row in merged_df.iterrows():
        if row["HMDB_code"]:
            for HMDB_index, HMDB_code in enumerate(row["HMDB_code"]):
                if HMDB_code:
                    hmdb_object = HMDB(
                        hmdb_id= HMDB_code,
                        name=row["assi_HMDB"][HMDB_index],
                        MZ=float(row["theormz_HMDB"])
                    )
                    hmdb_objects.append(hmdb_object)
    insert_data(hmdb_objects)
    # return list_of_objects


def insert_data(list_of_models):
    with Session(engine) as session:
        session.add_all(list_of_models)
        session.commit()


def main():
    # Update run_name with folder name of data to be inserted
    path_name = "/Users/rernst3/Development/WOC_2023/DIMSdb_Rdata/"
    # run_names = [f for f in os.listdir(path_name) if not f.startswith('.')]
    run_names = ["test"]
    for run_name in run_names:
        print(run_name)
        file_neg = path_name + run_name + '/outlist_ident_space_negative.RData'
        print(file_neg)
        file_pos = path_name + run_name + '/outlist_ident_space_positive.RData'
        parse_rdata(file_neg, run_name)
        # insert into database tables
        # insert_data(objectlist_neg)
        # parse_rdata(file_pos, run_name)
        #insert_data(objectlist_pos)


if __name__ == "__main__":
    main()
