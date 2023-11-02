from sqlmodel import Session, SQLModel, create_engine
from .models import Sample, Patient

sqlite_file_name = "db.sqlite3"  # Todo: Move to config
sqlite_url = f"sqlite:///{sqlite_file_name}"  # Todo: Move to config

engine = create_engine(sqlite_url)


def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        p1 = Patient(intermediate_id="p1", birth_year=1989)
        s1 = Sample(id="p1.1", type="blood", patient=p1)
        s2 = Sample(id="p1.2", type="blood", patient=p1)

        p2 = Patient(intermediate_id="p2", birth_year=1989)
        s3 = Sample(id="p2.1", type="plasma", patient=p2)
        s4 = Sample(id="p2.2", type="plasma", patient=p2)

        session.add_all([p1, s1, s2, p2, s3, s4])
        session.commit()
