from fastapi import FastAPI
from sqlmodel import Session, select

from .database import engine
from .models import HMDB, Patient

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/hmdb/{id}")
def get_hmdb(id: str):
    with Session(engine) as session:
        query = select(HMDB).where(HMDB.id == id)
        result = session.exec(query).one_or_none()
    return result


@app.get("/patient/")
def get_patients():
    with Session(engine) as session:
        query = select(Patient)
        result = session.exec(query).all()
    return result
