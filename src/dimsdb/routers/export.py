from typing import Annotated
from fastapi import FastAPI, Query
from sqlmodel import Session, select, or_, col, func
import pandas as pd

from dimsdb.db.session import engine
from dimsdb.archive.models import Sample, DIMSRun, HMDB, DIMSResults

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "DIMSdb user"}


@app.get("/patient/info")
def get_patient_info(
    pat_id: Annotated[str, Query()],
    samp_id: Annotated[str, Query()],
    run_name: Annotated[str, Query()],
    matrix_type: Annotated[str, Query()],
):
    if len(samp_id) <= 1:
        samp_id = "%"
    if len(run_name) <= 1:
        run_name = "%"
    with Session(engine) as session:
        query = (
            select(Sample.patient_id, Sample.id, DIMSRun.name, DIMSRun.matrix)
            .join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id, isouter=True)
            .join(DIMSRun, onclause=DIMSRun.name == DIMSResults.run_name, isouter=True)
            .where(
                Sample.patient_id == pat_id,
                DIMSRun.matrix == matrix_type.upper(),
                or_(col(Sample.id).like(samp_id)),
                or_(col(DIMSRun.name).like(run_name)),
            )
            .distinct()
        )
        result = session.exec(query).all()
    return result


@app.get("/results/hmdb/iden/zscores/{zscore_min}/{zscore_max}")
def get_iden_results(
    run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()], zscore_min: float, zscore_max: float
):
    with Session(engine) as session:
        query_hmdb_adduct = (
            select(DIMSResults.row_hash, DIMSResultsHMDBLink.hmdb_id, DIMSResultsHMDBLink.adduct)
            .join(DIMSResults, onclause=DIMSResults.row_hash == DIMSResultsHMDBLink.row_hash, isouter=True)
            .where(
                col(DIMSResults.run_name).in_(run_names),
                col(DIMSResults.sample_id).in_(samples),
                or_(DIMSResults.z_score <= zscore_min, DIMSResults.z_score >= zscore_max),
            )
        )
        results_hmdb_adduct = session.exec(query_hmdb_adduct).all()

        results_hmdb_adduct = pd.DataFrame(results_hmdb_adduct, columns=["Row_hash", "HMDB_id", "Adduct"])
        row_hashes = results_hmdb_adduct.get("Row_hash").unique()
        hmdb_ids = results_hmdb_adduct.get("HMDB_id").to_list()
        adducts = set(results_hmdb_adduct.get("Adduct"))

        query_dimsresults = (
            select(DIMSResults, HMDB, DIMSResultsHMDBLink.adduct)
            .join(DIMSResultsHMDBLink, onclause=DIMSResults.row_hash == DIMSResultsHMDBLink.row_hash, isouter=True)
            .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_id, isouter=True)
            .where(
                col(DIMSResults.run_name).in_(run_names),
                col(DIMSResultsHMDBLink.hmdb_id).in_(hmdb_ids),
                col(DIMSResultsHMDBLink.adduct).in_(adducts),
                col(DIMSResults.row_hash).in_(row_hashes),
            )
        )

        results_dimsresults = session.exec(query_dimsresults).all()

    return results_dimsresults


@app.get("/results/hmdb/notiden/zscores/{zscore_min}/{zscore_max}")
def get_unident_results(
    run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()], zscore_min: float, zscore_max: float
):
    with Session(engine) as session:
        query = select(DIMSResults).where(
            col(DIMSResults.row_hash).in_(
                select(DIMSResults.row_hash)
                .join(DIMSResultsHMDBLink, onclause=DIMSResultsHMDBLink.row_hash == DIMSResults.uuid, isouter=True)
                .where(
                    col(DIMSResults.run_name).in_(run_names),
                    col(DIMSResults.sample_id).in_(samples),
                    or_(DIMSResults.z_score <= zscore_min, DIMSResults.z_score >= zscore_max),
                    col(DIMSResultsHMDBLink.row_hash).is_(None),
                )
            )
        )
        results = session.exec(query).all()

    return results


@app.get("/results/hmdb/all/zscores/{zscore_min}/{zscore_max}")
def get_all_results(
    run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()], zscore_min: float, zscore_max: float
):
    ident_results = get_iden_results(run_names, samples, zscore_min, zscore_max)
    unident_results = get_unident_results(run_names, samples, zscore_min, zscore_max)

    all_results = [ident_results, unident_results]
    all_results = pd.concat(all_results)

    return all_results


@app.get("/hmdb/info/hmdb_id/{hmdb_id}")
def get_hmdb_info(hmdb_id: str):
    if len(hmdb_id) == 9:
        with Session(engine) as session:
            query = select(HMDB).where(
                or_(col(HMDB.sec_hmdb_id).contains(hmdb_id + ";"), col(HMDB.sec_hmdb_id).endswith(hmdb_id))
            )
            results = session.exec(query).all()
    elif len(hmdb_id) == 11:
        with Session(engine) as session:
            query = select(HMDB).where(HMDB.hmdb_id == hmdb_id)
            results = session.exec(query).all()
    return results


@app.get("/hmdb/info/hmdb_name/{hmdb_name}")
def get_hmdb_info(hmdb_name: str):
    with Session(engine) as session:
        query = select(HMDB).where(func.upper(HMDB.name).contains(hmdb_name.upper()))
        results = session.exec(query).all()
    return results


@app.get("/results/metab/{zscore_min}/{zscore_max}")
def get_metab_results(hmdb_uuids: Annotated[list[str], Query()], zscore_min: float, zscore_max: float):
    with Session(engine) as session:
        query = (
            select(DIMSResults, DIMSResultsHMDBLink)
            .join(DIMSResultsHMDBLink, onclause=DIMSResultsHMDBLink.row_hash == DIMSResults.row_hash, isouter=True)
            .where(
                col(DIMSResultsHMDBLink.hmdb_id).in_(hmdb_uuids),
                or_(DIMSResults.z_score <= zscore_min, DIMSResults.z_score >= zscore_max),
            )
        )

        results = session.exec(query).all()
    return results
