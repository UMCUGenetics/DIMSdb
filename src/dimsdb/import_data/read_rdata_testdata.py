import base64
import os
import re
from datetime import datetime
import time
import pandas as pd
import rdata  # https://github.com/vnmabus/rdata
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select, col, or_
from add_functions import add_patient, add_sample, add_dims_run
from dimsdb.models.models import Patient, Sample, DIMSRun, DIMSResults, HMDB, DIMSResultsHMDBLink
from dimsdb.database import engine


def parse_rdata_file(file):
    """

    :param file:
    :return:
    """
    # read the RData file
    parsed = rdata.parser.parse_file(file)
    result = rdata.conversion.convert(parsed)

    return result


def get_row_hash(row):
    hash_row = str(round(row["mzmed.pgrp"], 5)) + str(time.time())
    hash_row = base64.b64encode(hash_row.encode("ascii")).decode("ascii")
    return hash_row


def parse_settings_file(file, run_name):
    """

    :param file:
    :param run_name:
    :return:
    """
    settings_df = pd.read_table(file, sep="=")
    # rename the first column to "value"
    settings_df = settings_df.set_axis(["value"], axis=1)

    # get run date
    run_date = re.search("202[0-9]{5}", run_name)
    if run_date is not None:
        run_date = run_date.group(0)
    else:
        run_date = re.search("202[0-9]", run_name)
        if run_date is not None:
            run_date = run_date.group(0) + "0101"
        else:
            run_date = "20000101"
    run_date = datetime.fromisoformat(run_date)

    return settings_df, run_date


def add_dimsrun_db(settings_file, run_name):
    settings_df, run_date = parse_settings_file(settings_file, run_name)

    # check if run is present, if not add to the database
    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == run_name)
        dimsrun = session.exec(query).one_or_none()

        if not dimsrun:
            dimsrun = add_dims_run(
                run_name,
                settings_df.at["email", "value"],
                settings_df.at["nrepl", "value"],
                run_date,
                5,
                settings_df.at["resol", "value"],
                settings_df.at["matrix", "value"].upper(),
            )
            session.add(dimsrun)
            session.commit()


def add_hmdb_dimsresults(dimsresult, hmdb_code, session):
    print(dimsresult.uuid)
    results = session.query(HMDB).filter(
        col(HMDB.sec_hmdb_id).like(hmdb_code + ";"), or_(col(HMDB.sec_hmdb_id).endswith(hmdb_code))
    )
    hmdbs = results.all()
    dimsresult.hmdb = hmdbs
    session.add(dimsresult)
    session.commit()


def get_samples_run(file_pos, file_neg):
    sample_ids = []

    for file in [file_pos, file_neg]:
        result = parse_rdata_file(file)
        # use only identified part, both parts contain the same samples
        identified_df = result["outlist.ident"]

        cols_no_samples = [
            "HMDB_code",
            "assi_HMDB",
            "assi_noise",
            "avg.ctrls",
            "avg.int",
            "fq.best",
            "fq.worst",
            "iso_HMDB",
            "mzmax.pgrp",
            "mzmed.pgrp",
            "mzmin.pgrp",
            "nrsamples",
            "ppmdev",
            "sd.ctrls",
            "theormz_HMDB",
            "theormz_noise",
        ]

        sample_ids.extend(
            [col_name for col_name in identified_df.columns if col_name not in cols_no_samples and "_Zscore" not in col_name]
        )

    sample_ids = list(set(sample_ids))

    return sample_ids


def add_samples_patients_db(file_pos, file_neg):
    sample_ids = get_samples_run(file_pos, file_neg)

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


def get_data_run(file):
    result = parse_rdata_file(file)

    # split data into identified and unidentified part
    identified = result["outlist.ident"]
    unidentified = result["outlist.not.ident"]

    # merge the two parts
    merged_df = pd.concat((identified, unidentified))

    merged_df["row_hash"] = merged_df.apply(get_row_hash, axis=1)

    hmdb_row_hash_df = get_dimsresults_hmdb_link_df(merged_df)

    # drop unused columns
    merged_df = merged_df.drop(
        [
            "fq.best",
            "fq.worst",
            "nrsamples",
            "mzmin.pgrp",
            "mzmax.pgrp",
            "iso_HMDB",
            "theormz_HMDB",
            "avg.int",
            "assi_noise",
            "theormz_noise",
            "avg.ctrls",
            "sd.ctrls",
        ],
        axis=1,
    )

    # melt and pivot the table to get for each sample a row with the intensity and zscore
    merged_df_melt = merged_df.melt(
        id_vars=["mzmed.pgrp", "ppmdev", "assi_HMDB", "HMDB_code", "row_hash"], var_name="Sample_Type", value_name="Intensity"
    )
    merged_df_melt[["Sample", "Type"]] = merged_df_melt["Sample_Type"].str.extract(r"(.+?)(?:_(Zscore))?$")
    merged_df_pivot = merged_df_melt.pivot(
        index=["mzmed.pgrp", "ppmdev", "assi_HMDB", "HMDB_code", "row_hash", "Sample"], columns="Type", values="Intensity"
    ).reset_index()
    # rename columns
    merged_df_pivot.columns = ["mzmed.pgrp", "ppmdev", "assi_HMDB", "HMDB_code", "row_hash", "Sample", "Intensity", "Zscore"]

    # change HMDB_code values to list
    merged_df_pivot["HMDB_code"].fillna("", inplace=True)
    merged_df_pivot["HMDB_code"] = merged_df_pivot["HMDB_code"].str.split(";")
    # change assi_HMDB values to list
    merged_df_pivot["assi_HMDB"].fillna("", inplace=True)
    merged_df_pivot["assi_HMDB"] = merged_df_pivot["assi_HMDB"].str.split(";")  # string to list
    merged_df_pivot = merged_df_pivot.reset_index(drop=True)

    return merged_df_pivot, hmdb_row_hash_df


