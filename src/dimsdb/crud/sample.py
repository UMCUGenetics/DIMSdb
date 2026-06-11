from sqlmodel import Session

from dimsdb.archive.models import Sample

def select_sample_by_id(db_session: Session, sample_id: str) -> Sample:
    return db_session.get_one(Sample, sample_id)

def insert_sample(db_session: Session, sample: Sample) -> Sample:
    try:
        db_session.add(sample)
        db_session.commit()
        db_session.refresh(sample)
    except Exception:
        db_session.rollback()
        raise
    return sample

def update_sample(db_session: Session, sample: Sample, sample_data: dict) -> Sample:
    try:
        sample.sqlmodel_update(sample_data)
        db_session.add(sample)
        db_session.commit()
        db_session.refresh(sample)
    except Exception:
        db_session.rollback()
        raise
    return sample

def delete_sample(db_session: Session, sample: Sample) -> None:
    try:
        db_session.delete(sample)
        db_session.commit()
    except Exception:
        db_session.rollback()
    raise
