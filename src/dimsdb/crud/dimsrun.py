from sqlmodel import Session

from dimsdb.archive.models import DIMSRun

def select_dimsrun_by_id(db_session: Session, run_id: str) -> DIMSRun:
    return db_session.get_one(DIMSRun, run_id)

def insert_dimsrun(db_session: Session, run: DIMSRun) -> DIMSRun:
    try:
        db_session.add(run)
        db_session.commit()
        db_session.refresh(run)
    except Exception:
        db_session.rollback()
        raise
    return run

def update_dimsrun(db_session: Session, dimsrun: DIMSRun, run_data: dict) -> DIMSRun:
    try:
        dimsrun.sqlmodel_update(run_data)
        db_session.add(dimsrun)
        db_session.commit()
        db_session.refresh(dimsrun)
    except Exception:
        db_session.rollback()
        raise
    return dimsrun

def delete_dimsrun(db_session: Session, dimsrun: DIMSRun) -> None:
    try:
        db_session.delete(dimsrun)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
