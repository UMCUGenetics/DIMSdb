from fastapi import FastAPI
from sqlmodel import Session, select, or_, join

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
