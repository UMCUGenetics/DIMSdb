from sqlmodel import Session, select

from dimsdb.archive.models import MeasuredMZ

def select_measuredmz_by_id(db_session: Session, id: int) -> MeasuredMZ:
    return db_session.get_one(MeasuredMZ, id)

def select_measuredmz_by_mz(db_session: Session, mz_start: float, mz_end: float) -> list[MeasuredMZ]:
    statement = (
        select(MeasuredMZ)
        .where(MeasuredMZ.mz >= mz_start)
        .where(MeasuredMZ.mz <= mz_end)
    )
    return db_session.exec(statement).all()

def insert_measuredmz(db_session: Session, measuredmz: MeasuredMZ) -> MeasuredMZ:
    try:
        db_session.add(measuredmz)
        db_session.commit()
        db_session.refresh(measuredmz)
    except Exception:
        db_session.rollback()
        raise
    return measuredmz

def update_measuredmz(db_session: Session, measuredmz: MeasuredMZ, measuredmz_data: dict) -> MeasuredMZ:
    try:
        measuredmz.sqlmodel_update(measuredmz_data)
        db_session.add(measuredmz)
        db_session.commit()
        db_session.refresh(measuredmz)
    except Exception:
        db_session.rollback()
        raise
    return measuredmz

def delete_measuredmz(db_session: Session, measuredmz: MeasuredMZ) -> None:
    try:
        db_session.delete(measuredmz)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
