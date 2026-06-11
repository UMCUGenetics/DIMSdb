from pandas import DataFrame
from sqlmodel import Session, select, col, or_

from dimsdb.models.hmdb import HMDB

def select_hmdb_by_hmdb_id(db_session: Session, hmdb_id: str) -> HMDB:
    statement = select(HMDB).where(HMDB.hmdb_id == hmdb_id)
    return db_session.exec(statement).first()

def select_hmdbs_by_hmdb_key(db_session: Session, hmdb_key: str) -> list[HMDB]:
    statement = select(HMDB).where(HMDB.hmdb_key == hmdb_key)
    return db_session.exec(statement).all()

def select_hmdb_by_sec_hmdb_id(db_session: Session, hmdb_id: str) -> list[HMDB]:
    statement = (
        select(HMDB).
        where(or_(col(HMDB.sec_hmdb_id).contains(hmdb_id + ";"), col(HMDB.sec_hmdb_id).endswith(hmdb_id)))
    )
    return db_session.exec(statement).all()

def insert_hmdb(db_session: Session, hmdb: HMDB) -> HMDB:
    try:
        db_session.add(hmdb)
        db_session.commit()
        db_session.refresh(hmdb)
    except Exception:
        db_session.rollback()
        raise
    return hmdb

def insert_hmdb_table(db_session: Session, hmdb_df: DataFrame) -> None:
    try:
        with db_session.begin() as conn:
            hmdb_df.to_sql(name='hmdb', con=conn, index=False, if_exists='append', chunksize=5000)
    except Exception:
        db_session.rollback()
        raise

def update_hmdb(db_session: Session, hmdb: HMDB, hmdb_data: dict) -> HMDB:
    try:
        hmdb.sqlmodel_update(hmdb_data)
        db_session.add(hmdb)
        db_session.commit()
        db_session.refresh(hmdb)
    except Exception:
        db_session.rollback()
        raise
    return hmdb

def delete_hmdb(db_session: Session, hmdb: HMDB) -> None:
    try:
        db_session.delete(hmdb)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
