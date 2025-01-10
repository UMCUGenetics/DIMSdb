from typing import Annotated
from fastapi import FastAPI, Query
from sqlmodel import Session, select, or_, col
import pandas as pd

from .database import engine
from .models import DIMSRun, DIMSResults, HMDB, Patient, Sample, DIMSResultsHMDBLink

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "DIMSdb user"}


@app.get("/patient/info")
def get_patient_info(pat_id: Annotated[str, Query()], samp_id: Annotated[str, Query()],
                     run_name: Annotated[str, Query()], matrix_type: Annotated[str, Query()]):
    if len(samp_id) <= 1:
        samp_id = '%'
    if len(run_name) <= 1:
        run_name = '%'
    with Session(engine) as session:
        query = select(Sample.patient_id, Sample.id, DIMSRun.name, DIMSRun.matrix) \
            .join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id, isouter=True) \
            .join(DIMSRun, onclause=DIMSRun.name == DIMSResults.run_name, isouter=True) \
            .where(Sample.patient_id == pat_id,
                   DIMSRun.matrix == matrix_type.upper(),
                   or_(col(Sample.id).like(samp_id)),
                   or_(col(DIMSRun.name).like(run_name))).distinct()
        result = session.exec(query).all()
    return result


@app.get("/results/hmdb/iden/zscores/{zscore_min}/{zscore_max}")
def get_iden_results(run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()],
                     zscore_min: float, zscore_max: float):
    with Session(engine) as session:
        query_hmdb_adduct = select(DIMSResults.row_hash, DIMSResultsHMDBLink.hmdb_id, DIMSResultsHMDBLink.adduct) \
            .join(DIMSResults, onclause=DIMSResults.uuid == DIMSResultsHMDBLink.result_id, isouter=True) \
            .where(col(DIMSResults.run_name).in_(run_names),
                   col(DIMSResults.sample_id).in_(samples),
                   or_(DIMSResults.z_score <= zscore_min, DIMSResults.z_score >= zscore_max))
        results_hmdb_adduct = session.exec(query_hmdb_adduct).all()

        results_hmdb_adduct = pd.DataFrame(results_hmdb_adduct, columns=['Row_hash', 'HMDB_id', 'Adduct'])
        row_hashes = results_hmdb_adduct.get('Row_hash').unique()
        hmdb_ids = results_hmdb_adduct.get("HMDB_id").to_list()
        adducts = set(results_hmdb_adduct.get("Adduct"))

        query_dimsresults = select(DIMSResults, HMDB, DIMSResultsHMDBLink.adduct) \
            .join(DIMSResultsHMDBLink, onclause=DIMSResults.uuid == DIMSResultsHMDBLink.result_id, isouter=True) \
            .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_id, isouter=True) \
            .where(col(DIMSResults.run_name).in_(run_names),
                   col(DIMSResultsHMDBLink.hmdb_id).in_(hmdb_ids),
                   col(DIMSResultsHMDBLink.adduct).in_(adducts),
                   col(DIMSResults.row_hash).in_(row_hashes))

        results_dimsresults = session.exec(query_dimsresults).all()

    return results_dimsresults


@app.get("/results/hmdb/notiden/zscores/{zscore_min}/{zscore_max}")
def get_unident_results(run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()],
                        zscore_min: float, zscore_max: float):
    with Session(engine) as session:
        query = select(DIMSResults) \
            .where(col(DIMSResults.row_hash).in_(
                select(DIMSResults.row_hash).join(DIMSResultsHMDBLink,
                                                  onclause=DIMSResultsHMDBLink.result_id == DIMSResults.uuid, isouter=True) \
                    .where(col(DIMSResults.run_name).in_(run_names),
                           col(DIMSResults.sample_id).in_(samples),
                           or_(DIMSResults.z_score <= zscore_min, DIMSResults.z_score >= zscore_max),
                           col(DIMSResultsHMDBLink.result_id).is_(None)))
                   )
        results = session.exec(query).all()

    return results


@app.get("/results/hmdb/all/zscores/{zscore_min}/{zscore_max}")
def get_all_results(run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()],
                    zscore_min: float, zscore_max: float):
    ident_results = get_iden_results(run_names, samples, zscore_min, zscore_max)
    unident_results = get_unident_results(run_names, samples, zscore_min, zscore_max)

    all_results = [ident_results, unident_results]
    all_results = pd.concat(all_results)

    return all_results
