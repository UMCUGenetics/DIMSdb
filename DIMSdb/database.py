from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine
# from .models import DIMSRun, DIMSResults, Patient, Sample
import models
import pathlib
import configparser

config = configparser.ConfigParser()
config.read(f'{pathlib.Path(__file__).parent.parent.absolute()}/config.ini')

sql_protocol = config.get('database', 'sql_protocol')
database_name_or_url = config.get('database', 'database_name_or_url')

sql_url = f'{sql_protocol}{database_name_or_url}'

engine = create_engine(sql_url)


def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
