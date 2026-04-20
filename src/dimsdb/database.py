from sqlmodel import create_engine, SQLModel
from dimsdb.config import Settings

engine = create_engine(Settings.DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
