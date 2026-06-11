import os
import re
import pandas as pd
import pyreadr
import argparse
from datetime import datetime
from sqlmodel import Session, select, col
from dimsdb.archive.add_functions import add_patient, add_sample, add_dims_run
from dimsdb.archive.models import Patient, Sample
from dimsdb.db.session import engine

import dimsdb.crud.dimsrun as dimsrun_crud_crud

from dimsdb.utils.exceptions import NotFoundError

def parse_rdata_file(file):
    """Parsing a RData file with the pyreadr package

    Args:
        file: file path to a RData file

    Returns:
         A dataframe containing the RData file data
    """
    # read the RData file
    result = pyreadr.read_r(file)

    df_name = list(result.keys())[0]

    rdata_df = result.get(df_name)
    sample_ids = get_samples_run(rdata_df.columns)
    sample_ids_zscores = [sample_id + "_Zscore" for sample_id in sample_ids]

    rdata_df["HMDB_code"] = rdata_df["HMDB_code"].apply(
        lambda x: None if pd.isna(x) or x == "" else x
    )

    cols = [
        "mzmed.pgrp",
        "HMDB_code",
        "theormz_HMDB",
        "ppmdev",
        "assi_HMDB"
    ] + sample_ids + sample_ids_zscores

    rdata_df = rdata_df[cols]

    return rdata_df

def get_samples_run(peakgroup_df_cols):
    """Get a set of samples  in a run

    Args:
        peakgroup_df_cols: column names of the peakgroup dataframe

    Returns:
        a set of samples starting with C or P
    """
    sample_ids = [
        col for cols in peakgroup_df_cols
        if (col.startswith(("C", "P")) and not col.endswith("_Zscore"))
    ]

    return sample_ids

def get_repo_tag(file_path, repo_name="DIMS"):
    """Get the repo tag from a log file

    Args:
        file_path: file path to a log file
        repo_name: repository name (default: DIMS)

    Returns:
        the repository tag
    """
    lines = open(file_path, "r").readlines()

    for i, line in enumerate(lines):
        if line.strip() == repo_name:
            if i + 1 < len(lines):
                commit_line = lines[i + 1]
                match = re.search(r'v\s*([^\s,]+)', commit_line)
                if match:
                    return match.group(1)
            break
    return "Unknown"

def get_run_parameters(file_path):
    """Get the run parameters

    Args:
        file_path: file path to a workflow parameters file

    Returns:
        a dataframe containing the run parameters
    """
    parameter_df = pd.read_table(file_path, delimiter="\t")
    cols_to_keep = [
        "email",
        "matrix",
        "nr_replicates",
        "ppm",
        "resolution",
        "date"
    ]
    pattern = "|".join(cols_to_keep)
    parameter_df = parameter_df[parameter_df["param"].str.contains(pattern, case=False, na=False)]
    return parameter_df

def add_dimsrun_db(run_name, run_parameters, repo_version):
    """Add a DIMS run to the database

    Args:
        run_name: the run name
        run_parameters: dataframe with run parameters
        repo_version: the repository version
    """
    run_parameters = run_parameters.set_index("param")
    dimsrun = add_dims_run(
        run_name,
        run_parameters.at["email", "value"],
        run_parameters.at["nr_replicates", "value"],
        run_parameters.at["date", "value"],
        run_parameters.at["ppm", "value"],
        run_parameters.at["resolution", "value"],
        run_parameters.at["matrix", "value"],
        repo_version,
    )

    try:
        dimsrun = dimsrun_crud_crud.select_dimsrun_by_id(Session(engine), run_name)
    except NotFoundError:
        dimsrun = dimsrun_crud_crud.insert_dimsrun(dimsrun)


def add_samples_db(peakgroup_df_cols):
    """Add sample to the database

    Args:
        peakgroup_df_cols: set of sample names
    """
    sample_ids = get_samples_run(peakgroup_df_cols)

    with Session(engine) as session:
        for sample_id in sample_ids:
            patient_id = sample_id.split(".")[0]

            query_patient = select(Patient).where(Patient.id == patient_id)
            patient = session.exec(query_patient).one_or_none()

            if not patient:
                patient = add_patient(patient_id, None)
                session.add(patient)
                session.commit()

            query_sample = select(Sample).where(Sample.id == sample_id)
            sample = session.exec(query_sample).one_or_none()

            if not sample:
                sample = add_sample(sample_id, patient)
                session.add(sample)
                session.commit()

def main(dir_path):
    time_start = datetime.now()
    print("Start")
    print(time_start)
    chunk_size = 1000
    run_name = os.path.basename(dir_path)
    print(run_name)
    repo_version = get_repo_tag(dir_path / "repository_version.log", "DIMS")
    run_parameters_df = get_run_parameters(dir_path / "workflow_params.txt")
    add_dimsrun_db(run_name, run_parameters_df, repo_version)

    polarities = ["positive", "negative"]
    for polarity in polarities:
        print(polarity)
        peakgroup_df = parse_rdata_file(dir_path / f"outlist_identified_{polarity}.RData")
        peakgroup_df["row_hash"] = peakgroup_df.apply(get_row_hash, axis=1)

        add_samples_db(peakgroup_df.columns)
        print("Samples added")
        hmdb_row_hash_df = get_dimsresults_hmdb_link_df(peakgroup_df)
        print("hmdb_row_hash_df done")
        dims_data_df = transform_dims_data(peakgroup_df)
        print("DIMS data transformation done")
        dims_dict = transform_dims_data_to_dict(dims_data_df, polarity, run_name)
        print("dims_dict done")
        add_dimsresults_to_db(dims_dict, chunk_size)
        print("DIMS resuls added")
        print("Add link DIMS results and HMDB")
        add_link_results_hmdb(hmdb_row_hash_df, chunk_size)
    time_end = datetime.now()
    print("Time total")
    print(time_end)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "dir_name",
        type=str,
        help="Path to the directory containing the RData files",
    )

    args = parser.parse_args()
    main(args.dir_name)
