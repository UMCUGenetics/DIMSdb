import base64
import os
import re
import pandas as pd
import time
import pyreadr
import argparse
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select, col, or_
from .add_functions import add_patient, add_sample, add_dims_run
from ..models.models import Patient, Sample, DIMSRun, DIMSResults, HMDB, DIMSResultsHMDBLink
from ..database import engine

def parse_rdata_file(file):
    """

    :param file:
    :return:
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

def get_row_hash(row):
    hash_row = str(round(row["mzmed.pgrp"], 5)) + str(time.time())
    hash_row = base64.b64encode(hash_row.encode("ascii")).decode("ascii")
    return hash_row

def get_samples_run(peakgroup_df_cols):
    sample_ids = [
            col for col in peakgroup_df_cols
            if (col.startswith(("C","P")) and not col.endswith("_Zscore"))
        ]

    return sample_ids

def get_repo_tag(file_path, repo_name="DIMS"):
    lines = open(file_path, "r").readlines()

    for i, line in enumerate(lines):
        if line.strip() == repo_name:
            if i + 1 < len(lines):
                commit_line = lines[i + 1]
                match = re.search(r'tag:\s*([^\s,]+)', commit_line)
                if match:
                    return match.group(1)
            break
    return None

def get_run_parameters(file_path):
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
    run_parameters = run_parameters.set_index("param")
    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == run_name)
        dimsrun = session.exec(query).one_or_none()

        if not dimsrun:
            dimsrun = add_dims_run(
                run_name,
                run_parameters.at["email", "value"],
                run_parameters.at["nr_replicates", "value"],
                run_parameters.at["date", "value"],
                run_parameters.at["ppm", "value"],
                run_parameters.at["resolution", "value"],
                run_parameters.at["matrix", "value"],
                repo_version
            )
            session.add(dimsrun)
            session.commit()

def add_samples_db(peakgroup_df_cols):
    sample_ids = get_samples_run(peakgroup_df_cols)

    with Session(engine) as session:
        for sample_id in sample_ids:
            patient_id = sample_id.split(".")[0]

            query_patient = select(Patient).where(Patient.intermediate_id == patient_id)
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

def split_assi_hmdb(df_col):
    reg_pattern = r"(?<!&gt)(?<!&lt)(?<!&amp)(?<!2235)(?<!awR\))(?<!&alpha);"
    return re.split(reg_pattern, df_col)

def get_dimsresults_hmdb_link_df(merged_df):
    hmdb_row_hash_df = merged_df[["HMDB_code", "assi_HMDB", "theormz_HMDB", "row_hash"]]
    hmdb_row_hash_df = hmdb_row_hash_df.dropna()
    hmdb_row_hash_df["HMDB_code"] = hmdb_row_hash_df["HMDB_code"].str.split(";")
    hmdb_row_hash_df["assi_HMDB"] = hmdb_row_hash_df["assi_HMDB"].apply(split_assi_hmdb)
    hmdb_row_hash_df = hmdb_row_hash_df.explode("HMDB_code")
    hmdb_row_hash_df = hmdb_row_hash_df.explode("assi_HMDB")
    hmdb_row_hash_df = hmdb_row_hash_df.drop_duplicates()
    hmdb_row_hash_df[["HMDB_code", "adduct"]] = hmdb_row_hash_df["HMDB_code"].str.extract(r"(HMDB\d+)_?(\d+)?")
    hmdb_row_hash_df["adduct"] = hmdb_row_hash_df["adduct"].fillna(0).astype(int)
    hmdb_row_hash_df["assi_HMDB"] = hmdb_row_hash_df["assi_HMDB"].str.replace(r"\[M.*", "", regex=True).str.strip()

    return hmdb_row_hash_df

def add_dimsresults_to_db(dims_data_dict, chunk_size):
    with Session(engine) as session:
        for i in range(0, len(dims_data_dict), chunk_size):
            session.execute(insert(DIMSResults), dims_data_dict[i:i + chunk_size])
            session.commit()


def transform_dims_data(peakgroup_df):
    peakgroup_df = peakgroup_df.drop(columns=["theormz_HMDB"])

    info_cols = ["mzmed.pgrp", "ppmdev", "HMDB_code", "assi_HMDB", "row_hash"]

    cols = peakgroup_df.columns.difference(info_cols)

    intensity_cols = [c for c in cols if not c.endswith("_Zscore")]
    zscore_cols = [c for c in cols if c.endswith("_Zscore")]

    # stack
    intensity = peakgroup_df[intensity_cols].stack().rename("Intensity")

    zscore = (
        peakgroup_df[zscore_cols]
        .rename(columns=lambda c: c[:-7])
        .stack()
        .rename("Zscore")
    )

    # expliciet joinen i.p.v. implicit alignment
    result = intensity.to_frame().join(zscore, how="left")

    result = result.reset_index().rename(columns={
        "level_1": "Sample"
    })

    # join info cols
    result = result.join(peakgroup_df[info_cols], on="level_0").drop(columns=["level_0"])

    # lijst conversie
    for col in ["HMDB_code", "assi_HMDB"]:
        result[col] = (
            result[col]
            .fillna("")
            .astype(str)
            .str.split(";", regex=False)
        )

    return result
    

def transform_dims_data_to_dict(dims_data_df, polarity, run_name):
    dims_data_df = dims_data_df.drop(["assi_HMDB"], axis=1)
    dims_data_df.columns = ["m_z", "ppm_dev", "HMDB_code", "row_hash", "sample_id", "intensity", "z_score"]

    if polarity == "positive":
        pol = True
    else:
        pol = False

    dims_data_df["polarity"] = pol
    dims_data_df["run_name"] = run_name

    dimsresults_dict = dims_data_df.to_dict(orient="records")
    return dimsresults_dict


def get_dimsresults_uuid_by_row_hash(row_hashes, chunk_size=500):
    rows = []

    with Session(engine) as session:
        for i in range(0, len(row_hashes), chunk_size):
            chunk = row_hashes[i:i + chunk_size]
            query = (
                select(DIMSResults.uuid, DIMSResults.row_hash)
                .where(DIMSResults.row_hash.in_(chunk))
            )
            rows.extend(session.exec(query).all())

    uuid_rowhash_df = pd.DataFrame(
        rows,
        columns=["dims_results_uuid", "row_hash"]
    )

    return uuid_rowhash_df


def get_dimsresults_hmdb_link(hmdb_code_list, size_chunk):
    like_clauses = [
        or_(
            col(HMDB.sec_hmdb_id).contains(f"{hmdb_code};%"),
            col(HMDB.sec_hmdb_id).endswith(hmdb_code)
        )
        for hmdb_code in hmdb_code_list
    ]

    results = []

    with Session(engine) as session:
        for i in range(0, len(like_clauses), size_chunk):
            like_clauses_chunk = like_clauses[i:i + size_chunk]

            query = (
                select(HMDB.uuid, HMDB.sec_hmdb_id)
                .where(or_(*like_clauses_chunk))
            )
            chunk_result = session.exec(query).all()
            if chunk_result:
                results.append(
                    pd.DataFrame(chunk_result, columns=['uuid', 'sec_hmdb_id'])
                )

    if results:
        return pd.concat(results, ignore_index=True)

    return pd.DataFrame(columns=['uuid', 'sec_hmdb_id'])


def add_new_hmdb(hmdb_info):
    hmdb_info = hmdb_info.rename(
        columns={'assi_HMDB': 'name', 'theormz_HMDB': 'theor_mz'}
    )

    hmdb_info['hmdb_key'] = hmdb_info['HMDB_code']
    hmdb_info['hmdb_id'] = hmdb_info['HMDB_code']
    hmdb_info['sec_hmdb_id'] = hmdb_info['HMDB_code']

    hmdb_info = hmdb_info.drop(['HMDB_code'], axis=1)
    hmdb_info_dict = hmdb_info.to_dict(orient='records')

    with Session(engine) as session:
        session.execute(insert(HMDB), hmdb_info_dict)
        session.commit()


def add_hmdb_results_link(row_hash_adduct_uuid, size_chunk):
    row_hash_adduct_uuid = row_hash_adduct_uuid.to_dict(orient='records')

    with Session(engine) as session:
        for i in range(0, len(row_hash_adduct_uuid), size_chunk):
            session.execute(
                insert(DIMSResultsHMDBLink),
                row_hash_adduct_uuid[i:i + size_chunk]
            )
            session.commit()


def add_link_results_hmdb(hmdb_row_hash_df, size_chunk):
    hmdb_row_hash_df = hmdb_row_hash_df.dropna(subset=["HMDB_code"])
    hmdb_uuid_code_df = get_dimsresults_hmdb_link(hmdb_row_hash_df["HMDB_code"].unique(), size_chunk)

    # Get a list of all unique hmdb codes present in the DIMSResultsHMDBLink table
    sec_hmdb_ids_list = (
        hmdb_uuid_code_df["sec_hmdb_id"]
        .str.split(';')
        .explode()
        .unique()
    )

    # Get hmdb codes that are not present in the DIMSResultsHMDBLink table
    hmdb_not_present = list(set(hmdb_row_hash_df["HMDB_code"]) - set(sec_hmdb_ids_list))
    print(len(hmdb_not_present))
    if len(hmdb_not_present) > 0:
        hmdb_info_not_present = hmdb_row_hash_df[hmdb_row_hash_df["HMDB_code"].isin(hmdb_not_present)]

        # Add the HMDB info for the hmdb codes that are not present in the DIMSResultsHMDBLink table
        add_new_hmdb(hmdb_info_not_present)

        # Get the uuids for the newly added hmdb codes
        new_hmdb_results_link_df = get_dimsresults_hmdb_link(hmdb_info_not_present["HMDB_code"].unique(), size_chunk)
        # Combine all uuid info for all hmdb codes
        hmdb_uuid_code_df = pd.concat([hmdb_uuid_code_df, new_hmdb_results_link_df])
    print("Done adding new HMDBs")
    # Get the correct combination of uuid and hmdb code
    hmdb_uuid_code_df = hmdb_uuid_code_df.assign(sec_hmdb_id=hmdb_uuid_code_df['sec_hmdb_id'].str.split(';')).explode(
        'sec_hmdb_id')
    uuid_hmdb_link_df = hmdb_uuid_code_df[hmdb_uuid_code_df['sec_hmdb_id'].isin(hmdb_row_hash_df['HMDB_code'])]
    uuid_hmdb_link_df = uuid_hmdb_link_df.rename(columns={'uuid': 'hmdb_id', 'sec_hmdb_id': 'HMDB_code'})

    # Combine the uuid with row hash and adduct info
    merged_link_info = pd.merge(hmdb_row_hash_df, uuid_hmdb_link_df, on='HMDB_code', how='left')
    row_hash_adduct_uuid = merged_link_info[['hmdb_id', 'row_hash', 'adduct']].drop_duplicates()
    row_hash_adduct_uuid[['hmdb_id']] = row_hash_adduct_uuid[['hmdb_id']].astype(int)
    row_hash_adduct_uuid[['row_hash']] = row_hash_adduct_uuid[['row_hash']].astype(str)

    dims_uuid_df = get_dimsresults_uuid_by_row_hash(
        row_hash_adduct_uuid["row_hash"].unique())

    final_link_df = (
        row_hash_adduct_uuid
        .merge(dims_uuid_df, on="row_hash", how="left")
        [['dims_results_uuid', 'hmdb_id', 'adduct', 'row_hash']]
        .drop_duplicates()
    )

    print(final_link_df.size)
    # Add the new uuid-row hash in the DIMSResultsHMDBLink table
    add_hmdb_results_link(final_link_df, size_chunk)

def main(dir_path):
    chunk_size = 1000
    run_name = os.path.basename(dir_path)
    print(run_name)
    repo_version = get_repo_tag(dir_path / "repository_version.log", "DIMS")
    run_parameters_df = get_run_parameters(dir_path / "workflow_params.txt")

    add_dimsrun_db(run_name, run_parameters_df, repo_version)

    polarities = ["positive", "negative"]
    for polarity in polarities:
        peakgroup_df = parse_rdata_file(dir_path / f"outlist_identified_{polarity}.RData")
        peakgroup_df["row_hash"] = peakgroup_df.apply(get_row_hash, axis=1)

        add_samples_db(peakgroup_df.columns)
        hmdb_row_hash_df = get_dimsresults_hmdb_link_df(peakgroup_df)

        dims_data_df = transform_dims_data(peakgroup_df)
        dims_dict = transform_dims_data_to_dict(dims_data_df, polarity, run_name)
        add_dimsresults_to_db(dims_dict, chunk_size)

        add_link_results_hmdb(hmdb_row_hash_df, chunk_size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "dir_name",
        type=str,
        help="Path to the directory containing the RData files",
    )

    args = parser.parse_args()
    main(args.dir_name)
