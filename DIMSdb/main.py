from typing import Annotated
from fastapi import FastAPI, Query
from sqlmodel import Session, select, or_, col

from .database import engine
from .models import DIMSRun, DIMSResults, HMDB, Patient, Sample, DIMSResultsHMDBLink

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "DIMSdb user"}


@app.get("/dimsruns")
def get_dimsruns():
    with Session(engine) as session:
        query = select(DIMSRun)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}")
def get_dimsrun(name: str):
    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == name)
        result = session.exec(query).one_or_none()
    return result


@app.get("/dimsruns/{name}/results")
def get_dimsrun_result(name: str):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/samples/{id}/results")
def get_sample_result(name: str, id: str):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name, DIMSResults.sample_id == id)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/results/samples/{id}")
def get_dimsrun_samples(name: str, id: str):
    with Session(engine) as session:
        query = select(DIMSResults, Sample).join(Sample).where(DIMSResults.run_name == name,
                                                               DIMSResults.sample_id == id)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/results/samples/{id}/hmdb")
def get_dimsrun_samples(name: str, id: str):
    with Session(engine) as session:
        query = select(DIMSResults, HMDB).join(DIMSResultsHMDBLink,
                                               onclause=DIMSResults.uuid == DIMSResultsHMDBLink.run_uuid) \
            .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_uuid).where(DIMSResults.run_name == name,
                                                                                   DIMSResults.sample_id == id)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/samples/{id}/zscoremax/{zscoremax}")
def get_sample_zscoremax_result(name: str, id: str, zscoremax: float):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name,
                                          DIMSResults.sample_id == id, DIMSResults.z_score >= zscoremax)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/samples/{id}/zscoremax/{zscoremax}/hmdb")
def get_sample_zscoremax_result(name: str, id: str, zscoremax: float):
    with Session(engine) as session:
        query = select(DIMSResults, HMDB).join(DIMSResultsHMDBLink,
                                               onclause=DIMSResults.uuid == DIMSResultsHMDBLink.run_uuid,
                                               isouter=True) \
            .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_uuid, isouter=True).where(
            DIMSResults.run_name == name,
            DIMSResults.sample_id == id,
            DIMSResults.z_score >= zscoremax)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/samples/{id}/zscoremin/{zscoremin}")
def get_sample_zscoremin_result(name: str, id: str, zscoremin: float):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name, DIMSResults.sample_id == id,
                                          DIMSResults.z_score <= zscoremin)
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/samples/{id}/zscores/{zscoremin}/{zscoremax}")
def get_sample_zscores_result(name: str, id: str, zscoremin: float, zscoremax: float):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name, DIMSResults.sample_id == id,
                                          or_(DIMSResults.z_score <= zscoremin, DIMSResults.z_score >= zscoremax))
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{name}/patient/samples")
def get_patient_samples_runs(name: str):
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name).join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id,
                                                  isouter=True).join(DIMSRun,
                                                                     onclause=DIMSRun.name == DIMSResults.run_name,
                                                                     isouter=True).where(
            DIMSRun.name == name).distinct()
        result = session.exec(query).all()
    return result


@app.get("/test/dimsruns/{name}/wildcard")
def get_wildcard(name: str):
    with Session(engine) as session:
        query = select(DIMSRun).where(col(DIMSRun.name).contains(name))
        result = session.exec(query).all()
    return result


@app.get("/hmdbs/{id}")
def get_hmdb(id: str):
    with Session(engine) as session:
        query = select(HMDB).where(HMDB.hmdb_id == id)
        result = session.exec(query).one_or_none()
    return result


@app.get("/hmdbs")
def get_hmdb():
    with Session(engine) as session:
        query = select(HMDB)
        result = session.exec(query).all()
    return result


@app.get("/patients")
def get_patients():
    with Session(engine) as session:
        query = select(Patient)
        result = session.exec(query).all()
    return result


@app.get("/patients/{id}")
def get_patient(id: str):
    with Session(engine) as session:
        query = select(Patient).where(Patient.intermediate_id == id)
        result = session.exec(query).all()
    return result


@app.get("/patients/{id}/samples")
def get_patient_samples(id: str):
    with Session(engine) as session:
        query = select(Sample).where(Sample.patient_id == id)
        result = session.exec(query).all()
    return result


@app.get("/patients/{id}/samples/runs")
def get_patient_samples_runs(id: str):
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name).join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id,
                                                  isouter=True).join(DIMSRun,
                                                                     onclause=DIMSRun.name == DIMSResults.run_name,
                                                                     isouter=True).where(
            Sample.patient_id == id).distinct()
        result = session.exec(query).all()
    return result


@app.get("/samples")
def get_samples():
    with Session(engine) as session:
        query = select(Sample)
        result = session.exec(query).all()
    return result


@app.get("/samples/{id}")
def get_sample(id: str):
    with Session(engine) as session:
        query = select(Sample).where(Sample.id == id)
        result = session.exec(query).one_or_none()
    return result


@app.get("/samples/{id}/runs")
def get_patient_samples_runs(id: str):
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name).join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id,
                                                  isouter=True).join(DIMSRun,
                                                                     onclause=DIMSRun.name == DIMSResults.run_name,
                                                                     isouter=True).where(Sample.id == id).distinct()
        result = session.exec(query).all()
    return result


