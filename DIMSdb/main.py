from fastapi import FastAPI
from sqlmodel import Session, select

from .database import engine
from .models import DIMSRun, DIMSResults, HMDB, Patient, Sample

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "DIMSdb user"}


@app.get("/dimsrun/{name}")
def get_dimsrun(name: str):
    with Session(engine) as session:
        query = select(DIMSRun).where(DIMSRun.name == name)
        result = session.exec(query).one_or_none()
    return result


@app.get("/dimsrun/{name}/results")
def get_dimsrun_result(name: str):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name)
        result = session.exec(query).all()
    return result


@app.get("/dimsrun/{name}/sample/{id}/results")
def get_sample_result(name: str, id: str):
    with Session(engine) as session:
        query = select(DIMSResults).where(DIMSResults.run_name == name).where(DIMSResults.sample_id == id)
        result = session.exec(query).one_or_none()
    return result


@app.get("/hmdbs/{id}")
def get_hmdb(id: str):
    with Session(engine) as session:
        query = select(HMDB).where(HMDB.id == id)
        result = session.exec(query).one_or_none()
    return result


@app.get("/patients/")
def get_patients():
    with Session(engine) as session:
        query = select(Patient)
        result = session.exec(query).all()
    return result


@app.get("/patients/{id}")
def get_patient():
    with Session(engine) as session:
        query = select(Patient).where(Patient.id == id)
        result = session.exec(query).all()
    return result


@app.get("/patient/{id}/samples/")
def get_patient_samples(id: str):
    with Session(engine) as session:
        query = select(Sample).where(Sample.patient_id == id)
        result = session.exec(query).all()
    return result


@app.get("/sample/{id}")
def get_samples(id: str):
    with Session(engine) as session:
        query = select(Sample)
        result = session.exec(query).all()
    return result