def get_dimsresults_dict(dimsresults_df, polarity, run_name):
    dimsresults_df = dimsresults_df.drop(["assi_HMDB"], axis=1)
    dimsresults_df.columns = ["m_z", "ppm_dev", "HMDB_code", "row_hash", "sample_id", "intensity", "z_score"]

    if polarity == "positive":
        pol = True
    else:
        pol = False

    dimsresults_df["polarity"] = pol
    dimsresults_df["run_name"] = run_name

    dimsresults_dict = dimsresults_df.to_dict(orient="records")
    return dimsresults_dict


def split_assi_hmdb(df_col):
    reg_pattern = r"(?<!&gt)(?<!&lt)(?<!&amp)(?<!2235)(?<!awR\))(?<!&alpha);"
    return re.split(reg_pattern, df_col)


def get_dimsresults_hmdb_link_df(merged_df):
    hmdb_row_hash_df = merged_df[["HMDB_code", "assi_HMDB", "theormz_HMDB", "row_hash"]]
    hmdb_row_hash_df = hmdb_row_hash_df.dropna()
    hmdb_row_hash_df["HMDB_code"] = hmdb_row_hash_df["HMDB_code"].str.split(";")
    hmdb_row_hash_df["assi_HMDB"] = hmdb_row_hash_df["assi_HMDB"].apply(split_assi_hmdb)
    hmdb_row_hash_df = hmdb_row_hash_df.explode(["HMDB_code", "assi_HMDB"])
    hmdb_row_hash_df = hmdb_row_hash_df.drop_duplicates()
    hmdb_row_hash_df[["HMDB_code", "adduct"]] = hmdb_row_hash_df["HMDB_code"].str.extract(r"(HMDB\d+)_?(\d+)?")
    hmdb_row_hash_df["adduct"] = hmdb_row_hash_df["adduct"].fillna(0).astype(int)
    hmdb_row_hash_df["assi_HMDB"] = hmdb_row_hash_df["assi_HMDB"].str.replace(r"\[M.*", "", regex=True).str.strip()

    return hmdb_row_hash_df


def add_dimsresults(file, polarity, run_name, size_chunk):
    dimsresults_df, hmdb_row_hash_dict = get_data_run(file)
    dimsresults_dict = get_dimsresults_dict(dimsresults_df, polarity, run_name)

    with Session(engine) as session:
        for i in range(0, len(dimsresults_dict), size_chunk):
            session.execute(insert(DIMSResults), dimsresults_dict[i : i + size_chunk])
            session.commit()

    return hmdb_row_hash_dict


def get_dimsresults_hmdb_link(hmdb_code_list, size_chunk):
    like_clauses = []
    hmdb_uuid_code_df = pd.DataFrame()

    for hmdb_code in hmdb_code_list:
        like_clauses.append(col(HMDB.sec_hmdb_id).contains(f"{hmdb_code};%"))
        like_clauses.append(col(HMDB.sec_hmdb_id).endswith(hmdb_code))

    with Session(engine) as session:
        for i in range(0, len(like_clauses), size_chunk):
            like_clauses_chunk = like_clauses[i : i + size_chunk]
            query = select(HMDB.uuid, HMDB.sec_hmdb_id).where(or_(*like_clauses_chunk))
            result = session.exec(query).all()
            result_df = pd.DataFrame(result, columns=["uuid", "sec_hmdb_id"])
            hmdb_uuid_code_df = pd.concat([hmdb_uuid_code_df, result_df])

    return hmdb_uuid_code_df


def add_new_hmdb(hmdb_info):
    hmdb_info = hmdb_info.rename(columns={"assi_HMDB": "name", "theormz_HMDB": "theor_mz"})
    hmdb_info["hmdb_key"], hmdb_info["hmdb_id"], hmdb_info["sec_hmdb_id"] = (
        hmdb_info["HMDB_code"],
        hmdb_info["HMDB_code"],
        hmdb_info["HMDB_code"],
    )
    hmdb_info = hmdb_info.drop(["HMDB_code"], axis=1)
    hmdb_info_dict = hmdb_info.to_dict(orient="records")

    with Session(engine) as session:
        session.execute(insert(HMDB), hmdb_info_dict)
        session.commit()