@app.get("/matrix/{type}/patient/samples/runs")
def get_matrix_patient_samples_runs(type: str):
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name).join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id,
                                                  isouter=True).join(DIMSRun,
                                                                     onclause=DIMSRun.name == DIMSResults.run_name,
                                                                     isouter=True).where(Sample.type == type).distinct()
        result = session.exec(query).all()
    return result


@app.get("/dimsruns/{run_name}/patient/{patient_id}/samples/{sample_id}/matrix/{matrix_type}")
def get_run_patient_sample_matrix_info(run_name: str, patient_id: str, sample_id: str, matrix_type: str):
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name).join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id,
                                                  isouter=True).join(DIMSRun,
                                                                     onclause=DIMSRun.name == DIMSResults.run_name,
                                                                     isouter=True) \
            .where(or_(DIMSRun.name == run_name,
                       Sample.id == sample_id,
                       Sample.patient_id == patient_id,
                       Sample.type == matrix_type)).distinct()
        result = session.exec(query).all()
    return result


@app.get("/runs/info")
def get_patient_samples_runs(run_names: Annotated[list[str], Query()]):
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name).join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id,
                                                  isouter=True) \
            .join(DIMSRun, onclause=DIMSRun.name == DIMSResults.run_name, isouter=True) \
            .where(col(DIMSRun.name).in_(run_names)).distinct()
        result = session.exec(query).all()
    return result


@app.get("/patient/info")
def get_patient_info(pat_id: Annotated[str, Query()], samp_id: Annotated[str, Query()],
                     run_name: Annotated[str, Query()], matrix_type: Annotated[str, Query()]):
    if len(samp_id) < 1:
        samp_id = '%'
    if len(run_name) < 1:
        run_name = '%'
    with Session(engine) as session:
        query = select(Sample, DIMSRun.name) \
            .join(DIMSResults, onclause=DIMSResults.sample_id == Sample.id, isouter=True) \
            .join(DIMSRun, onclause=DIMSRun.name == DIMSResults.run_name, isouter=True) \
            .where(Sample.patient_id == pat_id,
                   Sample.type == matrix_type,
                   or_(col(Sample.id).like(samp_id)),
                   or_(col(DIMSRun.name).like(run_name))).distinct()
        result = session.exec(query).all()
    return result


@app.get("/results/hmdb/{iden}/zscores/{zscoremin}/{zscoremax}")
def get_results_hmdb(run_names: Annotated[list[str], Query()], samples: Annotated[list[str], Query()],
                     iden: str, zscoremin: float, zscoremax: float):
    with Session(engine) as session:
        if iden == "iden":
            query = select(DIMSResults, HMDB) \
                .join(DIMSResultsHMDBLink, onclause=DIMSResults.uuid == DIMSResultsHMDBLink.run_uuid, isouter=True) \
                .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_uuid, isouter=True) \
                .where(col(DIMSResults.run_name).in_(run_names),
                       col(DIMSResultsHMDBLink.hmdb_uuid).in_(
                           select(DIMSResultsHMDBLink.hmdb_uuid) \
                               .join(DIMSResults, onclause=DIMSResultsHMDBLink.run_uuid == DIMSResults.uuid,
                                     isouter=True) \
                               .where(col(DIMSResults.run_name).in_(run_names),
                                      col(DIMSResults.sample_id).in_(samples),
                                      col(DIMSResultsHMDBLink.hmdb_uuid).is_not(None),
                                      or_(DIMSResults.z_score <= zscoremin, DIMSResults.z_score >= zscoremax))
                       )
                ).distinct()
        elif iden == "not_iden":
            query = select(DIMSResults, HMDB) \
                .join(DIMSResultsHMDBLink, onclause=DIMSResults.uuid == DIMSResultsHMDBLink.run_uuid, isouter=True) \
                .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_uuid, isouter=True) \
                .where(col(DIMSResults.run_name).in_(run_names),
                       col(DIMSResultsHMDBLink.hmdb_uuid).in_(
                           select(DIMSResultsHMDBLink.hmdb_uuid) \
                               .join(DIMSResults, onclause=DIMSResultsHMDBLink.run_uuid == DIMSResults.uuid,
                                     isouter=True) \
                               .where(col(DIMSResults.run_name).in_(run_names),
                                      col(DIMSResults.sample_id).in_(samples),
                                      col(DIMSResultsHMDBLink.hmdb_uuid).is_(None),
                                      or_(DIMSResults.z_score <= zscoremin, DIMSResults.z_score >= zscoremax))
                       )
                ).distinct()
        elif iden == "all":
            query = select(DIMSResults, HMDB) \
                .join(DIMSResultsHMDBLink, onclause=DIMSResults.uuid == DIMSResultsHMDBLink.run_uuid, isouter=True) \
                .join(HMDB, onclause=HMDB.uuid == DIMSResultsHMDBLink.hmdb_uuid, isouter=True) \
                .where(col(DIMSResults.run_name).in_(run_names),
                       col(DIMSResultsHMDBLink.hmdb_uuid).in_(
                           select(DIMSResultsHMDBLink.hmdb_uuid) \
                               .join(DIMSResults, onclause=DIMSResultsHMDBLink.run_uuid == DIMSResults.uuid,
                                     isouter=True) \
                               .where(col(DIMSResults.run_name).in_(run_names),
                                      col(DIMSResults.sample_id).in_(samples),
                                      or_(DIMSResults.z_score <= zscoremin, DIMSResults.z_score >= zscoremax))
                       )
                ).distinct()
        result = session.exec(query).all()
    return result
