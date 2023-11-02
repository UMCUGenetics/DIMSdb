from fastapi import FastAPI
from sqlmodel import Session, select

from .database import engine, create_db_and_tables
from .models import HMDB

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/hmdb/{id}")
def get_hmdb(id: str):
    with Session(engine) as session:
        query = select(HMDB).where(HMDB.id == id)
        result = session.exec(query).one_or_none()
    return result
