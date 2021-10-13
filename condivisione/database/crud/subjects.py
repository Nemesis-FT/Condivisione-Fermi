from fastapi import HTTPException
from sqlalchemy.orm import Session
from condivisione.database import schemas, models
from condivisione.database.crud.common import commit


def get_subject(db: Session, id: int) -> models.Subject:
    s = db.query(models.Subject).filter_by(id=id).first()
    if not s:
        raise HTTPException(404)
    return s


def get_subjects(db: Session) -> list:
    return db.query(models.Subject).all()


def create_subject(db: Session, subject: schemas.Subject) -> models.Subject:
    db_subject = models.Subject(name=subject.name, teacher=subject.teacher, day_week=[a.json() for a in subject.day_week],
                                time=subject.time)
    return commit(db, db_subject)


def update_subject(db: Session, _id: int, subject: schemas.Subject) -> models.Subject:
    db_subject = get_subject(db, _id)
    if not db_subject:
        return None
    db_subject.name = subject.name
    db_subject.teacher = subject.teacher
    db_subject.time = subject.time
    db_subject.day_week = [a.json() for a in subject.day_week]
    db.commit()
    return db_subject


def delete_subject(db: Session, _id: int):
    db_subject = get_subject(db, _id)
    db.delete(db_subject)
    db.commit()
