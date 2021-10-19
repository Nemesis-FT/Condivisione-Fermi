from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from condivisione.database import schemas, models
from condivisione.database.crud.common import commit


def get_message(db: Session, id: int) -> models.Message:
    m = db.query(models.Message).filter_by(id=id).first()
    if not m:
        raise HTTPException(404, "Not found")
    return m


def get_messages(db: Session) -> list:
    return db.query(models.Message).all()


def create_message(db: Session, message: schemas.Message) -> models.Message:
    return commit(db,
                  models.Message(title=message.title, content=message.content, type=message.type, date=datetime.now()))


def update_message(db: Session, message: schemas.Message, id: int) -> models.Message:
    db_message = get_message(db, id)
    db_message.title = message.title
    db_message.content = message.content
    db_message.type = message.type
    db.commit()
    return db_message


def remove_message(db: Session, id: int):
    db_message = get_message(db, id)
    db.delete(db_message)