def add_hmdb_results_link(row_hash_adduct_uuid, size_chunk):
    row_hash_adduct_uuid = row_hash_adduct_uuid.to_dict(orient="records")

    with Session(engine) as session:
        for i in range(0, len(row_hash_adduct_uuid), size_chunk):
            session.execute(insert(DIMSResultsHMDBLink), row_hash_adduct_uuid[i : i + size_chunk])
            session.commit()


def add_link_results_hmdb(hmdb_row_hash_df, size_chunk):
    # Divide size_chunk by 20, because there are fewer records to be added
    size_chunk = int(size_chunk / 20)
    # Get uuid for the hmdb codes
    hmdb_row_hash_df = hmdb_row_hash_df.dropna(subset=["HMDB_code"])
    hmdb_uuid_code_df = get_dimsresults_hmdb_link(hmdb_row_hash_df["HMDB_code"].unique(), size_chunk)
    hmdb_uuid_code_df = hmdb_uuid_code_df.reset_index(drop=True)

    # Get a list of all unique hmdb codes present in the DIMSResultsHMDBLink table
    sec_hmdb_ids_col = hmdb_uuid_code_df["sec_hmdb_id"].str.split(";").explode()
    sec_hmdb_ids_list = set(sec_hmdb_ids_col)

    # Get hmdb codes that are not present in the DIMSResultsHMDBLink table
    hmdb_not_present = list(set(hmdb_row_hash_df["HMDB_code"]) - sec_hmdb_ids_list)
    if len(hmdb_not_present) > 0:
        print(hmdb_not_present)
        hmdb_info_not_present = hmdb_row_hash_df[hmdb_row_hash_df["HMDB_code"].isin(hmdb_not_present)]

        # Add the HMDB info for the hmdb codes that are not present in the DIMSResultsHMDBLink table
        add_new_hmdb(hmdb_info_not_present)

        # Get the uuids for the newly added hmdb codes
        new_hmdb_results_link_df = get_dimsresults_hmdb_link(hmdb_info_not_present["HMDB_code"].unique(), size_chunk)
        # Combine all uuid info for all hmdb codes
        hmdb_uuid_code_df = pd.concat([hmdb_uuid_code_df, new_hmdb_results_link_df])

    # Get the correct combination of uuid and hmdb code
    hmdb_uuid_code_df = hmdb_uuid_code_df.assign(sec_hmdb_id=hmdb_uuid_code_df["sec_hmdb_id"].str.split(";")).explode(
        "sec_hmdb_id"
    )
    uuid_hmdb_link_df = hmdb_uuid_code_df[hmdb_uuid_code_df["sec_hmdb_id"].isin(hmdb_row_hash_df["HMDB_code"])]
    uuid_hmdb_link_df = uuid_hmdb_link_df.rename(columns={"uuid": "hmdb_id", "sec_hmdb_id": "HMDB_code"})

    # Combine the uuid with row hash and adduct info
    merged_link_info = pd.merge(hmdb_row_hash_df, uuid_hmdb_link_df, on="HMDB_code", how="left")
    row_hash_adduct_uuid = merged_link_info[["hmdb_id", "row_hash", "adduct"]].drop_duplicates()
    row_hash_adduct_uuid[["hmdb_id"]] = row_hash_adduct_uuid[["hmdb_id"]].astype(int)
    row_hash_adduct_uuid[["row_hash"]] = row_hash_adduct_uuid[["row_hash"]].astype(str)

    # Add the new uuid-row hash in the DIMSResultsHMDBLink table
    add_hmdb_results_link(row_hash_adduct_uuid, size_chunk)


def main():
    # Update run_name with folder name of data to be inserted
    print("start")
    print(datetime.now())

    size_chunk = 10000

    path_name = "/Users/aluesin2/Documents/DIMSdb/test_data/"
    run_names = [f for f in os.listdir(path_name) if not f.startswith(".")]
    print(run_names)

    # run_names = ["test_long", "test_wide"] # 2 tests, one with all columns, one with all rows
    # run_names = ["TEST_20241115_RUN9"]

    for run_name in run_names:
        print(run_name)
        settings_file = path_name + run_name + "/settings.config"
        file_neg = path_name + run_name + "/outlist_identified_negative.RData"
        file_pos = path_name + run_name + "/outlist_identified_positive.RData"

        # Add DIMS run info to the database
        add_dimsrun_db(settings_file, run_name)
        # Add sample and patient info to the database
        add_samples_patients_db(file_pos, file_neg)

        # Add DIMS results data to the database for the negative scan modus
        hmdb_row_hash_dict_neg = add_dimsresults(file_neg, "negative", run_name, size_chunk)
        add_link_results_hmdb(hmdb_row_hash_dict_neg, size_chunk)
        # Add DIMS results data to the database for the positive scan modus
        hmdb_row_hash_dict_pos = add_dimsresults(file_pos, "positive", run_name, size_chunk)
        add_link_results_hmdb(hmdb_row_hash_dict_pos, size_chunk)

    print(datetime.now())
    print("___ Data done ___")


if __name__ == "__main__":
    main()
