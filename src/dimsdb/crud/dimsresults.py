from sqlmodel import Session

from dimsdb.archive.models import DIMSResults


def select_dimsresults_by_id(db_session: Session, dimsresults_id: int) -> DIMSResults:
    return db_session.get_one(DIMSResults, dimsresults_id)

def insert_dimsresults(db_session: Session, dimsresults: DIMSResults) -> DIMSResults:
    try:
        db_session.add(dimsresults)
        db_session.commit()
        db_session.refresh(dimsresults)
    except Exception:
        db_session.rollback()
        raise
    return dimsresults

def update_dimsresults(db_session: Session, dimsresults: DIMSResults, dimsresults_data: dict) -> DIMSResults:
    try:
        dimsresults.sqlmodel_update(dimsresults_data)
        db_session.add(dimsresults)
        db_session.commit()
        db_session.refresh(dimsresults)
    except Exception:
        db_session.rollback()
        raise
    return dimsresults

def delete_dimsresults(db_session: Session, dimsresults: DIMSResults) -> None:
    try:
        db_session.delete(dimsresults)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
